#!/usr/bin/env python3
"""Qualifica un rapporto locale di sicurezza; non esegue scansioni o aggiornamenti.

Il rapporto e le prove restano in _notes/sicurezza. Un controllo assente, vecchio,
incompleto o riferito a un altro stato non diventa un esito senza rilievi.
--hook conserva il verdetto nel testo e non blocca l'apertura della sessione.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

SCHEMA = "project-security-review-0.1"
SCOPES = {"dipendenze", "runtime", "host", "immagini", "esposizione", "integrita"}
STATES = {"verificato", "non_verificato", "non_applicabile"}
MANIFESTS = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "composer.json",
    "composer.lock",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "Gemfile.lock",
    "Cargo.lock",
    "go.mod",
    "go.sum",
}
PRUNE = {
    ".git",
    ".claude",
    ".agents",
    "_notes",
    "_old",
    "_private",
    "private",
    "output",
    "node_modules",
    ".venv",
    "venv",
    "vendor",
    ".next",
    "dist",
    "build",
    "target",
    "tests",
    "__tests__",
    "fixtures",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child(root: Path, name: str) -> Path:
    p = Path(name)
    if (
        p.is_absolute()
        or ".." in p.parts
        or re.match(r"^[A-Za-z]:", name)
        or "\\" in name
    ):
        raise ValueError("percorso_prova_non_relativo")
    result = (root / p).resolve()
    if not result.is_relative_to(root):
        raise ValueError("prova_fuori_progetto")
    return result


def inputs(root: Path) -> dict[str, str]:
    import os

    result: dict[str, str] = {}

    def error(exc: OSError) -> None:
        raise exc

    for current, dirs, files in os.walk(root, onerror=error, followlinks=False):
        base = Path(current)
        dirs[:] = [
            n
            for n in dirs
            if n not in PRUNE
            and not (base / n).is_symlink()
            and not (getattr(base / n, "is_junction", lambda: False)())
        ]
        for name in files:
            if (
                name in MANIFESTS
                or name.lower().startswith("dockerfile")
                or ("compose" in name.lower() and name.endswith((".yml", ".yaml")))
            ):
                p = base / name
                if p.is_symlink():
                    raise ValueError("manifest_collegato_non_verificabile")
                result[p.relative_to(root).as_posix()] = sha(p)
    return result


def git_state(root: Path) -> tuple[str, str, bool]:
    def git(*args: str) -> str:
        p = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf8",
            errors="replace",
            timeout=10,
            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
        )
        if p.returncode:
            raise ValueError("stato_git_non_verificabile")
        return p.stdout.rstrip("\r\n")

    if Path(git("rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("radice_git_diversa")
    changed = [
        line[3:].strip('"')
        for line in git(
            "status", "--porcelain", "--untracked-files=normal"
        ).splitlines()
    ]
    dirty = any(
        not p.startswith((".claude/", ".agents/", "docs/", "_notes/"))
        and p not in {"README.md", "CLAUDE.md", "AGENTS.md", "CASE-STUDIES.md"}
        for p in changed
    )
    return git("rev-parse", "HEAD"), git("branch", "--show-current"), dirty


def assess(root: Path, max_hours: float = 24, now: dt.datetime | None = None) -> dict:
    root = root.resolve()
    out = {
        "schema_version": SCHEMA,
        "progetto": str(root),
        "stato": "non_verificato",
        "motivi": [],
        "rilievi_aperti": [],
        "aggiornamenti_eseguiti": False,
        "scansione_eseguita": False,
        "connessioni_remote_eseguite": False,
    }
    report = root / "_notes/sicurezza/ultimo-controllo.json"
    try:
        if not root.is_dir():
            return dict(out, stato="non_verificabile", motivi=["radice_assente"])
        if not report.is_file():
            return dict(out, motivi=["rapporto_assente"])
        if report.stat().st_size > 2_000_000:
            raise ValueError("rapporto_troppo_grande")
        data = json.loads(report.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
            raise ValueError("schema_rapporto_non_supportato")
        timestamp = dt.datetime.fromisoformat(
            data["verificato_il"].replace("Z", "+00:00")
        )
        if timestamp.utcoffset() is None:
            raise ValueError("data_senza_fuso")
        now = now or dt.datetime.now(dt.timezone.utc)
        age = (now - timestamp).total_seconds() / 3600
        if age < -5 / 60:
            raise ValueError("data_nel_futuro")
        out["ore_dal_controllo"] = round(age, 2)
        findings = data["rilievi"]
        if not isinstance(findings, list):
            raise ValueError("rilievi_non_validi")
        for item in findings:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or item.get("stato") not in {"aperto", "mitigato", "risolto"}
            ):
                raise ValueError("rilievo_non_valido")
            if item.get("gravita") not in {
                "critica",
                "alta",
                "media",
                "bassa",
                "informativa",
            }:
                raise ValueError("gravita_non_valida")
            if item["stato"] in {"aperto", "mitigato"}:
                out["rilievi_aperti"].append(
                    {k: item[k] for k in ("id", "gravita", "stato")}
                )
        coverage = data["copertura"]
        if not isinstance(coverage, dict) or set(coverage) != SCOPES:
            raise ValueError("perimetri_mancanti_o_estranei")
        incomplete = []
        for name, section in coverage.items():
            if not isinstance(section, dict) or section.get("stato") not in STATES:
                raise ValueError("copertura_non_valida")
            if section["stato"] == "non_verificato":
                incomplete.append(name)
            if (
                section["stato"] == "non_applicabile"
                and not section.get("motivo", "").strip()
            ):
                raise ValueError("non_applicabile_senza_motivo")
        evidence = data["prove"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("prove_assenti")
        for proof in evidence:
            if not isinstance(proof, dict) or not re.fullmatch(
                r"[a-f0-9]{64}", proof.get("sha256", "")
            ):
                raise ValueError("prova_non_valida")
            if sha(child(root, proof["percorso"])) != proof["sha256"]:
                raise ValueError("prova_cambiata")
        declared = data["input_sha256"]
        if not isinstance(declared, dict) or any(
            not isinstance(k, str) or not re.fullmatch(r"[a-f0-9]{64}", str(v))
            for k, v in declared.items()
        ):
            raise ValueError("input_non_validi")
        # Frame esatto: anche un nuovo manifest invalida il rapporto precedente.
        current = inputs(root)
        commit, branch, dirty = git_state(root)
        if (
            current != declared
            or commit != data["commit"]
            or branch != data["ramo"]
            or dirty
        ):
            out.update(stato="cambiato", motivi=["input_o_riferimento_git_cambiato"])
        elif age > max_hours:
            out.update(stato="scaduto", motivi=["serve_controllo_aggiornato"])
        elif incomplete:
            out.update(stato="incompleto", motivi=sorted(incomplete))
        elif out["rilievi_aperti"]:
            out.update(stato="rilievi_aperti")
        else:
            out.update(stato="nessun_rilievo_nel_perimetro")
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        subprocess.TimeoutExpired,
    ) as exc:
        out.update(
            stato="non_verificabile",
            motivi=[str(exc) if isinstance(exc, ValueError) else type(exc).__name__],
        )
    return out


def exit_code(result: dict) -> int:
    if result["rilievi_aperti"]:
        return 1
    return 0 if result["stato"] == "nessun_rilievo_nel_perimetro" else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radice", type=Path, default=Path.cwd())
    parser.add_argument("--max-ore", type=float, default=24)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--hook", action="store_true")
    args = parser.parse_args(argv)
    if not 0 < args.max_ore <= 744:
        parser.error("--max-ore deve essere fra 0 e 744")
    result = assess(args.radice, args.max_ore)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            "Sicurezza: %s; rilievi aperti=%s; %s"
            % (
                result["stato"],
                len(result["rilievi_aperti"]),
                ", ".join(result["motivi"]),
            )
        )
        print(
            "Il verdetto riguarda il rapporto e il perimetro dichiarati; non e una scansione o una certificazione del sistema."
        )
    return 0 if args.hook else exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
