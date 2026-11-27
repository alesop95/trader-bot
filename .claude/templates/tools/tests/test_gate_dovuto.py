"""Il gate dei pacchetti dovuto, visto dalla ricevuta dell'allineamento e dall'apertura di sessione.

Dal 2026-11-20, L-002 di un progetto istanziato: un allineamento in blocco portava il catalogo nel
progetto senza eseguire il gate, riservato al proprietario, e niente lo diceva alla sessione
successiva. Un progetto di novanta commit non aveva mai fatto una tornata. Queste prove
esercitano il percorso vero: lo strumento di allineamento su un template e un progetto
costruiti, la ricevuta che scrive, e la riga che verifica-pacchetti.py dà all'apertura.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STRUMENTI = Path(__file__).resolve().parents[1]
ALLINEA = STRUMENTI / "allinea-dal-template.py"
VERIFICA = STRUMENTI / "verifica-pacchetti.py"
CATALOGO = ".claude/templates/PACKAGES.md"
RICEVUTA = ".claude/ultimo-allineamento.md"


def catalogo(*nomi):
    righe = ["| Pacchetto | Che cosa fa |", "|---|---|"] + [f"| `{n}` | prova |" for n in nomi]
    return "\n".join(righe) + "\n"


class GateDovuto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gate-")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.tpl, self.prj = base / "template", base / "progetto"
        self.tpl.mkdir()
        self.prj.mkdir()
        for args in (("init", "-q", "-b", "main"), ("config", "user.name", "prova"),
                     ("config", "user.email", "prova@example.invalid")):
            subprocess.run(["git", "-C", str(self.tpl), *args], check=True, capture_output=True)
        self.pubblica("alfa", "beta")

    def pubblica(self, *nomi, altre_righe=""):
        f = self.tpl / CATALOGO
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(catalogo(*nomi) + altre_righe, encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(self.tpl), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.tpl), "commit", "-q", "-m", "catalogo"], check=True, capture_output=True)

    def allinea(self):
        r = subprocess.run([sys.executable, str(ALLINEA), "--template", str(self.tpl), "--progetto", str(self.prj),
                            "--applica"], capture_output=True, text=True, encoding="utf-8")
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
        return (self.prj / RICEVUTA).read_text(encoding="utf-8")

    def verifica(self, *extra):
        r = subprocess.run([sys.executable, str(VERIFICA), "--progetto", str(self.prj), "--template", str(self.prj), *extra],
                           capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def test_progetto_mai_passato_dal_gate_risulta_dovuto(self):
        ricevuta = self.allinea()
        self.assertIn("## Gate dei pacchetti", ricevuta)
        self.assertIn("Gate dovuto: 2 voci del catalogo su 2", ricevuta)
        self.assertIn("nessuna tornata registrata", ricevuta)
        codice, uscita = self.verifica("--gate")
        self.assertEqual(codice, 0)
        self.assertIn("Gate dovuto: 2", uscita)

    def test_dopo_la_tornata_il_gate_e_in_pari_anche_nella_ricevuta(self):
        self.allinea()
        codice, uscita = self.verifica("--registra-tornata")
        self.assertEqual(codice, 0, uscita)
        self.assertIn("Gate in pari", uscita)
        registro = json.loads((self.prj / ".claude/pacchetti.json").read_text(encoding="utf-8"))
        self.assertEqual(registro["versione"], 1)
        self.assertEqual(registro["tornate"][0]["catalogo"], ["alfa", "beta"])
        # la corsa seguente non consegna niente, ma deve togliere il «dovuto» rimasto
        ricevuta = self.allinea()
        self.assertNotIn("Gate dovuto", ricevuta)
        self.assertIn("Gate in pari", ricevuta)

    def test_una_voce_nuova_nel_catalogo_riapre_il_debito(self):
        self.allinea()
        self.verifica("--registra-tornata")
        self.pubblica("alfa", "beta", "gamma")
        ricevuta = self.allinea()
        self.assertIn("Gate dovuto: 1 voci del catalogo su 3", ricevuta)
        self.assertIn("`gamma`", ricevuta)
        self.assertNotIn("`alfa`,", ricevuta)

    def test_una_voce_decisa_senza_tornata_non_e_debito(self):
        (self.prj / ".claude").mkdir(parents=True, exist_ok=True)
        (self.prj / ".claude/pacchetti.json").write_text(json.dumps(
            {"versione": 1, "pacchetti": {"alfa": {"stato": "rifiutato", "data": "2026-11-20", "motivo": "prova"}}}),
            encoding="utf-8")
        ricevuta = self.allinea()
        self.assertIn("Gate dovuto: 1 voci del catalogo su 2", ricevuta)
        self.assertIn("`beta`", ricevuta)

    def test_skill_di_sistema_consegnata_senza_scelta_al_gate(self):
        skill = ".claude/skills/analisi-codice/SKILL.md"
        f = self.tpl / skill
        f.parent.mkdir(parents=True)
        f.write_text("---\nname: analisi-codice\ndescription: Analisi su richiesta.\n---\n",
                     encoding="utf-8", newline="\n")
        self.pubblica("alfa", altre_righe=(
            "| `analisi-codice` | Analisi | Non passa dal gate: skill di sistema | Attrezzi | Python |\n"
            "| `separazione-ambienti` | Guida | Non passa dal gate dei pacchetti: ha un proprio gate | Guida | Nessuno |\n"
        ))
        ricevuta = self.allinea()
        self.assertIn("| NUOVO | `" + skill + "` |", ricevuta)
        self.assertEqual((self.prj / skill).read_bytes(), f.read_bytes())
        self.assertIn("Gate dovuto: 1 voci del catalogo su 1", ricevuta)
        self.assertIn("Voci mai viste: `alfa`.", ricevuta)
        codice, uscita = self.verifica("--gate")
        self.assertEqual(codice, 0, uscita)
        self.assertIn("Gate dovuto: 1 voci del catalogo su 1", uscita)
        sync = STRUMENTI / "sync-codex-skills.py"
        for extra in ([], ["--check"]):
            esito = subprocess.run([sys.executable, str(sync), "--project-root", str(self.prj), *extra],
                                   capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(esito.returncode, 0, esito.stdout + esito.stderr)
        self.assertTrue((self.prj / ".agents/skills/analisi-codice/SKILL.md").is_file())

    def test_avviso_su_copia_rinominata_conserva_la_ricevuta(self):
        src = self.tpl / ".claude/templates/prova/tools/converti.py"
        src.parent.mkdir(parents=True)
        src.write_text("print('prova scollegata')\n", encoding="utf-8", newline="\n")
        locale = self.prj / "tools/converti-pagine.py"
        locale.parent.mkdir()
        locale.write_bytes(src.read_bytes())
        self.pubblica("alfa", "beta", "gamma")
        ricevuta = self.allinea()
        self.assertIn("| NUOVO | `" + src.relative_to(self.tpl).as_posix() + "` |", ricevuta)
        self.assertEqual(self.allinea(), ricevuta)


VECCHIA = ("- Apertura di sessione: `python .claude/templates/tools/verifica-pacchetti.py --gate`; "
           "se dice «Gate dovuto», la prima risposta chiede al proprietario `/gate-pacchetti`: skill `gate-pacchetti`.")
NUOVA = ("- Apertura di sessione: le righe di `python .claude/templates/tools/verifica-pacchetti.py --riepilogo` "
         "entrano nella prima risposta; se dicono «Gate dovuto» si avvia la skill `gate-pacchetti`.")


class RiepilogoERigaSuperata(GateDovuto):
    """Dal 2026-11-20: /riprendi mostra che cosa il progetto usa del template e avvia il gate;
    la riga di innesco che chiedeva di lanciarlo a mano va sostituita dove è già propagata."""

    def test_il_riepilogo_dice_allineamento_adottati_e_gate(self):
        self.allinea()
        (self.prj / ".claude/allineamento-template.json").write_text(
            json.dumps({"template_commit": "abcdef1234567", "allineato_il": "2026-11-20", "strumento": "prova"}),
            encoding="utf-8")
        (self.prj / ".claude/pacchetti.json").write_text(json.dumps(
            {"versione": 1, "pacchetti": {"alfa": {"stato": "rimandato", "data": "2026-11-20", "motivo": "prova"}}}),
            encoding="utf-8")
        codice, uscita = self.verifica("--riepilogo")
        self.assertEqual(codice, 0, uscita)
        self.assertIn("Template: allineato al commit abcdef1 del 2026-11-20", uscita)
        self.assertIn("Pacchetti adottati: nessuno registrato", uscita)
        self.assertIn("Pacchetti rimandati: alfa.", uscita)
        self.assertIn("Gate dovuto: 1 voci del catalogo su 2", uscita)

    def prepara_innesco(self, riga_progetto):
        modello = self.tpl / ".claude/templates/CLAUDE.md"
        modello.write_text("# Modello\n\nNorme caricate su richiesta, una riga per situazione.\n\n" + NUOVA + "\n",
                           encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(self.tpl), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.tpl), "commit", "-q", "-m", "modello"], check=True, capture_output=True)
        (self.prj / ".claude/skills/gate-pacchetti").mkdir(parents=True)
        (self.prj / "CLAUDE.md").write_text("# Progetto\n\nNorme caricate su richiesta.\n\n" + riga_progetto + "\n",
                                            encoding="utf-8", newline="\n")

    def allinea_innesco(self):
        r = subprocess.run([sys.executable, str(ALLINEA), "--template", str(self.tpl), "--progetto", str(self.prj),
                            "--applica", "--innesco"], capture_output=True, text=True, encoding="utf-8")
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
        return (self.prj / "CLAUDE.md").read_text(encoding="utf-8")

    def test_la_riga_superata_identica_si_sostituisce(self):
        self.prepara_innesco(VECCHIA)
        testo = self.allinea_innesco()
        self.assertIn(NUOVA, testo)
        self.assertNotIn(VECCHIA, testo)
        self.assertEqual(testo.count("skill `gate-pacchetti`"), 1)

    def test_la_riga_riformulata_dal_progetto_resta_sua(self):
        propria = "- Riga mia sul gate: skill `gate-pacchetti`."
        self.prepara_innesco(propria)
        testo = self.allinea_innesco()
        self.assertIn(propria, testo)
        self.assertNotIn(NUOVA, testo)


if __name__ == "__main__":
    unittest.main()
