#!/usr/bin/env python3
"""Prove della scelta della base e della verifica del merge in allinea-dal-template.

Ogni prova costruisce un repository git finto come template, con la storia che
riproduce un meccanismo osservato nella propagazione del 2026-09-28, e una
cartella come progetto. Le storie non sono inventate: le due forme del difetto
sono state misurate sui file veri di holiday-template a 50fa52b e di
rodrainaudio-reverse-eng a f656c53, e da li vengono le proporzioni fra i blocchi,
che sono cio che decide quale base la somiglianza sceglie.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STRUMENTO = Path(__file__).resolve().parents[1] / "allinea-dal-template.py"

REGOLA = ".claude/rules/norma.md"
PROPRIA = "riga scritta solo in questo progetto"


def righe(prefisso: str, n: int) -> list[str]:
    return [f"{prefisso} {i:03d}" for i in range(n)]


class BaseDelMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="allinea-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.tpl = self.base / "template"
        self.prj = self.base / "progetto"
        (self.tpl / ".claude").mkdir(parents=True)
        self.prj.mkdir()
        self.uscita = ""
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "prova")
        self.git("config", "user.email", "prova@example.invalid")

    def git(self, *args):
        r = subprocess.run(["git", "-C", str(self.tpl), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def commit(self, corpo: list[str], messaggio: str):
        f = self.tpl / REGOLA
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("\n".join(corpo) + "\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", messaggio)

    def scrivi_progetto(self, corpo: list[str]):
        f = self.prj / REGOLA
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("\n".join(corpo) + "\n", encoding="utf-8", newline="\n")

    def allinea(self) -> dict:
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl),
                            "--progetto", str(self.prj), "--json", str(rapporto), "--applica"],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.uscita = r.stdout + r.stderr
        esiti = {e["file"]: e for e in json.loads(rapporto.read_text(encoding="utf-8"))}
        return esiti[REGOLA]

    def risultato(self) -> list[str]:
        return (self.prj / REGOLA).read_text(encoding="utf-8").splitlines()


class ParagrafoDuplicato(BaseDelMerge):
    """Il progetto si era portato a mano un paragrafo dentro una copia vecchia del
    template; il template lo ha poi aggiunto per conto suo in un altro punto,
    insieme ad altro materiale che il progetto non ha. La base più vicina per
    contenuto e allora la copia vecchia, che il paragrafo non lo contiene: la
    differenza base->testa dice "aggiungi il paragrafo", il merge la applica a chi
    ce l'ha già e ne escono due copie senza un conflitto. E il caso di
    holiday-template e local-audio-transcriptor, dove la base scelta era il blob
    del 2026-07-01 e il paragrafo era quello di studio-didattico. Qui nessuna base
    evita il difetto, ed è la ragione per cui la sola scelta della base non basta:
    prenderne una che il paragrafo ce l'ha fa perdere il materiale che il progetto
    non ha ricevuto."""

    PAR = "Parentesi opzionale, non parte del ciclo di default: testo del paragrafo."

    def prepara(self, proprie=()):
        a, b, c = righe("sezione A", 50), righe("sezione B", 50), righe("sezione C", 50)
        d = righe("materiale arrivato col paragrafo", 30)
        n = righe("materiale successivo", 40)
        self.commit(a + b + c, "c1: senza il paragrafo")
        self.commit(a + b + [self.PAR] + c + d, "c2: paragrafo fra B e C, con altro materiale")
        self.commit(a + b + [self.PAR] + c + d + n, "testa: materiale successivo")
        self.scrivi_progetto(a + [self.PAR] + b + c + list(proprie))

    def test_il_paragrafo_non_viene_duplicato(self):
        self.prepara()
        esito = self.allinea()
        self.assertNotEqual(esito["esito"], "MERGE", self.uscita)
        self.assertEqual(self.risultato().count(self.PAR), 1, self.uscita)

    def test_senza_righe_proprie_si_prende_la_testa(self):
        self.prepara()
        esito = self.allinea()
        self.assertEqual(esito["esito"], "SUPERATO", self.uscita)
        self.assertIn("duplicherebbe", esito.get("nota", ""))

    def test_con_righe_proprie_diventa_conflitto(self):
        self.prepara(proprie=[PROPRIA])
        esito = self.allinea()
        self.assertEqual(esito["esito"], "CONFLITTO", self.uscita)
        self.assertEqual(esito["righe_proprie"], [PROPRIA])


class CorrezionePersa(BaseDelMerge):
    """La base scelta per somiglianza contiene già una correzione di una riga che
    il file locale non ha: quella correzione non entra nella differenza
    base->testa e non arriva a nessuno, mentre il blocco grande arriva. E il caso
    di rodrainaudio-reverse-eng, dove fix-accents.py ha ricevuto le righe nuove
    ma non la guardia RESIDUO_DOPPIA_CORREZIONE del 2026-09-09."""

    GUARDIA = "RESIDUO_DOPPIA_CORREZIONE = compila(guardia)"

    def prepara(self, proprie=()):
        corpo = righe("corpo", 200)
        nuove = righe("funzione nuova", 60)
        coda = righe("coda", 10)
        self.commit(corpo, "c1: corpo")
        self.commit(corpo + [self.GUARDIA], "c2: guardia aggiunta")
        self.commit(corpo + [self.GUARDIA] + nuove, "c3: blocco nuovo")
        self.commit(corpo + [self.GUARDIA] + nuove + coda, "testa: coda")
        self.scrivi_progetto(corpo + nuove + list(proprie))

    def test_la_guardia_arriva(self):
        self.prepara()
        esito = self.allinea()
        self.assertIn(self.GUARDIA, self.risultato(), self.uscita)
        self.assertEqual(esito["esito"], "SUPERATO", self.uscita)
        self.assertIn("non consegna", esito.get("nota", ""))

    def test_con_righe_proprie_non_si_applica_in_silenzio(self):
        self.prepara(proprie=[PROPRIA])
        esito = self.allinea()
        self.assertEqual(esito["esito"], "CONFLITTO", self.uscita)
        self.assertIn("non consegna", esito.get("nota", ""))


class BaseAlternativa(BaseDelMerge):
    """La base più vicina per contenuto perde una riga della testa, una più
    lontana fonde pulito e non perde niente: e il caso che la sola verifica non
    risolve, e che distingue la ricerca sulla base dal solo rifiuto del merge."""

    GUARDIA = "guardia che il progetto non ha mai ricevuto"

    def test_si_prova_un_altra_base(self):
        prima, seconda = righe("prima meta", 100), righe("seconda meta", 100)
        mezzo = righe("blocco poi tolto", 50)
        coda = righe("blocco finale", 30)
        self.commit(prima + seconda, "c1: corpo")
        self.commit(prima + seconda + [self.GUARDIA], "c2: guardia")
        self.commit(prima + mezzo + seconda + [self.GUARDIA], "c3: blocco in mezzo")
        self.commit(prima + seconda + [self.GUARDIA] + coda, "testa: mezzo tolto, coda")
        self.scrivi_progetto(prima + mezzo + seconda)
        esito = self.allinea()
        self.assertEqual(esito["esito"], "MERGE", self.uscita)
        r = self.risultato()
        self.assertEqual(r.count(self.GUARDIA), 1, self.uscita)
        self.assertEqual(r.count(mezzo[0]), 1, self.uscita)
        self.assertTrue(set(coda) <= set(r), self.uscita)


class NessunaRegressione(BaseDelMerge):
    """La correzione non deve trasformare in SUPERATO o in CONFLITTO cio che prima
    era classificato bene: senza queste quattro, rifiutare sempre il merge
    passerebbe le prove qui sopra."""

    def storia(self):
        corpo = righe("corpo", 120)
        nuove = righe("aggiunta del template", 20)
        self.commit(corpo, "c1")
        self.commit(corpo + nuove, "testa")
        return corpo, nuove

    def test_identico_resta_uguale(self):
        corpo, nuove = self.storia()
        self.scrivi_progetto(corpo + nuove)
        self.assertEqual(self.allinea()["esito"], "UGUALE", self.uscita)

    def test_versione_storica_intatta_resta_vecchio(self):
        corpo, nuove = self.storia()
        self.scrivi_progetto(corpo)
        self.assertEqual(self.allinea()["esito"], "VECCHIO", self.uscita)

    def test_estensione_locale_resta_merge(self):
        corpo, nuove = self.storia()
        self.scrivi_progetto([PROPRIA] + corpo)
        self.assertEqual(self.allinea()["esito"], "MERGE", self.uscita)
        self.assertEqual(self.risultato(), [PROPRIA] + corpo + nuove)

    def test_personalizzazione_completa_resta_adattato(self):
        corpo, nuove = self.storia()
        self.scrivi_progetto([PROPRIA] + corpo + nuove)
        self.assertEqual(self.allinea()["esito"], "ADATTATO", self.uscita)


class RigaAdattata(BaseDelMerge):
    """Il progetto ha adattato una riga del template, un percorso, e il template
    ha poi aggiunto materiale altrove. Il merge tiene la variante locale e porta
    l'aggiunta: e il caso di lint-md-tables.py e test-tipografia.py su
    retrogame-mod-pok-dev, classificati CONFLITTO fino al 2026-09-29 perché la
    riga della testa sostituita contava come persa."""

    ORIGINALE = '    cartella = os.path.join(ROOT, "_notes", "tmp")'
    ADATTATA = '    cartella = os.path.join(ROOT, "_notes", "lavoro", "tmp")'

    def test_la_variante_locale_non_e_un_conflitto(self):
        corpo, nuove = righe("corpo", 80), righe("aggiunta del template", 20)
        self.commit(corpo[:40] + [self.ORIGINALE] + corpo[40:], "c1")
        self.commit(corpo[:40] + [self.ORIGINALE] + corpo[40:] + nuove, "testa")
        self.scrivi_progetto(corpo[:40] + [self.ADATTATA] + corpo[40:])
        esito = self.allinea()
        self.assertEqual(esito["esito"], "MERGE", self.uscita)
        r = self.risultato()
        self.assertIn(self.ADATTATA, r)
        self.assertNotIn(self.ORIGINALE, r)
        self.assertTrue(set(nuove) <= set(r), self.uscita)

    def test_una_correzione_mancata_resta_guardata(self):
        """La stessa forma, ma al posto della riga corretta il progetto ha la riga
        vecchia del template: e la base troppo recente, e non si perdona."""
        corpo, nuove = righe("corpo", 80), righe("aggiunta del template", 20)
        vecchia, corretta = "valore = calcola(x)", "valore = calcola(x, guardia=True)"
        self.commit(corpo[:40] + [vecchia] + corpo[40:], "c1")
        self.commit(corpo[:40] + [corretta] + corpo[40:], "c2: correzione")
        self.commit(corpo[:40] + [corretta] + corpo[40:] + nuove, "testa")
        self.scrivi_progetto(corpo[:40] + [vecchia] + corpo[40:] + [PROPRIA])
        esito = self.allinea()
        self.assertEqual(esito["esito"], "CONFLITTO", self.uscita)
        self.assertIn("non consegna", esito.get("nota", ""))


class RisoltoAMano(BaseDelMerge):
    """Un file risolto a mano resta ADATTATO finché la testa non cambia, e torna
    a chiedere attenzione appena il template lo tocca di nuovo."""

    def allinea_con(self, *extra) -> dict:
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl),
                            "--progetto", str(self.prj), "--json", str(rapporto), *extra],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.uscita = r.stdout + r.stderr
        return {e["file"]: e for e in json.loads(rapporto.read_text(encoding="utf-8"))}[REGOLA]

    def test_registrato_poi_riaperto(self):
        corpo = righe("corpo", 60)
        self.commit(corpo + ["riga del template"], "c1")
        self.commit(corpo + ["riga del template riscritta dal template"], "testa")
        self.scrivi_progetto(corpo + ["riga riscritta in modo diverso dal progetto, per scelta"])
        self.assertEqual(self.allinea_con()["esito"], "CONFLITTO", self.uscita)
        self.assertEqual(self.allinea_con("--risolto", REGOLA)["esito"], "ADATTATO", self.uscita)
        self.assertTrue((self.prj / ".claude/allineamento-risolti.json").is_file())
        self.assertEqual(self.allinea_con()["esito"], "ADATTATO", self.uscita)
        self.commit(corpo + ["riga del template riscritta dal template"] + righe("nuovo", 5), "testa 2")
        self.assertNotEqual(self.allinea_con()["esito"], "ADATTATO", self.uscita)


class Innesco(BaseDelMerge):
    """Le righe di innesco si prendono dal modello del template e si scrivono
    solo per le skill che il CLAUDE.md non nomina ancora come skill."""

    MODELLO = ("# modello\n\nNorme caricate su richiesta, una riga per situazione. Si tolgono le righe delle skill "
               "che questo progetto non ha istanziato.\n\n"
               "- Quando si prova: skill `prove-che-misurano`.\n"
               "- Quando si recupera: skill `fonti-non-recuperabili`.\n\n## Apprendimenti recenti\n")

    def setUp(self):
        super().setUp()
        for s in ("prove-che-misurano", "fonti-non-recuperabili"):
            d = self.tpl / ".claude/skills" / s
            d.mkdir(parents=True)
            (d / "RIFERIMENTO.md").write_text("norma\n", encoding="utf-8")
            (d / "SKILL.md").write_text("skill\n", encoding="utf-8")
        m = self.tpl / ".claude/templates/CLAUDE.md"
        m.parent.mkdir(parents=True)
        m.write_text(self.MODELLO, encoding="utf-8", newline="\n")
        self.commit(["norma"], "c1")

    def corri(self, applica=True) -> list[dict]:
        rapporto = self.base / "rapporto.json"
        a = ["--innesco"] + (["--applica"] if applica else [])
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl),
                            "--progetto", str(self.prj), "--json", str(rapporto), *a],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.uscita = r.stdout + r.stderr
        return [e for e in json.loads(rapporto.read_text(encoding="utf-8")) if e["esito"] == "INNESCO"]

    def test_scritto_una_volta_prima_degli_apprendimenti(self):
        f = self.prj / "CLAUDE.md"
        f.write_bytes(b"# progetto\r\n\r\nLa vecchia regola `prove-che-misurano.md`.\r\n\r\n## Apprendimenti recenti\r\n\r\n- voce\r\n")
        self.assertEqual(len(self.corri()), 1, self.uscita)
        testo = f.read_bytes()
        self.assertIn(b"skill `prove-che-misurano`.\r\n", testo)
        self.assertLess(testo.index(b"skill `fonti-non-recuperabili`"), testo.index(b"## Apprendimenti"))
        self.assertNotIn(b"Si tolgono", testo)
        self.assertNotIn(b"\n\n", testo.replace(b"\r\n", b"\r"), "fine riga CRLF non conservata")
        self.assertEqual(self.corri(), [], "la seconda corsa non deve riscrivere")

    def test_claude_md_sotto_la_cartella_claude(self):
        """blog-alessio tiene il CLAUDE.md in .claude/: la prima corsa del 2026-09-29 lo
        dava per assente e lasciava il progetto senza innesco."""
        f = self.prj / ".claude/CLAUDE.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("# p\n\n## Apprendimenti recenti\n", encoding="utf-8", newline="\n")
        esiti = self.corri()
        self.assertEqual([e["file"] for e in esiti], [".claude/CLAUDE.md"], self.uscita)
        self.assertIn("skill `prove-che-misurano`.", f.read_text(encoding="utf-8"))
        self.assertFalse((self.prj / "CLAUDE.md").exists())

    def test_indice_esistente_si_completa(self):
        f = self.prj / "CLAUDE.md"
        f.write_text("# p\n\nNorme caricate su richiesta, formulate dal progetto.\n\n- Mia riga: skill `prove-che-misurano`.\n\n## Vincoli di team\n",
                     encoding="utf-8", newline="\n")
        self.corri()
        L = f.read_text(encoding="utf-8").split("\n")
        i = L.index("- Mia riga: skill `prove-che-misurano`.")
        self.assertEqual(L[i + 1], "- Quando si recupera: skill `fonti-non-recuperabili`.")
        self.assertEqual(sum("prove-che-misurano" in r for r in L), 1)


class SkillOpzionale(BaseDelMerge):
    """Una skill istanziata al gate dei pacchetti vive in due posti diversi: nel
    progetto sotto .claude/skills/<nome>, nel template sotto
    templates/<pacchetto>/skills/<nome>. Fino al 2026-10-12 il perimetro ne
    guardava uno solo, perché accettava .claude/skills/<nome> soltanto per i nomi
    di SKILL_SISTEMA: il template correggeva la skill e la copia nel progetto
    restava ferma per sempre, senza che niente diventasse rosso. è la forma del
    guasto per dimenticanza descritta in prove-che-misurano, e riguardava
    craft-apps, pipeline-app, studio-didattico e sync-readme insieme."""

    PKG = ".claude/templates/pacchetto/skills/attrezzo"
    PRJ = ".claude/skills/attrezzo"
    VECCHIA = "versione prima\n"
    TESTA = "versione seconda\n"

    def scrivi_tpl(self, rel: str, testo: str):
        f = self.tpl / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(testo, encoding="utf-8", newline="\n")

    def setUp(self):
        super().setUp()
        self.scrivi_tpl(f"{self.PKG}/SKILL.md", self.VECCHIA)
        self.commit(["norma"], "c1: la skill del pacchetto alla prima versione")
        self.scrivi_tpl(f"{self.PKG}/SKILL.md", self.TESTA)
        self.commit(["norma"], "testa: la skill corretta nel template")

    def istanzia(self, testo: str):
        f = self.prj / self.PRJ / "SKILL.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(testo, encoding="utf-8", newline="\n")

    def corri(self) -> dict:
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl),
                            "--progetto", str(self.prj), "--json", str(rapporto), "--applica"],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.uscita = r.stdout + r.stderr
        return {e["file"]: e for e in json.loads(rapporto.read_text(encoding="utf-8"))}

    def test_copia_intatta_di_una_versione_vecchia_si_aggiorna(self):
        self.istanzia(self.VECCHIA)
        voce = self.corri()[f"{self.PRJ}/SKILL.md"]
        self.assertEqual(voce["esito"], "VECCHIO", self.uscita)
        self.assertEqual(voce["template"], f"{self.PKG}/SKILL.md")
        self.assertEqual((self.prj / self.PRJ / "SKILL.md").read_text(encoding="utf-8"), self.TESTA)

    def test_non_istanziata_non_si_installa(self):
        """L'altra metà della regola, ed è quella che un'estensione distratta romperebbe:
        il gate dei pacchetti decide che cosa un progetto ha, l'allineamento no."""
        esiti = self.corri()
        self.assertNotIn(f"{self.PRJ}/SKILL.md", esiti, self.uscita)
        self.assertFalse((self.prj / self.PRJ).exists(),
                         "l'allineamento ha installato una skill che il gate non ha scelto")

    def test_file_nuovo_dentro_una_skill_istanziata_arriva(self):
        self.scrivi_tpl(f"{self.PKG}/RIFERIMENTO.md", "dettaglio\n")
        self.commit(["norma"], "testa: la skill cresce di un file")
        self.istanzia(self.TESTA)
        esiti = self.corri()
        self.assertEqual(esiti[f"{self.PRJ}/RIFERIMENTO.md"]["esito"], "NUOVO", self.uscita)
        self.assertEqual((self.prj / self.PRJ / "RIFERIMENTO.md").read_text(encoding="utf-8"), "dettaglio\n")

    def test_due_pacchetti_con_lo_stesso_nome_sono_un_conflitto(self):
        self.scrivi_tpl(".claude/templates/altro/skills/attrezzo/SKILL.md", "omonima\n")
        self.commit(["norma"], "testa: un secondo pacchetto porta lo stesso nome")
        self.istanzia(self.VECCHIA)
        voce = self.corri()[self.PRJ]
        self.assertEqual(voce["esito"], "CONFLITTO", self.uscita)
        self.assertIn("origine ambigua", voce["nota"])
        self.assertEqual((self.prj / self.PRJ / "SKILL.md").read_text(encoding="utf-8"), self.VECCHIA,
                         "un'origine ambigua non si risolve scrivendo")


class InnescoDiUnaSkillOpzionale(Innesco):
    """La riga di innesco di una skill opzionale non finisce con il suo nome ma con
    la condizione che la governa, e la skill sta nel pacchetto e non fra quelle di
    sistema. Con la corrispondenza di prima, che chiedeva la chiusura esatta della
    riga e il nome in SKILL_SISTEMA, non veniva innescata mai: la norma arrivava
    nel progetto e non la caricava nessuno, che è esattamente ciò che l'innesco
    esiste per impedire."""

    MODELLO = ("# modello\n\nNorme caricate su richiesta, una riga per situazione. Si tolgono le righe delle skill "
               "che questo progetto non ha istanziato.\n\n"
               "- Quando si prova: skill `prove-che-misurano`.\n"
               "- Quando si recupera: skill `fonti-non-recuperabili`.\n"
               "- Quando si tocca un artefatto: skill `attrezzo`, solo se istanziata al gate dei pacchetti.\n\n"
               "## Apprendimenti recenti\n")

    def setUp(self):
        super().setUp()
        d = self.tpl / ".claude/templates/pacchetto/skills/attrezzo"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("skill\n", encoding="utf-8", newline="\n")
        self.commit(["norma"], "c2: il pacchetto con la sua skill")

    def prepara_claude_md(self):
        f = self.prj / "CLAUDE.md"
        f.write_text("# p\n\n## Apprendimenti recenti\n", encoding="utf-8", newline="\n")
        return f

    def test_istanziata_riceve_la_riga(self):
        d = self.prj / ".claude/skills/attrezzo"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("skill\n", encoding="utf-8", newline="\n")
        f = self.prepara_claude_md()
        self.corri()
        self.assertIn("skill `attrezzo`, solo se istanziata al gate dei pacchetti.",
                      f.read_text(encoding="utf-8"), self.uscita)

    def test_non_istanziata_non_riceve_la_riga(self):
        f = self.prepara_claude_md()
        self.corri()
        self.assertNotIn("`attrezzo`", f.read_text(encoding="utf-8"), self.uscita)


class RiferimentoEsteso(BaseDelMerge):
    """.claude/norme/<nome>.md tiene il caso osservato che giustifica la regola
    omonima, e sta fuori da .claude/rules/ perche' Claude Code carica all'avvio
    tutto cio' che trova li' dentro. Il perimetro dell'allineamento lo tratta
    pero' come rules/, cioe' lo installa anche dove manca, e la ragione e' che
    la regola propagata ci punta: un rimando a un file assente costa a chi legge
    piu' di quanto sarebbe costato non averlo scritto. e' la differenza con una
    skill opzionale, che si aggiorna e non si installa perche' nessuno la
    nomina finche' il gate dei pacchetti non la sceglie."""

    NORMA = ".claude/norme/norma.md"
    VECCHIA = "il caso, prima stesura\n"
    TESTA = "il caso, con la misura rifatta\n"

    def scrivi_tpl(self, testo: str):
        f = self.tpl / self.NORMA
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(testo, encoding="utf-8", newline="\n")

    def setUp(self):
        super().setUp()
        self.scrivi_tpl(self.VECCHIA)
        self.commit(["norma"], "c1: la regola e il suo riferimento esteso")
        self.scrivi_tpl(self.TESTA)
        self.commit(["norma"], "testa: il riferimento esteso corretto")

    def corri(self) -> dict:
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl),
                            "--progetto", str(self.prj), "--json", str(rapporto), "--applica"],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.uscita = r.stdout + r.stderr
        return {e["file"]: e for e in json.loads(rapporto.read_text(encoding="utf-8"))}

    def test_arriva_dove_manca(self):
        voce = self.corri()[self.NORMA]
        self.assertEqual(voce["esito"], "NUOVO", self.uscita)
        self.assertEqual((self.prj / self.NORMA).read_text(encoding="utf-8"), self.TESTA)

    def test_copia_vecchia_si_aggiorna(self):
        f = self.prj / self.NORMA
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(self.VECCHIA, encoding="utf-8", newline="\n")
        voce = self.corri()[self.NORMA]
        self.assertEqual(voce["esito"], "VECCHIO", self.uscita)
        self.assertEqual(f.read_text(encoding="utf-8"), self.TESTA)

    def test_una_aggiunta_locale_non_viene_sovrascritta(self):
        """Il riferimento esteso e' il posto dove un progetto annota il proprio caso:
        se l'allineamento lo trattasse come un file da riscrivere, quel caso sparirebbe
        alla prima passata e nessuno se ne accorgerebbe."""
        f = self.prj / self.NORMA
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(self.VECCHIA + PROPRIA + "\n", encoding="utf-8", newline="\n")
        voce = self.corri()[self.NORMA]
        self.assertIn(voce["esito"], ("MERGE", "CONFLITTO"), self.uscita)
        self.assertIn(PROPRIA, f.read_text(encoding="utf-8"))


class SkillPromossa(BaseDelMerge):
    """Una skill di pacchetto diventa skill di sistema con una riscrittura che git non
    riconosce come rinomina. La copia intatta che un progetto aveva istanziato deve
    risultare una versione vecchia da aggiornare, non una modifica locale in conflitto.
    Il caso è craft-apps, 2026-10-19."""

    def test_copia_intatta_si_aggiorna(self):
        vecchia = "\n".join(f"riga vecchia del pacchetto {i:03d}" for i in range(40)) + "\n"
        nuova = "\n".join(f"riga riscritta per il sistema {i:03d}" for i in range(40)) + "\n"
        orig = self.tpl / ".claude/templates/craft-apps/skills/craft-apps/SKILL.md"
        orig.parent.mkdir(parents=True)
        orig.write_text(vecchia, encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "pacchetto")
        orig.unlink()
        dest = self.tpl / ".claude/skills/craft-apps/SKILL.md"
        dest.parent.mkdir(parents=True)
        dest.write_text(nuova, encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "promossa")
        locale = self.prj / ".claude/skills/craft-apps/SKILL.md"
        locale.parent.mkdir(parents=True)
        locale.write_text(vecchia, encoding="utf-8", newline="\n")
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl), "--progetto", str(self.prj),
                            "--json", str(rapporto), "--applica"], capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        esiti = {e["file"]: e for e in json.loads(rapporto.read_text(encoding="utf-8"))}
        self.assertEqual(esiti[".claude/skills/craft-apps/SKILL.md"]["esito"], "VECCHIO", r.stdout)
        self.assertEqual(locale.read_text(encoding="utf-8"), nuova)


class InnescoDellaSkillNuova(BaseDelMerge):
    """La riga d'innesco di una skill di sistema che arriva nella stessa passata si propone
    subito, non alla passata dopo: il 2026-10-20 37 progetti su 37 risultavano incompleti."""

    def test_innesco_nella_stessa_passata(self):
        modello = self.tpl / ".claude/templates/CLAUDE.md"
        modello.parent.mkdir(parents=True)
        modello.write_text("# <nome>\n\nNorme caricate su richiesta, una riga per situazione.\n\n"
                           "- Va prodotto un documento: skill `craft-apps`, che verifica in locale.\n\n"
                           "## Vincoli di team\n", encoding="utf-8", newline="\n")
        skill = self.tpl / ".claude/skills/craft-apps/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: craft-apps\n---\ncorpo\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "skill di sistema nuova")
        (self.prj / "CLAUDE.md").write_text("# P\n\nNorme caricate su richiesta, una riga per situazione.\n\n"
                                            "## Vincoli di team\n", encoding="utf-8", newline="\n")
        rapporto = self.base / "rapporto.json"
        r = subprocess.run([sys.executable, str(STRUMENTO), "--template", str(self.tpl), "--progetto", str(self.prj),
                            "--json", str(rapporto), "--innesco"], capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        esiti = json.loads(rapporto.read_text(encoding="utf-8"))
        self.assertIn("NUOVO", [e["esito"] for e in esiti if e["file"] == ".claude/skills/craft-apps/SKILL.md"])
        innesco = [e for e in esiti if e["esito"] == "INNESCO"]
        self.assertTrue(innesco and "craft-apps" in innesco[0].get("skill", []), r.stdout)


class Somiglianza(unittest.TestCase):
    """La scorciatoia della somiglianza decide come la ratio piena, a ogni soglia.

    La scorciatoia esiste per il costo, misurato il 2026-10-19 su un progetto mai
    allineato; se decidesse diversamente dalla ratio cambierebbe quali righe il
    merge perdona, cioe' l'esito dell'allineamento, senza nessun errore visibile.
    Le coppie coprono le tre forme: righe quasi uguali, lontane, e lontane per
    lunghezza, che e' il caso che real_quick_ratio scarta senza leggerle."""

    def test_decide_come_la_ratio_piena(self):
        import difflib
        import importlib.util
        spec = importlib.util.spec_from_file_location("allinea", STRUMENTO)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        paragrafo = "La passata di allineamento legge la storia del template e decide file per file. " * 12
        coppie = [
            (paragrafo, paragrafo.replace("decide", "sceglie")),
            (paragrafo, paragrafo[: len(paragrafo) // 3]),
            (paragrafo, "una riga breve e diversa"),
            ("abc def ghi", "abc dxf ghi"),
            ("", "qualcosa"),
            (paragrafo, "".join(reversed(paragrafo))),
            # stessa lunghezza, caratteri diversi: passa real_quick_ratio, la scarta quick_ratio
            ("a" * 300, "b" * 300),
        ]
        for v, r in coppie:
            piena = difflib.SequenceMatcher(None, v, r, autojunk=False).ratio()
            for soglia in (0.3, 0.6, 0.8, 0.95):
                for _ in range(2):  # la seconda volta passa dalla cache
                    q = mod.somiglianza(v, r, soglia)
                    self.assertEqual(q >= soglia, piena >= soglia, (v[:20], r[:20], soglia))
                    if piena >= soglia:
                        self.assertEqual(q, piena)


if __name__ == "__main__":
    unittest.main()
