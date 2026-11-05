"""La ricevuta di una fusione non può coprire un contenuto perso o escluso dal commit."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import test_allinea_dal_template as base


TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolution_gate", TOOLS / "verifica-milestone.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def alignment():
    case = base.RisoltoAMano("runTest")
    case.setUp()
    body = base.righe("corpo", 60)
    case.commit(body + ["riga del template"], "base")
    case.commit(body + ["riga nuova del template"], "testa")
    case.scrivi_progetto(body + ["scelta locale da conservare"])
    yield case
    case.tearDown()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_lost_local_merge_reopens_resolution(alignment):
    case = alignment
    assert case.allinea_con("--risolto", base.REGOLA)["esito"] == "RISOLTO"
    assert case.allinea_con()["esito"] == "ADATTATO"
    case.scrivi_progetto(base.righe("corpo", 60) + ["riga del template"])
    assert case.allinea_con()["esito"] != "ADATTATO"


def test_legacy_record_without_local_signature_is_remeasured(alignment):
    case = alignment
    case.allinea_con("--risolto", base.REGOLA)
    registry = case.prj / ".claude/allineamento-risolti.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    del data[base.REGOLA]["locale_sha256_lf"]
    registry.write_text(json.dumps(data), encoding="utf-8")
    assert case.allinea_con()["esito"] == "CONFLITTO"


def test_resolution_report_contains_both_registry_and_merged_file(alignment):
    case = alignment
    case.allinea_con("--risolto", base.REGOLA)
    report = json.loads((case.base / "rapporto.json").read_text(encoding="utf-8"))
    assert any(r["file"] == base.REGOLA and r["esito"] == "RISOLTO" for r in report)
    assert any(r["file"] == ".claude/allineamento-risolti.json" and r["esito"] == "VECCHIO" for r in report)


def test_registry_staged_without_merged_content_is_blocked(alignment):
    case = alignment
    git(case.prj, "init", "-q", "-b", "main")
    git(case.prj, "config", "user.name", "Fixture")
    git(case.prj, "config", "user.email", "prova@example.invalid")
    git(case.prj, "config", "core.autocrlf", "false")
    git(case.prj, "add", ".")
    git(case.prj, "commit", "-q", "-m", "Contenuto precedente")
    case.scrivi_progetto(base.righe("corpo", 60) + ["fusione deliberata da conservare"])
    case.allinea_con("--risolto", base.REGOLA)
    git(case.prj, "add", ".claude/allineamento-risolti.json")
    before = git(case.prj, "diff", "--cached")
    with pytest.raises(ValueError, match="stesso commit"):
        gate.verifica_risoluzioni_index(case.prj)
    assert git(case.prj, "diff", "--cached") == before
    git(case.prj, "add", base.REGOLA)
    gate.verifica_risoluzioni_index(case.prj)
