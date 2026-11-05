"""Ripresa comune: oggetti fuori storia e sincronizzazione ripetibile, con Git reale."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


TOOLS = Path(__file__).resolve().parents[1]


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def git(root, *args):
    result = run("git", "-C", str(root), *args)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "progetto"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "prova@example.invalid")
    (root / "codice.txt").write_text("contenuto\n", encoding="utf-8")
    git(root, "add", "codice.txt")
    git(root, "commit", "-q", "-m", "Base della prova")
    return root


def scheda(root, key, anchor):
    path = root / ".claude/context/STACK.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ncovers-paths: [codice.txt]\n{key}: {anchor}\n---\n\n# Stack\n",
        encoding="utf-8",
    )
    return path


def orphan(root):
    tree = git(root, "rev-parse", "HEAD^{tree}")
    anchor = git(root, "commit-tree", tree, "-m", "Oggetto fuori storia")
    git(root, "cat-file", "-e", anchor + "^{commit}")
    assert run("git", "-C", str(root), "merge-base", "--is-ancestor", anchor, "HEAD").returncode == 1
    assert git(root, "diff", anchor + "..HEAD") == ""
    return anchor


@pytest.mark.parametrize("key", ["last-verified-commit", "last-verified"])
def test_schema_rejects_existing_unreachable_anchor_with_identical_tree(repo, key):
    scheda(repo, key, orphan(repo))
    result = run(sys.executable, str(TOOLS / "verifica-schede.py"), "--radice", str(repo))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "fuori dalla storia" in result.stdout
    assert "STACK.md" in result.stdout


@pytest.mark.parametrize("key", ["last-verified-commit", "last-verified"])
def test_reachable_anchor_is_accepted_from_repository_subdirectory(repo, key):
    scheda(repo, key, git(repo, "rev-parse", "HEAD"))
    result = run(sys.executable, str(TOOLS / "verifica-schede.py"), "--rigoroso", cwd=repo / ".claude")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "schede con covers-paths: 1" in result.stdout


def test_non_repository_is_not_a_zero_card_success(tmp_path):
    result = run(sys.executable, str(TOOLS / "verifica-schede.py"), "--radice", str(tmp_path))
    assert result.returncode == 2, result.stdout + result.stderr


@pytest.mark.parametrize("key", ["last-verified-commit", "last-verified"])
def test_resume_rejects_existing_unreachable_anchor(repo, key):
    anchor = orphan(repo)
    scheda(repo, key, anchor)
    spec = importlib.util.spec_from_file_location("resume_under_test", TOOLS / "verifica-ripresa.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.schede_indietro(radice=str(repo)) == [("STACK.md", anchor)]


def test_sync_second_apply_and_check_preserve_bytes_and_modification_times(tmp_path):
    root = tmp_path / "progetto"
    source = root / ".claude/skills/riprendi/SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "---\nname: riprendi\ndescription: Ripresa del progetto.\ndisable-model-invocation: true\n---\nLeggere la procedura.\n",
        encoding="utf-8",
    )
    (root / ".claude/PROJECT-SYSTEM.md").write_text("# Sistema\n", encoding="utf-8")
    model = root / ".claude/templates/AGENTS.md"
    model.parent.mkdir(parents=True)
    model.write_bytes((TOOLS.parent / "AGENTS.md").read_bytes())
    args = [sys.executable, str(TOOLS / "sync-codex-skills.py"), "--project-root", str(root)]
    first = run(*args)
    assert first.returncode == 0, first.stdout + first.stderr

    def snapshot():
        return {
            str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob("*") if path.is_file()
        }

    before = snapshot()
    for flags in ([], ["--check"]):
        result = run(*args, *flags)
        assert result.returncode == 0, result.stdout + result.stderr
        assert snapshot() == before
    bridge = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert ".claude/skills/riprendi/SKILL.md" in bridge
    assert "$riprendi" in bridge
