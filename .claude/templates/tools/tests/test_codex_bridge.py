"""Regressioni del ponte Codex mancante nei progetti gia' istanziati."""

import json
import subprocess
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
SYNC = TOOLS / "sync-codex-skills.py"
ALIGN = TOOLS / "allinea-dal-template.py"
BRIDGE = "# Istruzioni Codex\n\nLeggere CLAUDE.md come fonte canonica.\n"


def run(*args, cwd=None):
    return subprocess.run(
        args, cwd=cwd, text=True, capture_output=True, encoding="utf-8"
    )


def project(root):
    skill = root / ".claude/skills/riprendi/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: riprendi\ndescription: Ripresa verificata.\ndisable-model-invocation: true\n---\n\nLeggere la memoria.\n",
        encoding="utf-8",
    )
    (root / ".claude/PROJECT-SYSTEM.md").write_text(
        "# Sistema di progetto\n", encoding="utf-8"
    )
    model = root / ".claude/templates/AGENTS.md"
    model.parent.mkdir(parents=True)
    model.write_text(BRIDGE, encoding="utf-8")
    return root


def sync(root, *flags):
    return run(sys.executable, str(SYNC), "--project-root", str(root), *flags)


def test_check_red_when_only_bridge_missing_and_no_write(tmp_path):
    root = project(tmp_path / "prj")
    assert sync(root).returncode == 0
    adapter = root / ".agents/skills/riprendi/SKILL.md"
    wrapper_before = adapter.read_bytes()
    (root / "AGENTS.md").unlink()
    result = sync(root, "--check")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "AGENTS.md" in result.stdout
    assert not (root / "AGENTS.md").exists()
    assert adapter.read_bytes() == wrapper_before


def test_generation_repairs_bridge_and_keeps_explicit_policy(tmp_path):
    root = project(tmp_path / "prj")
    assert sync(root).returncode == 0
    assert (root / "AGENTS.md").read_text(encoding="utf-8") == BRIDGE
    assert "../../../.claude/skills/riprendi/SKILL.md" in (
        root / ".agents/skills/riprendi/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in (
        root / ".agents/skills/riprendi/agents/openai.yaml"
    ).read_text(encoding="utf-8")
    assert sync(root, "--check").returncode == 0


def test_existing_custom_bridge_preserved(tmp_path):
    root = project(tmp_path / "prj")
    custom = b"# Codex locale\r\n\r\nLeggere CLAUDE.md; regola propria.\r\n"
    (root / "AGENTS.md").write_bytes(custom)
    assert sync(root).returncode == 0
    assert (root / "AGENTS.md").read_bytes() == custom


def test_alternative_wrapper_destination_does_not_adopt_root(tmp_path):
    root = project(tmp_path / "prj")
    result = sync(root, "--destination", str(tmp_path / "isolati"))
    assert result.returncode == 0, result.stderr
    assert not (root / "AGENTS.md").exists()


def test_missing_bridge_model_in_standard_project_is_not_green(tmp_path):
    root = project(tmp_path / "prj")
    (root / ".claude/templates/AGENTS.md").unlink()
    result = sync(root, "--check")
    assert result.returncode == 2, result.stdout + result.stderr
    assert not (root / "AGENTS.md").exists()


def git(root, *args):
    result = run("git", "-C", str(root), *args)
    assert result.returncode == 0, result.stderr


def setup_alignment(tmp_path, codex=True):
    template = tmp_path / "template"
    template.mkdir()
    model = template / ".claude/templates/AGENTS.md"
    model.parent.mkdir(parents=True)
    model.write_text(BRIDGE, encoding="utf-8")
    git(template, "init", "-q", "-b", "main")
    git(template, "config", "user.name", "Fixture")
    git(template, "config", "user.email", "prova@example.invalid")
    git(template, "add", ".claude")
    git(template, "commit", "-q", "-m", "Fixture con ponte canonico")
    root = tmp_path / "prj"
    root.mkdir()
    if codex:
        (root / ".agents/skills").mkdir(parents=True)
    return template, root


def align(template, root, report, apply=False):
    flags = ["--applica"] if apply else []
    result = run(
        sys.executable,
        str(ALIGN),
        "--template",
        str(template),
        "--progetto",
        str(root),
        "--json",
        str(report),
        *flags,
    )
    assert result.returncode in (0, 1), result.stdout + result.stderr
    return {
        entry["file"]: entry for entry in json.loads(report.read_text(encoding="utf-8"))
    }


def test_alignment_repairs_existing_codex_and_reports_for_commit(tmp_path):
    template, root = setup_alignment(tmp_path)
    report = tmp_path / "report.json"
    planned = align(template, root, report)
    assert planned["AGENTS.md"]["esito"] == "NUOVO"
    assert not (root / "AGENTS.md").exists()
    applied = align(template, root, report, apply=True)
    assert applied["AGENTS.md"]["esito"] == "NUOVO"
    assert (root / "AGENTS.md").read_text(encoding="utf-8") == BRIDGE
    assert align(template, root, report)["AGENTS.md"]["esito"] == "UGUALE"


def test_alignment_does_not_add_codex_to_claude_only_project(tmp_path):
    template, root = setup_alignment(tmp_path, codex=False)
    entries = align(template, root, tmp_path / "report.json", apply=True)
    assert "AGENTS.md" not in entries
    assert not (root / "AGENTS.md").exists()


def test_alignment_does_not_overwrite_unrelated_custom_bridge(tmp_path):
    template, root = setup_alignment(tmp_path)
    custom = (
        "# Politica locale\n\nLeggere CLAUDE.md. Contenuto proprio da conservare.\n"
    )
    (root / "AGENTS.md").write_text(custom, encoding="utf-8")
    entries = align(template, root, tmp_path / "report.json", apply=True)
    assert entries["AGENTS.md"]["esito"] in ("CONFLITTO", "ADATTATO", "MERGE")
    actual = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "Contenuto proprio da conservare." in actual


def test_generated_description_obeys_typography_and_source_stays_verbatim(tmp_path):
    root = project(tmp_path / "prj")
    source = root / ".claude/skills/riprendi/SKILL.md"
    canonical = source.read_bytes().replace(
        b"Ripresa verificata.", "ISO27001 \u2014 guida e \u2013 esempi".encode("utf-8")
    )
    source.write_bytes(canonical)
    assert sync(root).returncode == 0
    output = (root / ".agents/skills/riprendi/SKILL.md").read_text(encoding="utf-8")
    assert "ISO27001 - guida e - esempi" in output
    assert "\u2014" not in output and "\u2013" not in output
    assert source.read_bytes() == canonical
    assert sync(root, "--check").returncode == 0
