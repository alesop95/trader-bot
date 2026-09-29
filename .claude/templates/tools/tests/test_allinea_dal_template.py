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

    def test_indice_esistente_si_completa(self):
        f = self.prj / "CLAUDE.md"
        f.write_text("# p\n\nNorme caricate su richiesta, formulate dal progetto.\n\n- Mia riga: skill `prove-che-misurano`.\n\n## Vincoli di team\n",
                     encoding="utf-8", newline="\n")
        self.corri()
        L = f.read_text(encoding="utf-8").split("\n")
        i = L.index("- Mia riga: skill `prove-che-misurano`.")
        self.assertEqual(L[i + 1], "- Quando si recupera: skill `fonti-non-recuperabili`.")
        self.assertEqual(sum("prove-che-misurano" in r for r in L), 1)


if __name__ == "__main__":
    unittest.main()
