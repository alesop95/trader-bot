import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("review", HERE / "stato-vulnerabilita.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
NOW = dt.datetime(2026, 10, 26, 12, tzinfo=dt.timezone.utc)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "package.json").write_text(
            '{"private":true,"dependencies":{"next":"16.1.6"}}'
        )
        self.private = self.root / "_notes/sicurezza"
        self.private.mkdir(parents=True)
        (self.private / "prova.json").write_text('{"scope":"synthetic"}')
        self.data = dict(
            schema_version=review.SCHEMA,
            verificato_il=NOW.isoformat(),
            commit="base",
            ramo="test",
            input_sha256=review.inputs(self.root),
            prove=[
                dict(
                    percorso="_notes/sicurezza/prova.json",
                    sha256=review.sha(self.private / "prova.json"),
                )
            ],
            copertura={s: dict(stato="verificato") for s in review.SCOPES},
            rilievi=[],
        )
        self.mock = patch.object(
            review, "git_state", return_value=("base", "test", False)
        )
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def save(self):
        (self.private / "ultimo-controllo.json").write_text(json.dumps(self.data))

    def result(self):
        self.save()
        return review.assess(self.root, now=NOW)

    def test_absent_report_is_unknown(self):
        self.assertEqual(review.assess(self.root, now=NOW)["stato"], "non_verificato")

    def test_missing_root_is_not_inspected(self):
        self.assertEqual(
            review.assess(self.root / "absent")["stato"], "non_verificabile"
        )

    def test_fresh_complete_review_has_limited_verdict(self):
        self.assertEqual(self.result()["stato"], "nessun_rilievo_nel_perimetro")

    def test_old_review_is_stale(self):
        self.data["verificato_il"] = (NOW - dt.timedelta(days=2)).isoformat()
        self.assertEqual(self.result()["stato"], "scaduto")

    def test_future_review_is_invalid(self):
        self.data["verificato_il"] = (NOW + dt.timedelta(hours=1)).isoformat()
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_timestamp_needs_timezone(self):
        self.data["verificato_il"] = "2026-10-26T12:00:00"
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_change_manifest_invalidates(self):
        (self.root / "package.json").write_text("{}")
        self.assertEqual(self.result()["stato"], "cambiato")

    def test_new_nested_manifest_invalidates(self):
        (self.root / "apps").mkdir()
        (self.root / "apps/package.json").write_text("{}")
        self.assertEqual(self.result()["stato"], "cambiato")

    def test_removed_manifest_invalidates(self):
        (self.root / "package.json").unlink()
        self.assertEqual(self.result()["stato"], "cambiato")

    def test_foreign_branch_invalidates(self):
        self.data["ramo"] = "other"
        self.assertEqual(self.result()["stato"], "cambiato")

    def test_foreign_commit_invalidates(self):
        self.data["commit"] = "old"
        self.assertEqual(self.result()["stato"], "cambiato")

    def test_missing_coverage_is_not_clean(self):
        self.data["copertura"].pop("host")
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_uninspected_runtime_is_incomplete(self):
        self.data["copertura"]["runtime"]["stato"] = "non_verificato"
        self.assertEqual(self.result()["stato"], "incompleto")

    def test_not_applicable_requires_reason(self):
        self.data["copertura"]["runtime"]["stato"] = "non_applicabile"
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_changed_evidence_invalidates(self):
        (self.private / "prova.json").write_text("changed")
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_missing_evidence_invalidates(self):
        self.data["prove"] = []
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_relative_escape_rejected(self):
        self.data["prove"][0]["percorso"] = "../outside"
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_unreadable_manifest_is_not_clean(self):
        with patch.object(review, "inputs", side_effect=PermissionError()):
            self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_unknown_schema_is_not_clean(self):
        self.data["schema_version"] = "other"
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_known_findings_remain_visible_when_stale(self):
        self.data["verificato_il"] = (NOW - dt.timedelta(days=2)).isoformat()
        self.data["rilievi"] = [
            dict(id="GHSA-example", stato="aperto", gravita="critica")
        ]
        result = self.result()
        self.assertEqual(result["stato"], "scaduto")
        self.assertEqual(review.exit_code(result), 1)
        self.assertEqual(len(result["rilievi_aperti"]), 1)

    def test_mitigated_is_still_open(self):
        self.data["rilievi"] = [dict(id="example", stato="mitigato", gravita="alta")]
        self.assertEqual(self.result()["stato"], "rilievi_aperti")

    def test_invalid_finding_is_not_zero(self):
        self.data["rilievi"] = [{}]
        self.assertEqual(self.result()["stato"], "non_verificabile")

    def test_source_changes_invalidate(self):
        with patch.object(review, "git_state", return_value=("base", "test", True)):
            self.assertEqual(self.result()["stato"], "cambiato")

    def test_report_permission_failure_is_explicit(self):
        with patch.object(Path, "is_file", side_effect=PermissionError()):
            self.assertEqual(
                review.assess(self.root, now=NOW)["stato"], "non_verificabile"
            )

    def test_hook_returns_zero_with_visible_problem(self):
        p = subprocess.run(
            [
                "python",
                str(HERE / "stato-vulnerabilita.py"),
                "--radice",
                str(self.root),
                "--hook",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.returncode, 0)
        self.assertIn("non_verificato", p.stdout)

    def test_real_git_scope(self):
        self.mock.stop()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("_notes/\n")
        subprocess.run(
            ["git", "-C", str(self.root), "add", "package.json", ".gitignore"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=",
                "commit",
                "--allow-empty",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        self.data["commit"], self.data["ramo"], _ = review.git_state(self.root)
        self.assertEqual(self.result()["stato"], "nessun_rilievo_nel_perimetro")


if __name__ == "__main__":
    unittest.main()
