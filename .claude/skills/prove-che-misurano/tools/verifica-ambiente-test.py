#!/usr/bin/env python3
"""Fail before a test suite can silently skip its integration cases.

The check deliberately does not print environment values or URL credentials.
"""

from __future__ import annotations

import argparse
import ipaddress
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch
from urllib.parse import urlsplit


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"{path.name}:{number}: expected NAME=value")
        name, value = line.split("=", 1)
        name = name.strip()
        if not name.isidentifier():
            raise ValueError(f"{path.name}:{number}: invalid variable name")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name] = value
    return values


def is_loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def local_endpoint(value: str) -> tuple[str, int]:
    try:
        parsed = urlsplit(value)
        host, port = parsed.hostname, parsed.port
    except ValueError as exc:
        raise ValueError("invalid URL") from exc
    if not parsed.scheme or not host or port is None:
        raise ValueError("URL must include scheme, host and explicit port")
    if not is_loopback(host):
        raise ValueError("host is not loopback")
    return host, port


def check(names: list[str], env_file: Path | None, tcp: bool) -> list[str]:
    file_values: dict[str, str] = {}
    if any(not os.environ.get(name) for name in names) and env_file:
        if not env_file.is_file():
            raise ValueError(f"{env_file.name}: test environment file missing")
        file_values = read_env_file(env_file)
    messages: list[str] = []
    for name in names:
        value = os.environ.get(name) or file_values.get(name)
        if not value:
            raise ValueError(f"{name}: missing test URL")
        try:
            host, port = local_endpoint(value)
        except ValueError as exc:
            raise ValueError(f"{name}: {exc}") from exc
        if tcp:
            try:
                with socket.create_connection((host, port), timeout=2):
                    pass
            except OSError as exc:
                raise ValueError(f"{name}: local service unavailable on {host}:{port}") from exc
        messages.append(f"{name}: loopback {host}:{port}" + (" reachable" if tcp else ""))
    return messages


def self_test() -> None:
    assert is_loopback("localhost") and is_loopback("127.0.0.1") and is_loopback("::1")
    assert not is_loopback("localhost.example.com") and not is_loopback("neon.tech")
    assert local_endpoint("postgresql://user:password@127.0.0.1:5433/test") == ("127.0.0.1", 5433)
    for bad in ("postgresql://neon.tech:5432/test", "postgresql://localhost/test", "not-a-url"):
        try:
            local_endpoint(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe test URL accepted")
    path = Path(".env.test")
    with patch.object(Path, "read_text", return_value='# comment\nexport DATABASE_URL="postgresql://localhost:5433/test"\n'), patch.object(Path, "is_file", return_value=True):
        assert read_env_file(path)["DATABASE_URL"] == "postgresql://localhost:5433/test"
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost:5434/override"}):
            assert check(["DATABASE_URL"], path / "missing", False) == ["DATABASE_URL: loopback localhost:5434"]
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://remote.invalid:5432/test"}):
            try:
                check(["DATABASE_URL"], path, False)
            except ValueError:
                pass
            else:
                raise AssertionError("remote process URL was hidden by the local test file")
    print("Self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="fallback file when a variable is absent from the process")
    parser.add_argument("--loopback-url", action="append", default=[], metavar="NAME", help="required URL variable; repeat for each local service")
    parser.add_argument("--tcp", action="store_true", help="also verify that the local port accepts connections")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.loopback_url:
        parser.error("at least one --loopback-url is required")
    try:
        for message in check(args.loopback_url, args.env_file, args.tcp):
            print(message)
    except ValueError as exc:
        print(f"Test preflight failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
