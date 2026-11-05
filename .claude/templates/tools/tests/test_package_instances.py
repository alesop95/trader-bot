"""L'allineamento deve misurare l'istanza, non soltanto il magazzino del pacchetto."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("packages_tested", TOOLS / "verifica-pacchetti.py")
packages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packages)


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, encoding="utf-8")


def git(root, *args):
    result = run("git", "-C", str(root), *args)
    assert result.returncode == 0, result.stderr


def setup(tmp_path, adopted=False):
    template, project = tmp_path / "template", tmp_path / "progetto"
    template.mkdir()
    project.mkdir()
    recipe = json.loads((TOOLS.parent / "pacchetti-istanza.json").read_text(encoding="utf-8"))
    source_recipe = template / packages.RICETTE
    source_recipe.parent.mkdir(parents=True)
    source_recipe.write_text(json.dumps(recipe), encoding="utf-8")
    (template / ".claude/templates/PACKAGES.md").write_text("| `anonymization` | descrizione |\n", encoding="utf-8")
    for entry in recipe["ricette"]["anonymization"]["file"]:
        source = template / entry["origine"]
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Fixture del pacchetto\n", encoding="utf-8")
    git(template, "init", "-q", "-b", "main")
    git(template, "config", "user.name", "Fixture")
    git(template, "config", "user.email", "prova@example.invalid")
    git(template, "add", ".")
    git(template, "commit", "-q", "-m", "Modelli della prova")
    if adopted:
        registry = project / packages.REGISTRO
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({"versione": 1, "pacchetti": {"anonymization": {"stato": "adottato"}}}), encoding="utf-8")
    return template, project, recipe


def align(template, project, output, apply=False):
    result = run(sys.executable, str(TOOLS / "allinea-dal-template.py"), "--template", str(template), "--progetto", str(project), "--json", str(output), *(["--applica"] if apply else []))
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_model_delivery_does_not_implicitly_adopt_package(tmp_path):
    template, project, _ = setup(tmp_path)
    report = align(template, project, tmp_path / "report.json", apply=True)
    assert (project / ".claude/templates/anonymization/tools/Test-Anonymization.py").is_file()
    assert not (project / "tools/Test-Anonymization.py").exists()
    state = next(r for r in report if r["esito"] == "PACCHETTI")["pacchetti"][0]
    assert state["decisione"] == "non-censito"
    assert state["istanza"] == "non-istanziato"


def test_adopted_package_restores_missing_runtime_files_and_second_pass_is_stable(tmp_path):
    template, project, recipe = setup(tmp_path, adopted=True)
    preview = align(template, project, tmp_path / "preview.json")
    assert any(r["file"] == "tools/Test-Anonymization.py" and r["esito"] == "NUOVO" for r in preview)
    assert not (project / "tools/Test-Anonymization.py").exists()
    align(template, project, tmp_path / "first.json", apply=True)
    for entry in recipe["ricette"]["anonymization"]["file"]:
        assert (project / entry["destinazione"]).read_bytes() == (template / entry["origine"]).read_bytes().replace(b"\r\n", b"\n")
    before = {str(p.relative_to(project)): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()}
    align(template, project, tmp_path / "second.json", apply=True)
    after = {str(p.relative_to(project)): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()}
    assert before == after
    assert not (project / "_notes/.anonymization-patterns.json").exists()


def test_incomplete_existing_instance_is_reported_without_inventing_consent(tmp_path):
    _, project, recipe = setup(tmp_path)
    rule = project / ".claude/rules/anonymization.md"
    rule.parent.mkdir(parents=True)
    rule.write_text("# Regola locale\n", encoding="utf-8")
    state = packages.audit(project, recipe, "")[0]
    assert state["istanza"] == "parziale"
    assert state["decisione"] == "non-censito"
    assert state["configurazione"] == "da-configurare"
    assert packages.piano(project, recipe, set()) == []


def test_adopted_existing_rule_receives_the_new_published_revision(tmp_path):
    template, project, _ = setup(tmp_path, adopted=True)
    rule = project / ".claude/rules/anonymization.md"
    rule.parent.mkdir(parents=True)
    rule.write_text("# Fixture del pacchetto\n", encoding="utf-8")
    source = template / ".claude/templates/anonymization/rules/anonymization.md"
    source.write_text("# Fixture del pacchetto\n\nRegola aggiornata.\n", encoding="utf-8")
    git(template, "add", ".")
    git(template, "commit", "-q", "-m", "Aggiorna la regola della prova")
    align(template, project, tmp_path / "report.json", apply=True)
    assert "Regola aggiornata." in rule.read_text(encoding="utf-8")


def test_existing_scripts_convention_is_updated_without_a_second_tool_copy(tmp_path):
    template, project, _ = setup(tmp_path, adopted=True)
    tool = project / "scripts/Test-Anonymization.py"
    tool.parent.mkdir()
    tool.write_text("# Fixture del pacchetto\n", encoding="utf-8")
    source = template / ".claude/templates/anonymization/tools/Test-Anonymization.py"
    source.write_text("# Fixture del pacchetto\n# Nuova revisione\n", encoding="utf-8")
    git(template, "add", ".")
    git(template, "commit", "-q", "-m", "Aggiorna lo strumento della prova")
    align(template, project, tmp_path / "report.json", apply=True)
    assert "Nuova revisione" in tool.read_text(encoding="utf-8")
    assert not (project / "tools/Test-Anonymization.py").exists()


@pytest.mark.parametrize("destination", ["../esterno.py", ".git/config", ".claude/templates/falso.py"])
def test_adoption_contract_cannot_write_outside_runtime(tmp_path, destination):
    _, project, recipe = setup(tmp_path, adopted=True)
    recipe["ricette"]["anonymization"]["file"][0]["destinazione"] = destination
    with pytest.raises(ValueError):
        packages.piano(project, recipe, {item["origine"] for item in recipe["ricette"]["anonymization"]["file"]})
