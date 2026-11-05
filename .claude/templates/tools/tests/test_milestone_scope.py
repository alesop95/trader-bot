"""La conferma di una milestone non può includere altro lavoro o uno stage preesistente."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest


TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("milestone_tested", TOOLS / "verifica-milestone.py")
milestone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(milestone)


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "prova@example.invalid")
    (tmp_path / ".gitignore").write_text("_notes/\n", encoding="utf-8")
    (tmp_path / "uno.txt").write_text("prima\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "Base della prova")
    (tmp_path / "uno.txt").write_text("dopo\n", encoding="utf-8")
    return tmp_path


def test_scope_excludes_other_session_files_and_leaves_stage_untouched(repo):
    (repo / "due.txt").write_text("altro lavoro\n", encoding="utf-8")
    data = milestone.inventario(repo)
    scope = repo / "_notes/COMMIT-SCOPE.json"
    scope.parent.mkdir()
    scope.write_text(json.dumps({"head": data["head"], "paths": ["uno.txt"]}), encoding="utf-8")
    before = git(repo, "diff", "--cached")
    report = milestone.controlla(repo, data)
    assert report["paths"] == ["uno.txt"]
    assert report["fuori_perimetro"] == ["due.txt"]
    assert git(repo, "diff", "--cached") == before


def test_preexisting_stage_is_preserved_and_rejected(repo):
    git(repo, "add", "uno.txt")
    before = git(repo, "diff", "--cached")
    with pytest.raises(ValueError, match="stage già presente"):
        milestone.controlla(repo, milestone.inventario(repo))
    assert git(repo, "diff", "--cached") == before


def test_content_change_after_preview_is_observable_even_when_names_are_identical(repo):
    first = milestone.controlla(repo, milestone.inventario(repo))
    (repo / "uno.txt").write_text("cambiato dopo i controlli\n", encoding="utf-8")
    second = milestone.controlla(repo, milestone.inventario(repo))
    assert first["paths"] == second["paths"]
    assert first != second


def test_adopted_teaching_warns_without_blocking_a_routine_change(repo):
    master = repo / ".claude/context/studio-didattico-master.md"
    master.parent.mkdir(parents=True)
    master.write_text("# Registro\n", encoding="utf-8")
    git(repo, "add", str(master))
    git(repo, "commit", "-q", "-m", "Livello didattico adottato")
    tool = repo / "tools/prova.py"
    tool.parent.mkdir()
    tool.write_text("print(1)\n", encoding="utf-8")
    report = milestone.controlla(repo, milestone.inventario(repo))
    assert any("Didattica adottata" in item for item in report["warnings"])


@pytest.mark.skipif(os.name != "nt", reason="esercita la variante PowerShell su Windows")
def test_windows_closure_rejects_preexisting_stage_before_committing(repo):
    git(repo, "add", "uno.txt")
    before = git(repo, "diff", "--cached")
    head = git(repo, "rev-parse", "HEAD")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TOOLS / "chiudi-sessione.ps1"),
         "-Radice", str(repo), "-Messaggio", "Aggiornato il file di prova", "-Si", "-NoPush", "-NoWipe"],
        capture_output=True, timeout=45,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert git(repo, "diff", "--cached") == before
    assert git(repo, "rev-parse", "HEAD") == head


@pytest.mark.skipif(os.name != "nt", reason="esercita la variante PowerShell su Windows")
def test_windows_closure_commits_only_prepared_scope_and_keeps_other_work(repo):
    (repo / "due.txt").write_text("lavoro di un'altra sessione\n", encoding="utf-8")
    scope = repo / "_notes/COMMIT-SCOPE.json"
    scope.parent.mkdir()
    scope.write_text(json.dumps({"head": milestone.inventario(repo)["head"], "paths": ["uno.txt"]}), encoding="utf-8")
    head = git(repo, "rev-parse", "HEAD")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TOOLS / "chiudi-sessione.ps1"),
         "-Radice", str(repo), "-Messaggio", "Aggiornato il file di prova", "-Si", "-NoPush", "-NoWipe"],
        capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert git(repo, "diff", "--cached") == b""
    assert git(repo, "rev-parse", "HEAD") != head
    assert git(repo, "show", "--format=", "--name-only", "HEAD").strip() == b"uno.txt"
    assert (repo / "due.txt").read_text(encoding="utf-8") == "lavoro di un'altra sessione\n"
