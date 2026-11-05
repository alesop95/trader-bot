"""Instrada GitHub CLI dal profilo privato del repository, senza switch globali."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


class GateFailure(Exception):
    pass


TOKEN_KEYS = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "GH_DEBUG",
    "GH_HOST",
    "GH_REPO",
)


def clean_environment():
    return {k: v for k, v in os.environ.items() if k not in TOKEN_KEYS}


def call(argv, env, runner):
    try:
        return runner(argv, capture_output=True, env=env, timeout=45)
    except (OSError, subprocess.TimeoutExpired):
        raise GateFailure("command_unavailable_or_timeout") from None


def git_value(repo, key, runner):
    p = call(
        ["git", "-C", str(repo), "config", "--local", "--get", key],
        dict(clean_environment(), GIT_OPTIONAL_LOCKS="0"),
        runner,
    )
    if p.returncode == 1:
        return None
    if p.returncode:
        raise GateFailure("git_configuration_unavailable")
    return p.stdout.decode("utf8").strip()


def destination(remote):
    m = re.fullmatch(
        r"(?:ssh://)?git@([^/:]+)(?::|/)([^/\s]+)/([^/\s]+?)/?", remote or ""
    )
    if not m:
        raise GateFailure("ssh_remote_required")
    alias, owner, repo = m.groups()
    repo = repo.removesuffix(".git")
    if not repo or repo in {".", ".."}:
        raise GateFailure("invalid_repository")
    return alias, owner + "/" + repo


def validate_pr_text(args):
    """Reject damaged PR prose before credentials or a write command are used."""
    if args[:2] not in (["pr", "create"], ["pr", "edit"]):
        return
    texts = []
    for index, arg in enumerate(args[2:], 2):
        if arg in {"--body", "-b"} or arg.startswith("--body="):
            raise GateFailure("pr_description_requires_utf8_body_file")
        flag, separator, value = arg.partition("=")
        if flag not in {"--body-file", "-F", "--title", "-t"}:
            continue
        if not separator:
            if index + 1 >= len(args):
                raise GateFailure("pr_text_argument_missing")
            value = args[index + 1]
        if flag in {"--body-file", "-F"}:
            if value == "-":
                raise GateFailure("pr_description_requires_utf8_body_file")
            try:
                texts.append(Path(value).read_bytes().decode("utf8"))
            except (OSError, UnicodeError):
                raise GateFailure("pr_description_not_readable_utf8") from None
        else:
            texts.append(value)
    for text in texts:
        if "\ufffd" in text or text.startswith("\ufeff"):
            raise GateFailure("pr_text_contains_encoding_damage")
        if re.search(r"[\u00c2\u00c3][\u0080-\u00bf]|\u00e2\u20ac", text):
            raise GateFailure("pr_text_contains_encoding_damage")
        # Inspect prose; query strings and code can legitimately contain '?'.
        prose = re.sub(r"```[\s\S]*?```|`[^`]*`|https?://[^\s<>]+", "", text)
        if re.search(r"(?<=[^\W\d_])\?(?=[^\W\d_])|(?<!\S)\?(?=\s+[^\W\d_])", prose):
            raise GateFailure("pr_text_contains_suspect_question_mark")
        if re.search(r"\b(?:vulnerabilit|conformit|identit|propriet|attivit|funzionalit|qualit|gi|perch|pu)\?(?=\W|$)", prose, re.I):
            raise GateFailure("pr_text_contains_suspect_question_mark")


def command_args(args, host, repository, allow_write):
    if not args:
        return []
    if args[0] in {"auth", "config", "alias", "extension"}:
        raise GateFailure("authentication_and_configuration_are_manual")
    if args[:2] == ["pr", "merge"]:
        raise GateFailure("merge_is_manual")
    if any(
        a in {"-H", "--header", "--hostname"}
        or a.startswith(("--header=", "--hostname="))
        or a.startswith("-H")
        for a in args
    ):
        raise GateFailure("host_or_header_override_denied")
    args = list(args)
    if args[0] == "api":
        if len(args) < 2 or not (
            args[1].lstrip("/") == "repos/" + repository
            or args[1].lstrip("/").startswith("repos/" + repository + "/")
        ):
            raise GateFailure("api_repository_mismatch")
        writing = any(
            a in {"-f", "-F", "--field", "--raw-field", "--input"}
            or a.startswith(("--field=", "--raw-field=", "--input="))
            or a.startswith(("-f", "-F"))
            for a in args[2:]
        )
        for i, a in enumerate(args):
            if a in {"-X", "--method"}:
                if i + 1 >= len(args):
                    raise GateFailure("method_missing")
                writing = writing or args[i + 1].upper() != "GET"
            elif a.startswith("--method="):
                writing = writing or a.split("=", 1)[1].upper() != "GET"
            elif a.startswith("-X") and len(a) > 2:
                writing = writing or a[2:].upper() != "GET"
        if writing and not allow_write:
            raise GateFailure("write_requires_explicit_manual_flag")
        return args + ["--hostname", host]
    if args[0] not in {"pr", "issue", "repo"} or len(args) < 2:
        raise GateFailure("unsupported_command_family")
    readonly = args[:2] in [
        ["pr", "view"],
        ["pr", "list"],
        ["pr", "diff"],
        ["pr", "checks"],
        ["issue", "view"],
        ["issue", "list"],
        ["repo", "view"],
    ]
    if not readonly and not allow_write:
        raise GateFailure("write_requires_explicit_manual_flag")
    if "--web" in args or "-w" in args:
        raise GateFailure("browser_identity_is_separate")
    explicit = False
    for i, a in enumerate(args):
        if a in {"-R", "--repo"}:
            if i + 1 >= len(args) or args[i + 1].lower() != repository.lower():
                raise GateFailure("repository_override_denied")
            explicit = True
        elif a.startswith("--repo="):
            if a.split("=", 1)[1].lower() != repository.lower():
                raise GateFailure("repository_override_denied")
            explicit = True
        elif a.startswith("-R") and len(a) > 2:
            raise GateFailure("compact_repository_override_denied")
    return args if explicit else args + ["--repo", repository]


def execute(repo, profile, gh, args=(), allow_write=False, runner=subprocess.run):
    if profile.get("schema_version") != 1 or profile.get("github_host") != "github.com":
        raise GateFailure("unsupported_profile")
    expected = profile.get("git_local", {})
    keys = {"user.name", "user.email", "remote.origin.url", "core.sshCommand"}
    if set(expected) != keys or not all(
        isinstance(expected[k], str) and expected[k] for k in keys - {"core.sshCommand"}
    ):
        raise GateFailure("incomplete_git_profile")
    for key, value in expected.items():
        actual = git_value(repo, key, runner)
        if actual != value:
            raise GateFailure("git_profile_mismatch")
    alias, repository = destination(expected["remote.origin.url"])
    if alias != profile.get("ssh_alias"):
        raise GateFailure("ssh_alias_mismatch")
    login = profile.get("github_login")
    if not isinstance(login, str) or not re.fullmatch(
        r"[a-zA-Z0-9][a-zA-Z0-9-]{0,38}", login
    ):
        raise GateFailure("invalid_api_identity")
    argv = command_args(list(args), profile["github_host"], repository, allow_write)
    validate_pr_text(list(args))
    env = clean_environment()
    lookup = call(
        [gh, "auth", "token", "--hostname", profile["github_host"], "--user", login],
        env,
        runner,
    )
    if lookup.returncode:
        raise GateFailure("profile_credentials_unavailable")
    token = lookup.stdout.decode("utf8").strip()
    if not token or "\n" in token or "\r" in token:
        raise GateFailure("invalid_credentials_result")
    selected = dict(
        env, GH_TOKEN=token, GH_HOST=profile["github_host"], GH_PROMPT_DISABLED="1"
    )
    identity = call(
        [gh, "api", "user", "--hostname", profile["github_host"], "--jq", ".login"],
        selected,
        runner,
    )
    if (
        identity.returncode
        or identity.stdout.decode("utf8").strip().lower() != login.lower()
    ):
        raise GateFailure("api_identity_mismatch")
    if not argv:
        return dict(
            matched=True,
            profile_loaded=True,
            credentials_bound_per_process=True,
            global_account_switched=False,
        ), None
    result = call([gh, *argv], selected, runner)
    result.stdout = result.stdout.replace(token.encode(), b"<redacted>")
    result.stderr = result.stderr.replace(token.encode(), b"<redacted>")
    return dict(
        matched=True, credentials_bound_per_process=True, global_account_switched=False
    ), result


def profile_path(repo, override, runner=subprocess.run):
    if override:
        return Path(override).resolve()
    p = call(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        dict(clean_environment(), GIT_OPTIONAL_LOCKS="0"),
        runner,
    )
    if p.returncode:
        raise GateFailure("git_common_directory_unavailable")
    common = Path(p.stdout.decode("utf8").strip()).resolve()
    if common.name != ".git":
        raise GateFailure("explicit_profile_required_for_nonstandard_git_directory")
    return common.parent / "_notes/identita-gh.locale.json"


def from_registry(repo, registry, runner=subprocess.run):
    if registry.get("schema_version") != 1:
        raise GateFailure("unsupported_registry")
    actual = {
        k: git_value(repo, k, runner)
        for k in ["user.name", "user.email", "remote.origin.url", "core.sshCommand"]
    }
    alias, repository = destination(actual["remote.origin.url"])
    matches = [
        p
        for p in registry.get("profiles", [])
        if p.get("git_user_name") == actual["user.name"]
        and p.get("git_user_email") == actual["user.email"]
        and p.get("ssh_alias") == alias
        and p.get("core_ssh_command") == actual["core.sshCommand"]
    ]
    if len(matches) != 1:
        raise GateFailure("machine_profile_missing_or_ambiguous")
    selected = matches[0]
    return dict(
        schema_version=1,
        github_host=selected.get("github_host"),
        github_login=selected.get("github_login"),
        ssh_alias=alias,
        git_local=actual,
    )


def load_profile(repo, override=None, registry_override=None, runner=subprocess.run):
    profile = profile_path(repo, override, runner)
    if profile.is_file():
        return json.loads(profile.read_text(encoding="utf-8-sig"))
    if override:
        raise GateFailure("private_project_profile_missing")
    registry = (
        Path(registry_override)
        if registry_override
        else Path.home() / ".config/identita-gh-profili.json"
    )
    if not registry.is_file():
        raise GateFailure("private_project_or_machine_profile_missing")
    return from_registry(
        repo, json.loads(registry.read_text(encoding="utf-8-sig")), runner
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--profile-file")
    parser.add_argument("--registry-file")
    parser.add_argument("--gh")
    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="Solo per operazioni manuali espressamente autorizzate; merge escluso.",
    )
    parser.add_argument("gh_args", nargs=argparse.REMAINDER)
    a = parser.parse_args()
    try:
        repo = Path(a.repo).resolve()
        profile = load_profile(repo, a.profile_file, a.registry_file)
        gh = a.gh or shutil.which("gh")
        if not gh:
            raise GateFailure("github_cli_not_installed")
        command = a.gh_args[1:] if a.gh_args[:1] == ["--"] else a.gh_args
        checked, result = execute(repo, profile, gh, command, a.allow_write)
        if result is None:
            print(json.dumps(checked))
            return 0
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        return result.returncode
    except (GateFailure, OSError, ValueError) as e:
        print(
            json.dumps(
                dict(
                    matched=False,
                    error=str(e)
                    if isinstance(e, GateFailure)
                    else "profile_unavailable_or_invalid",
                    global_account_switched=False,
                )
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
