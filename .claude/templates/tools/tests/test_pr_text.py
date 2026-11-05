"""Synthetic PR prose: reject encoding loss without blocking real punctuation."""

from pathlib import Path
import importlib.util
import json
import tempfile
import types
import unittest

P = Path(__file__).resolve().parent
if not (P / "gh-progetto.py").is_file():
    P = P.parent
spec = importlib.util.spec_from_file_location("gh_pr_text", P / "gh-progetto.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def suite(m):
    class Text(unittest.TestCase):
        def body(self, data):
            with tempfile.TemporaryDirectory(prefix="pr-text-") as folder:
                f = Path(folder) / "body.md"
                f.write_bytes(data)
                m.validate_pr_text(["pr", "edit", "1", "--body-file", str(f)])

        def test_utf8_accents_and_apostrophe(self):
            self.body(
                "Vulnerabilità: è già pronta l’analisi, perché serve qualità.\n".encode(
                    "utf8"
                )
            )

        def test_legitimate_question_and_url_and_code(self):
            self.body(
                "Compatibilità? Sì. https://example.test/?q=a?b e `object?.field`.\n".encode(
                    "utf8"
                )
            )

        def test_unicode_languages(self):
            self.body("日本語: テスト。 العربية: اختبار.\n".encode("utf8"))

        def test_ascii_prose(self):
            self.body(b"Fix parser and preserve input.\n")

        def test_invalid_utf8(self):
            with self.assertRaises(m.GateFailure):
                self.body(b"Invalid: \xe8.\n")

        def test_mojibake(self):
            with self.assertRaises(m.GateFailure):
                self.body("Qualit\u00c3\u00a0".encode("utf8"))

        def test_replacement_character(self):
            with self.assertRaises(m.GateFailure):
                self.body("Qualit\ufffd".encode("utf8"))

        def test_lossy_apostrophe(self):
            with self.assertRaises(m.GateFailure):
                self.body(b"Verifica l?accesso.")

        def test_lossy_verb(self):
            with self.assertRaises(m.GateFailure):
                self.body(b"Il registro ? globale.")

        def test_lossy_accent(self):
            with self.assertRaises(m.GateFailure):
                self.body(b"Corregge vulnerabilit? note.")

        def test_inline_body_disallowed(self):
            with self.assertRaises(m.GateFailure):
                m.validate_pr_text(["pr", "edit", "1", "--body", "text"])

        def test_stdin_body_disallowed(self):
            with self.assertRaises(m.GateFailure):
                m.validate_pr_text(["pr", "create", "--body-file", "-"])

        def test_damaged_title(self):
            with self.assertRaises(m.GateFailure):
                m.validate_pr_text(["pr", "edit", "1", "--title", "Qualit? del parser"])

        def test_damaged_body_blocks_before_credentials(self):
            with tempfile.TemporaryDirectory(prefix="pr-text-") as folder:
                f = Path(folder) / "body.md"
                f.write_bytes(b"Verifica l?accesso.")
                calls = []

                def runner(argv, **kwargs):
                    calls.append(argv)

                    class Result:
                        returncode = 0
                        stdout = b""

                    return Result()

                expected = {
                    "user.name": "Synthetic",
                    "user.email": "fixture@example.invalid",
                    "remote.origin.url": "git@git-synthetic:owner/repository.git",
                    "core.sshCommand": None,
                }
                original = m.git_value
                try:
                    m.git_value = lambda repo, key, runner: expected[key]
                    with self.assertRaises(m.GateFailure):
                        m.execute(
                            ".",
                            dict(
                                schema_version=1,
                                github_host="github.com",
                                github_login="synthetic",
                                ssh_alias="git-synthetic",
                                git_local=expected,
                            ),
                            "gh",
                            ["pr", "edit", "1", "--body-file", str(f)],
                            True,
                            runner=runner,
                        )
                    self.assertEqual(calls, [])
                finally:
                    m.git_value = original

    return unittest.defaultTestLoader.loadTestsFromTestCase(Text)


if __name__ == "__main__":
    import io

    stream = io.StringIO()
    good = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite(module))
    print(stream.getvalue())
    assert good.wasSuccessful()
    source = (P / "gh-progetto.py").read_text(encoding="utf8")
    start = source.index("def validate_pr_text(args):")
    end = source.index("def command_args(", start)
    mutated = types.ModuleType("mutated_pr_text")
    exec(
        compile(
            source[:start]
            + "def validate_pr_text(args):\n    pass\n\n\n"
            + source[end:],
            "<mutation>",
            "exec",
        ),
        mutated.__dict__,
    )
    bad = unittest.TextTestRunner(stream=io.StringIO()).run(suite(mutated))
    assert len(bad.failures) == 10 and not bad.errors
    print(
        json.dumps(
            dict(
                tests=good.testsRun,
                passed=True,
                negative_control_failures=len(bad.failures),
                synthetic_only=True,
            )
        )
    )
