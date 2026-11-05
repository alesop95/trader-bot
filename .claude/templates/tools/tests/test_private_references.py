"""Riferimenti personali: avvisi senza introdurre un blocco sui casi ambigui."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "anonymization/tools/Test-Anonymization.py"
spec = importlib.util.spec_from_file_location("anonymization_tested", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def test_personal_paths_and_declared_cloud_are_nonblocking_warnings(tmp_path):
    source = tmp_path / "prova.md"
    source.write_text("C:/Users/" + "persona/Studio\nServizioPersonale\nC:/Users/<utente>/Studio\n", encoding="utf-8")
    config = {key: [] for key in ("reti_documentali_ammesse", "ip_ammessi", "prefissi_reali", "mac_ammessi_prefissi", "email_ammesse", "nomi_propri")}
    config["servizi_cloud_personali"] = ["ServizioPersonale"]
    findings, _ = scanner.analizza(config, [(str(source), "tracciato")])
    category = "RIFERIMENTO PERSONALE da valutare"
    assert len(findings[category]) == 2
    assert category not in scanner.BLOCCANTI
    assert all("oscur" not in item[2] or "<" in item[2] for item in findings[category])


def test_short_name_does_not_match_inside_real_code_words(tmp_path):
    # La variante reale contieneva un nome corto dentro removing/remoto.
    # La fixture deriva il token dal testo, senza usare dati di una persona.
    name = "removing"[1:6].upper()
    source = tmp_path / "prova.md"
    source.write_text("removing_exclusion()\nremoto\nremovable\n" + name + "\n(" + name.lower() + "),\nX" + name + "\n" + name + "123\n", encoding="utf-8")
    config = {key: [] for key in ("reti_documentali_ammesse", "ip_ammessi", "prefissi_reali", "mac_ammessi_prefissi", "email_ammesse", "nomi_propri")}
    config["nomi_propri"] = [name]
    findings, _ = scanner.analizza(config, [(str(source), "tracciato")])
    assert [item[1] for item in findings["NOME PROPRIO"]] == [4, 5]


def test_full_name_context_and_literal_secret_keep_their_contract(tmp_path):
    name = "Persona Sintetica"
    source = tmp_path / "prova.md"
    source.write_text("(" + name.upper() + ").\nX" + name + "Suffix\n" + name + " nella ragione sociale ammessa\naccount_marker_sintetico\n", encoding="utf-8")
    config = {key: [] for key in ("reti_documentali_ammesse", "ip_ammessi", "prefissi_reali", "mac_ammessi_prefissi", "email_ammesse", "nomi_propri")}
    config["nomi_propri"] = [name, ""]
    config["nomi_ammessi_in_contesto"] = ["ragione sociale ammessa"]
    config["segreti_letterali"] = ["marker_sintetico"]
    findings, _ = scanner.analizza(config, [(str(source), "tracciato")])
    assert [item[1] for item in findings["NOME PROPRIO"]] == [1]
    assert [item[1] for item in findings["SEGRETO LETTERALE"]] == [4]
