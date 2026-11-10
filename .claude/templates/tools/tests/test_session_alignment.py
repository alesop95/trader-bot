"""Contratti visibili di allineamento, esclusioni, trasporto e launcher."""

from pathlib import Path
import concurrent.futures
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import pytest

TOOLS = Path(__file__).resolve().parents[1]
AGENTS = TOOLS.parent / "agenti-terminale/tools"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def git(path, *args):
    r = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def history(tmp_path):
    template = tmp_path / "template-claude-developing"
    template.mkdir()
    git(template, "init", "-q", "-b", "main")
    git(template, "config", "user.name", "Fixture")
    git(template, "config", "user.email", "prova@example.invalid")
    p = template / ".claude/PROJECT-SYSTEM.md"
    p.parent.mkdir()
    p.write_text("# Sistema\n", encoding="utf-8")
    model = template / ".claude/templates/AGENTS.md"
    model.parent.mkdir()
    model.write_text("# Codex\nLeggi CLAUDE.md\n", encoding="utf-8")
    git(template, "add", ".")
    git(template, "commit", "-qm", "Base")
    old = git(template, "rev-parse", "HEAD")
    package = template / ".claude/templates/nuovo/README.md"
    package.parent.mkdir()
    package.write_text("# Nuovo\n", encoding="utf-8")
    git(template, "add", ".")
    git(template, "commit", "-qm", "Pacchetto nuovo")
    project = tmp_path / "progetto"
    (project / ".claude").mkdir(parents=True)
    (project / ".claude/allineamento-template.json").write_text(
        json.dumps({"template_commit": old}), encoding="utf-8"
    )
    return template, project


def test_startup_reports_missing_commit_package_and_uncommitted_changes(history):
    template, project = history
    helper = module("state", TOOLS / "stato-template.py")
    r = helper.stato(project, template)
    assert r["commit_indietro"] == 1 and r["pacchetti_nuovi"] == ["nuovo"]
    (template / ".claude/PROJECT-SYSTEM.md").write_text(
        "Modifica non committata\n", encoding="utf-8"
    )
    assert helper.stato(project, template)["modifiche_locali_template"] == 1


def test_unknown_anchor_is_not_reported_as_current(history):
    template, project = history
    helper = module("state", TOOLS / "stato-template.py")
    assert helper.stato(project, template, "0" * 40)["stato"] == "non-verificabile"


def test_expiration_is_visible_without_removing_exclusion():
    helper = module("state", TOOLS / "stato-template.py")
    today = datetime.date(2026, 10, 30)
    assert "SCADUTA" in helper.scadenza("lavoro | fino=2026-10-29", today)
    assert "scade il" in helper.scadenza("lavoro | fino=2026-10-30", today)
    assert "condizione da verificare" in helper.scadenza(
        "lavoro | condizione=review conclusa", today
    )
    assert "SENZA SCADENZA" in helper.scadenza("si allinea dopo", today)


@pytest.mark.parametrize("bom", [b"", b"\xef\xbb\xbf"])
def test_removing_one_line_preserves_mixed_eol_and_backup(tmp_path, bom):
    helper = module("state", TOOLS / "stato-template.py")
    path = tmp_path / "esclusi.txt"
    first = b"# nota\nE:/uno # motivo\r\n"
    last = b"E:/tre # altro\r"
    original = bom + first + b"E:/due # da togliere\n" + last
    path.write_bytes(original)
    result = helper.rimuovi(path, "e:\\due\\")
    assert path.read_bytes() == bom + first + last
    assert Path(result["backup"]).read_bytes() == original
    assert result["righe_prima"] == 4 and result["righe_dopo"] == 3


def test_duplicate_exclusions_refuse_ambiguous_rewrite(tmp_path):
    helper = module("state", TOOLS / "stato-template.py")
    path = tmp_path / "esclusi.txt"
    data = b"E:/due # uno\nE:/due # due\n"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        helper.rimuovi(path, "E:/due")
    assert path.read_bytes() == data


def test_alignment_receipt_is_managed_and_does_not_claim_conflicts_resolved(
    history, tmp_path
):
    template, project = history
    (project / ".agents/skills").mkdir(parents=True)
    report = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "allinea-dal-template.py"),
            "--template",
            str(template),
            "--progetto",
            str(project),
            "--json",
            str(report),
            "--applica",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = project / ".claude/ultimo-allineamento.md"
    assert receipt.is_file() and "AGENTS.md" in receipt.read_text(encoding="utf-8")
    entries = json.loads(report.read_text(encoding="utf-8"))
    assert any(
        e["file"] == ".claude/ultimo-allineamento.md" and e["esito"] == "NUOVO"
        for e in entries
    )
    helper = module("state", TOOLS / "stato-template.py")
    text = helper.ricevuta(
        [{"file": "a", "esito": "NUOVO"}, {"file": "b", "esito": "CONFLITTO"}], "0" * 40
    )
    assert "Conflitti ancora da risolvere: 1" in text


def test_filone_expectation_reaches_only_the_project_it_names(history, tmp_path):
    """La ricevuta porta al progetto le sole attese che lo nominano e ancora aperte.

    Il registro dei filoni resta a monte e non viene consegnato: senza questa resa
    un progetto ripropone una decisione gia' presa (L-018 di un progetto istanziato).
    """
    template, project = history
    (template / "docs").mkdir(exist_ok=True)
    (template / "docs/attese-dai-filoni.json").write_text(
        json.dumps(
            [
                {
                    "progetto": project.name,
                    "filone": "Lettura ancorata",
                    "attesa": "la specifica | con la barra",
                    "documento": "docs/proposta.md",
                    "aperta": "2026-11-09",
                },
                {
                    "progetto": "progetto-di-qualcun-altro",
                    "filone": "Filone estraneo",
                    "attesa": "niente che riguardi questo progetto",
                    "documento": "docs/altro.md",
                    "aperta": "2026-11-09",
                },
                {
                    "progetto": project.name,
                    "filone": "Filone gia chiuso",
                    "attesa": "consegnata il mese scorso",
                    "documento": "docs/chiuso.md",
                    "aperta": "2026-10-01",
                    "stato": "chiusa",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = tmp_path / "report-attese.json"
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "allinea-dal-template.py"),
            "--template",
            str(template),
            "--progetto",
            str(project),
            "--json",
            str(report),
            "--applica",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    testo = (project / ".claude/ultimo-allineamento.md").read_text(encoding="utf-8")
    assert "Il template aspetta da questo progetto" in testo
    assert "Lettura ancorata" in testo
    assert "la specifica / con la barra" in testo
    assert "Filone estraneo" not in testo
    assert "Filone gia chiuso" not in testo


def test_expectation_document_is_cited_from_the_template_folder(tmp_path):
    """Il documento a monte si cita con la cartella del template davanti.

    Senza il prefisso il controllo dei link del progetto legge un percorso locale
    inesistente e lo riscrive, e la ricevuta diverge dal generatore a ogni passata.
    """
    helper = module("state", TOOLS / "stato-template.py")
    template = tmp_path / "template-finto"
    (template / "docs").mkdir(parents=True)
    (template / "docs/attese-dai-filoni.json").write_text(
        json.dumps(
            [
                {
                    "progetto": "progetto",
                    "filone": "F",
                    "attesa": "A",
                    "documento": "docs/proposta.md",
                    "aperta": "2026-11-09",
                }
            ]
        ),
        encoding="utf-8",
    )
    voci = helper.attese(template, tmp_path / "progetto")
    assert [v["documento"] for v in voci] == ["template-finto/docs/proposta.md"]


def test_second_pass_does_not_rewrite_an_identical_receipt(history, tmp_path):
    """La seconda misura di una passata non deve trovare la ricevuta da riscrivere.

    Con un'attesa aperta la ricevuta esiste anche senza file consegnati, e senza
    questo confronto il progetto risulterebbe «incompleto» a ogni corsa: misurato
    il 2026-11-09 su un progetto reale.
    """
    template, project = history
    (template / "docs").mkdir(exist_ok=True)
    (template / "docs/attese-dai-filoni.json").write_text(
        json.dumps(
            [
                {
                    "progetto": project.name,
                    "filone": "Lettura ancorata",
                    "attesa": "la specifica",
                    "documento": "docs/proposta.md",
                    "aperta": "2026-11-09",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def passata(nome):
        report = tmp_path / nome
        esito = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "allinea-dal-template.py"),
                "--template",
                str(template),
                "--progetto",
                str(project),
                "--json",
                str(report),
                "--applica",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert esito.returncode == 0, esito.stdout + esito.stderr
        return json.loads(report.read_text(encoding="utf-8"))

    prima = passata("prima.json")
    assert any(
        e["file"] == ".claude/ultimo-allineamento.md" and e["esito"] == "NUOVO" for e in prima
    )
    dopo = passata("dopo.json")
    assert not [
        e
        for e in dopo
        if e["file"] == ".claude/ultimo-allineamento.md"
        and e["esito"] in ("NUOVO", "VECCHIO")
    ]
    assert "Il template aspetta da questo progetto" in (
        project / ".claude/ultimo-allineamento.md"
    ).read_text(encoding="utf-8")


def test_receipt_exists_for_an_expectation_even_without_delivered_files():
    """Un'attesa raggiunge il progetto anche quando la passata non scrive nulla."""
    helper = module("state", TOOLS / "stato-template.py")
    assert helper.ricevuta([], "0" * 40) is None
    testo = helper.ricevuta(
        [],
        "0" * 40,
        [{"filone": "F", "attesa": "A", "documento": "d.md", "aperta": "2026-11-09"}],
    )
    assert "Il template aspetta da questo progetto" in testo
    assert "| F | A | `d.md` | 2026-11-09 |" in testo


def test_a_dry_measure_is_not_a_propagation():
    """Una misura non è una propagazione: il registro lo dice con lo stato, non con l'albero.

    Il registro viene riscritto anche da una passata a vuoto, quindi confrontare il solo
    albero misurato faceva dichiarare «passata gia' fatta» un template che nessuno aveva
    propagato. Misurato il 2026-11-09, mentre si costruiva la misura in sottofondo.
    """
    helper = module("sospeso", TOOLS / "passata-in-sospeso.py")
    albero = "a" * 40

    def voci(*stati):
        return [{"stato": s, "misurato_il": "2026-11-09T15:55:39",
                 "template_albero_claude": albero} for s in stati]

    codice, righe = helper.verdetto(voci("applicato", "applicato"), albero, "CMD")
    assert codice == 0 and "passata gia fatta" in righe[0]
    codice, righe = helper.verdetto(
        voci("applicato", "da-allineare", "conflitti"), albero, "CMD")
    assert codice == 1, righe
    testo = "\n".join(righe)
    assert "misura gia' fatta" in testo
    assert "2 progetti hanno file da ricevere" in testo
    assert "di cui 1 in conflitto" in testo
    vecchie = [{"stato": "applicato", "misurato_il": "2026-11-01T10:00:00",
                "template_albero_claude": "b" * 40}]
    codice, righe = helper.verdetto(vecchie, albero, "CMD")
    assert codice == 1 and "e cambiato dall'ultima passata" in righe[0]
    assert helper.verdetto([], albero, "CMD")[0] == 1


def test_registry_entries_in_temp_folders_are_not_counted(tmp_path):
    """Le prove in cartelle temporanee non rimisurate direbbero propagazione dovuta per sempre."""
    helper = module("sospeso", TOOLS / "passata-in-sospeso.py")
    vero = tmp_path / "progetto-vero"
    vero.mkdir()
    voci = {str(vero): {"stato": "applicato", "template_albero_claude": "a" * 40},
            str(tmp_path / "assente"): {"stato": "applicato", "template_albero_claude": "a" * 40},
            "C:/Users/x/AppData/Local/Temp/prova": {"stato": "applicato",
                                                    "template_albero_claude": "a" * 40}}
    scelti = helper.seleziona(voci)
    assert len(scelti) == (1 if "temp" not in str(vero).lower() else 0)


def test_background_measure_does_not_start_while_a_pass_holds_the_lock(history):
    """Due passate insieme si contenderebbero i file dei progetti: la seconda non parte."""
    template, _ = history
    (template / ".claude/templates/PACKAGES.md").write_text("# Catalogo\n", encoding="utf-8")
    base = template / "_notes/allineamento"
    base.mkdir(parents=True, exist_ok=True)
    (base / ".in-corso").write_text("1234", encoding="utf-8")
    esito = subprocess.run(
        [sys.executable, str(TOOLS / "passata-in-sospeso.py"), "--misura"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(template),
    )
    assert esito.returncode == 1, esito.stdout + esito.stderr
    assert "gia' in corso" in esito.stdout or "solo in PowerShell" in esito.stdout
    assert not (base / "ultima-misura.txt").exists()


def test_grc_reinstall_repairs_missing_codex_exclusions_without_rewriting_skill(
    tmp_path,
):
    project = tmp_path / "progetto"
    skill = project / ".claude/templates/grc-skills/skills/iso27001/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("Fonte esterna\n", encoding="utf-8")
    (project / ".agents/skills").mkdir(parents=True)
    (project / "tools").mkdir()
    for name in ["dashes-exclude.txt", "accents-exclude.txt"]:
        (project / "tools" / name).write_bytes(b"# regole\r\n")
    cmd = [
        sys.executable,
        str(TOOLS.parent / "grc-skills/tools/grc-skills.py"),
        "--radice",
        str(project),
        "installa",
        "iso27001",
    ]
    for _ in range(2):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
    assert (
        project / ".claude/skills/iso27001/SKILL.md"
    ).read_bytes() == skill.read_bytes()
    for name in ["dashes-exclude.txt", "accents-exclude.txt"]:
        data = (project / "tools" / name).read_bytes()
        assert (
            data.startswith(b"# regole\r\n")
            and data.count(b".agents/skills/iso27001/") == 1
        )
        assert b"\n" not in data.replace(b"\r\n", b"")


def test_mailbox_bidirectional_atomic_delivery_and_explicit_archive(tmp_path):
    bus = module("mailbox", AGENTS / "posta-sessioni.py")
    root = tmp_path / "posta"
    bus.registra(root, "claude", "claude", tmp_path / "a")
    bus.registra(root, "codex", "codex", tmp_path / "b")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        messages = list(
            executor.map(
                lambda n: bus.invia(root, "claude", "codex", "evidenza", "dato %d" % n),
                range(8),
            )
        )
    assert len(bus.leggi(root, "codex")) == 8
    assert not list(root.rglob(".tmp-*"))
    assert len({x["id"] for x in messages}) == 8
    assert len(bus.leggi(root, "codex", True)) == 8 and bus.leggi(root, "codex") == []
    bus.invia(root, "codex", "claude", "correzione", "Correggo la lettura del dato.")
    assert bus.leggi(root, "claude")[0]["testo"] == "Correggo la lettura del dato."
    with pytest.raises(ValueError):
        bus.invia(root, "claude", "../altro", "x", "x")


@pytest.mark.skipif(os.name != "nt", reason="esercita launcher PowerShell Windows")
@pytest.mark.parametrize("account", [1, 2, 3])
def test_all_codex_accounts_cleanup_after_backend_failure(tmp_path, account):
    tools = tmp_path / "tools"
    tools.mkdir()
    shutil.copyfile(AGENTS / "Avvia-Codex.ps1", tools / "Avvia-Codex.ps1")
    (tools / "Pulisci-Codex.ps1").write_text(
        "param([int]$Account,[switch]$Tutto)\n[IO.File]::WriteAllText($env:PROVA_LOG, (ConvertTo-Json @{Account=$Account;Tutto=[bool]$Tutto}))\n",
        encoding="utf-8-sig",
    )
    profile = tmp_path / "profilo"
    root = profile / (".codex-account%d" % account)
    root.mkdir(parents=True)
    (root / "config.toml").write_text("# fixture\n", encoding="utf-8")
    log = tmp_path / "pulizia.json"
    script = tmp_path / "run.ps1"
    script.write_text(
        "function global:codex { throw 'backend simulato terminato' }\n& $env:PROVA_LAUNCHER -Account "
        + str(account)
        + " -Progetto $env:PROVA_PROGETTO -NoPosta\n",
        encoding="utf-8-sig",
    )
    env = dict(
        os.environ,
        USERPROFILE=str(profile),
        PROVA_LOG=str(log),
        PROVA_LAUNCHER=str(tools / "Avvia-Codex.ps1"),
        PROVA_PROGETTO=str(tmp_path),
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    result = json.loads(log.read_text(encoding="utf-8-sig"))
    assert result == {"Account": account, "Tutto": True}


@pytest.mark.skipif(os.name != "nt", reason="profilo PowerShell Windows")
def test_profile_installs_all_three_launchers_and_preserves_external_bytes(tmp_path):
    user = tmp_path / "utente"
    user.mkdir()
    for agent in ["claude", "codex"]:
        for n in [1, 2, 3]:
            (user / (".%s-account%d" % (agent, n))).mkdir()
    profile = tmp_path / "profilo.ps1"
    before = "# segno \u00ae\n# altra riga\r\n".encode("utf-8")
    profile.write_bytes(before)
    env = dict(os.environ, USERPROFILE=str(user))
    cmd = [
        "powershell",
        "-NoProfile",
        "-File",
        str(AGENTS / "Installa-Comandi.ps1"),
        "-Profilo",
        str(profile),
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    first = profile.read_bytes()
    assert first.startswith(before)
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert profile.read_bytes() == first
    content = first.decode("utf-8")
    for n in [1, 2, 3]:
        assert (
            "function codex-account%d" % n in content
            and "function claude-account%d" % n in content
        )
        assert "Avvia-Codex.ps1' -Account %d" % n in content
        assert "Avvia-Claude.ps1' -Account %d" % n in content


@pytest.mark.skipif(os.name != "nt", reason="launcher PowerShell Windows")
@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_both_launchers_offer_same_writable_mailbox_to_backend(tmp_path, agent):
    tools = tmp_path / "template/.claude/templates/agenti-terminale/tools"
    tools.mkdir(parents=True)
    helpers = tools.parent.parent / "tools"
    helpers.mkdir()
    (helpers / "stato-template.py").write_text("print('AVVISO-TEST')\n", encoding="utf-8")
    for name in [
        "Avvia-Codex.ps1",
        "Avvia-Claude.ps1",
        "Posta-Sessioni.ps1",
        "posta-sessioni.py",
    ]:
        shutil.copyfile(AGENTS / name, tools / name)
    (tools / "Pulisci-Codex.ps1").write_text(
        "param([int]$Account,[switch]$Tutto)\n", encoding="utf-8-sig"
    )
    user = tmp_path / "utente"
    root = user / (".%s-account1" % agent)
    root.mkdir(parents=True)
    if agent == "codex":
        (root / "config.toml").write_text("# fixture\n", encoding="utf-8")
    capture = tmp_path / "args.json"
    mailbox = tmp_path / "posta"
    script = tmp_path / "run.ps1"
    script.write_text(
        "function global:"
        + agent
        + " { [IO.File]::WriteAllText($env:PROVA_ARGS,(ConvertTo-Json @{args=@($args);id=$env:PROJECT_AGENT_MAILBOX_ID;root=$env:PROJECT_AGENT_MAILBOX_ROOT})) }\n& $env:PROVA_LAUNCHER -Account 1 -Progetto $env:PROVA_PROGETTO -Posta $env:PROVA_POSTA\n",
        encoding="utf-8-sig",
    )
    env = dict(
        os.environ,
        USERPROFILE=str(user),
        PROVA_ARGS=str(capture),
        PROVA_LAUNCHER=str(
            tools / ("Avvia-" + ("Codex" if agent == "codex" else "Claude") + ".ps1")
        ),
        PROVA_PROGETTO=str(tmp_path),
        PROVA_POSTA=str(mailbox),
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AVVISO-TEST" in result.stdout
    data = json.loads(capture.read_text(encoding="utf-8-sig"))
    assert (
        "--add-dir" in data["args"]
        and str(mailbox) in data["args"]
        and data["root"] == str(mailbox)
    )
    registered = json.loads(
        (mailbox / data["id"] / "partecipante.json").read_text(encoding="utf-8")
    )
    assert registered["agente"] == agent


def test_identity_guard_checks_new_files_and_respects_gitignore(tmp_path):
    git(tmp_path, "init", "-q")
    rules = tmp_path / ".claude"
    rules.mkdir()
    text = "nonammessa" + "@" + "esempio.invalid"
    (rules / "nuova.md").write_text(text, encoding="utf-8")
    (rules / "esclusa.md").write_text(text, encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".claude/esclusa.md\n", encoding="utf-8")
    guard = module("identity_guard", TOOLS / "test-identita-personali.py")
    results = guard.cerca_forme(tmp_path)
    assert len(results) == 1
    assert results[0][0] == ".claude/nuova.md"
