"""Un comando citato resta una fonte, senza inventare un'installazione del progetto."""

import importlib.util
import json
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sources_under_test", TOOLS / "fonti-a-monte.py")
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)


def test_npx_binary_is_bound_to_its_declared_dependency_metadata(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"devDependencies": {"typescript": "1"}}), encoding="utf-8")
    (tmp_path / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/typescript": {"bin": {"tsc": "bin/tsc"}}}}), encoding="utf-8")
    command = "npx " + "tsc; npm " + "install -g " + "tsc"
    found = sources.pacchetti(command, sources.binari_npm(tmp_path))
    assert found == ["npm:typescript", "npm:tsc"]


def test_quoted_install_instructions_do_not_become_proof_of_installation(tmp_path):
    path = tmp_path / ".claude/skills/esterna/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("Istruzioni della fonte: npx " + "skills add " + "autore/pacchetto\n", encoding="utf-8")
    entry = sources.nuova_voce(tmp_path, "npm:skills", path)
    assert "citato" in entry["motivo"]
    assert "installato nel progetto" not in entry["motivo"]


def test_old_automatic_reason_is_corrected_without_overwriting_manual_reasons(tmp_path):
    path = tmp_path / ".claude/skills/esterna/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("npx " + "skills add " + "autore/pacchetto\n", encoding="utf-8")
    registry = tmp_path / ".claude/fonti-a-monte.json"
    data = {"fonti": [{"id": "npm:skills", "ruolo": "strumenti", "scheda": ".claude/skills/esterna/SKILL.md", "motivo": "installato nel progetto, in .claude/skills/esterna/SKILL.md"}], "falsi": []}
    registry.write_text(json.dumps(data), encoding="utf-8")
    sources.censisci(tmp_path, True)
    corrected = json.loads(registry.read_text(encoding="utf-8"))
    assert "citato" in corrected["fonti"][0]["motivo"]
    corrected["fonti"][0]["motivo"] = "Motivo verificato dal progetto"
    registry.write_text(json.dumps(corrected), encoding="utf-8")
    sources.censisci(tmp_path, True)
    assert json.loads(registry.read_text(encoding="utf-8"))["fonti"][0]["motivo"] == "Motivo verificato dal progetto"


def test_git_eol_and_explicit_timezone_notations_are_not_invented_repositories():
    text = "Indice Git `i/mixed`, fuso dichiarato `America/New_York`; fonte `autore/progetto`."
    found = sources.tra_apici(text, set())
    assert found == ["github:autore/progetto"]
    assert sources.tra_apici("Fonte `America/progetto`", set()) == ["github:America/progetto"]
