"""Fixture sintetiche: account API del progetto indipendente dall account globale."""

from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parent
if not (P / "gh-progetto.py").is_file():
    P = P.parent
spec = importlib.util.spec_from_file_location("gh_project", P / "gh-progetto.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = dict(
    schema_version=1,
    github_host="github.com",
    github_login="account-alpha",
    ssh_alias="git-alpha",
    git_local={
        "user.name": "Synthetic Alpha",
        "user.email": "alpha@example.test",
        "remote.origin.url": "git@git-alpha:owner-alpha/repository.git",
        "core.sshCommand": None,
    },
)


class Fake:
    def __init__(self, profile=None):
        self.profile = copy.deepcopy(profile or BASE)
        self.calls = []
        self.active = "account-beta"
        self.actual_identity = None
        self.fail_token = False
        self.echo_token = False

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        out = b""
        code = 0
        if argv[0] == "git":
            value = self.profile["git_local"].get(argv[-1])
            out = (value or "").encode()
            code = 1 if value is None else 0
        elif argv[1:3] == ["auth", "token"]:
            assert "GH_TOKEN" not in kw["env"]
            assert "--user" in argv
            code = 1 if self.fail_token else 0
            out = b"SYNTHETIC_ALPHA_TOKEN"
        elif argv[1:4] == ["api", "user", "--hostname"]:
            assert (
                kw["env"]["GH_TOKEN"] == "SYNTHETIC_ALPHA_TOKEN"
                and kw["env"]["GH_HOST"] == "github.com"
            )
            out = (self.actual_identity or BASE["github_login"]).encode()
        else:
            out = b"SYNTHETIC_ALPHA_TOKEN" if self.echo_token else b'{"ok":true}'
        return subprocess.CompletedProcess(argv, code, out, b"")


def suite(m):
    class Routes(unittest.TestCase):
        def test_machine_registry_recognizes_declared_tuple(self):
            registry = dict(
                schema_version=1,
                profiles=[
                    dict(
                        git_user_name=BASE["git_local"]["user.name"],
                        git_user_email=BASE["git_local"]["user.email"],
                        ssh_alias=BASE["ssh_alias"],
                        core_ssh_command=None,
                        github_host="github.com",
                        github_login=BASE["github_login"],
                    )
                ],
            )
            self.assertEqual(m.from_registry(".", registry, Fake()), BASE)

        def test_machine_registry_does_not_guess_other_profiles(self):
            with self.assertRaises(m.GateFailure):
                m.from_registry(".", dict(schema_version=1, profiles=[]), Fake())

        def test_machine_registry_rejects_ambiguous_tuple(self):
            item = dict(
                git_user_name=BASE["git_local"]["user.name"],
                git_user_email=BASE["git_local"]["user.email"],
                ssh_alias=BASE["ssh_alias"],
                core_ssh_command=None,
                github_host="github.com",
                github_login=BASE["github_login"],
            )
            with self.assertRaises(m.GateFailure):
                m.from_registry(
                    ".", dict(schema_version=1, profiles=[item, item]), Fake()
                )

        def test_profile_wins_over_active_global(self):
            fake = Fake()
            before = dict(os.environ)
            with patch.dict(
                os.environ,
                {
                    "GH_TOKEN": "OTHER_SYNTHETIC_TOKEN",
                    "GH_HOST": "other.invalid",
                    "GH_REPO": "other/repository",
                    "GH_DEBUG": "api",
                },
            ):
                report, result = m.execute(
                    ".",
                    BASE,
                    "gh",
                    ["api", "repos/owner-alpha/repository/pulls/1"],
                    runner=fake,
                )
            self.assertTrue(report["credentials_bound_per_process"])
            self.assertEqual(fake.active, "account-beta")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(dict(os.environ), before)
            self.assertNotIn(["auth", "switch"], [a[1:3] for a, k in fake.calls])

        def test_wrong_git_identity_blocks_before_credentials(self):
            fake = Fake()
            fake.profile["git_local"]["user.email"] = "other@example.test"
            with self.assertRaises(m.GateFailure):
                m.execute(".", BASE, "gh", runner=fake)
            self.assertTrue(all(a[0] == "git" for a, k in fake.calls))

        def test_wrong_ssh_alias(self):
            profile = copy.deepcopy(BASE)
            profile["ssh_alias"] = "git-other"
            with self.assertRaises(m.GateFailure):
                m.execute(".", profile, "gh", runner=Fake())

        def test_wrong_remote(self):
            fake = Fake()
            fake.profile["git_local"]["remote.origin.url"] = (
                "git@git-alpha:owner-alpha/other.git"
            )
            with self.assertRaises(m.GateFailure):
                m.execute(".", BASE, "gh", runner=fake)

        def test_missing_profile_fields(self):
            with self.assertRaises(m.GateFailure):
                m.execute(".", {}, "gh", runner=Fake())

        def test_wrong_api_identity(self):
            fake = Fake()
            fake.actual_identity = "account-beta"
            with self.assertRaises(m.GateFailure):
                m.execute(
                    ".",
                    BASE,
                    "gh",
                    ["api", "repos/owner-alpha/repository/pulls/1"],
                    runner=fake,
                )
            self.assertFalse(
                any(
                    a[1:3] == ["api", "repos/owner-alpha/repository/pulls/1"]
                    for a, k in fake.calls
                    if a[0] == "gh"
                )
            )

        def test_unavailable_credentials_do_not_echo_token(self):
            fake = Fake()
            fake.fail_token = True
            with self.assertRaises(m.GateFailure) as error:
                m.execute(".", BASE, "gh", runner=fake)
            self.assertNotIn("TOKEN", str(error.exception))

        def test_repository_is_explicit_for_pr(self):
            fake = Fake()
            m.execute(".", BASE, "gh", ["pr", "view", "1"], runner=fake)
            self.assertEqual(
                fake.calls[-1][0][-2:], ["--repo", "owner-alpha/repository"]
            )

        def test_wrong_repository_is_blocked(self):
            with self.assertRaises(m.GateFailure):
                m.execute(
                    ".",
                    BASE,
                    "gh",
                    ["pr", "view", "1", "--repo", "other/repository"],
                    runner=Fake(),
                )

        def test_header_override_is_blocked(self):
            with self.assertRaises(m.GateFailure):
                m.execute(
                    ".",
                    BASE,
                    "gh",
                    [
                        "api",
                        "repos/owner-alpha/repository",
                        "-H",
                        "Authorization: synthetic",
                    ],
                    runner=Fake(),
                )

        def test_write_needs_manual_flag(self):
            with self.assertRaises(m.GateFailure):
                m.execute(
                    ".",
                    BASE,
                    "gh",
                    [
                        "api",
                        "repos/owner-alpha/repository/issues",
                        "-f",
                        "title=synthetic",
                    ],
                    runner=Fake(),
                )

        def test_merge_stays_blocked(self):
            with self.assertRaises(m.GateFailure):
                m.execute(".", BASE, "gh", ["pr", "merge", "1"], True, runner=Fake())

        def test_auth_token_cannot_be_forwarded(self):
            with self.assertRaises(m.GateFailure):
                m.execute(".", BASE, "gh", ["auth", "token"], True, runner=Fake())

        def test_token_is_redacted_if_command_echoes_it(self):
            fake = Fake()
            fake.echo_token = True
            report, result = m.execute(
                ".", BASE, "gh", ["pr", "view", "1"], runner=fake
            )
            self.assertEqual(result.stdout, b"<redacted>")

        def test_api_write_with_explicit_manual_flag(self):
            fake = Fake()
            report, result = m.execute(
                ".",
                BASE,
                "gh",
                ["api", "repos/owner-alpha/repository/issues", "-f", "title=synthetic"],
                True,
                runner=fake,
            )
            self.assertEqual(result.returncode, 0)

    return unittest.defaultTestLoader.loadTestsFromTestCase(Routes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    a = parser.parse_args()
    output = (
        Path(a.output_dir)
        if a.output_dir
        else Path(tempfile.mkdtemp(prefix="project-gh-tests-"))
    )
    output.mkdir(parents=True, exist_ok=True)
    source = (P / "gh-progetto.py").read_bytes()
    fingerprint = hashlib.sha256(source).hexdigest()
    stream = io.StringIO()
    good = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite(module))
    (output / "test.stdout.log").write_text(stream.getvalue(), encoding="utf8")
    assert good.wasSuccessful()
    line = '        if actual != value:\n            raise GateFailure("git_profile_mismatch")\n'
    text = source.decode()
    assert text.count(line) == 1
    namespace = {"__name__": "mutated_identity"}
    exec(compile(text.replace(line, "        pass\n", 1), "<mutation-in-memory>", "exec"), namespace)
    import types

    mutated = types.SimpleNamespace(**namespace)
    stream = io.StringIO()
    bad = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite(mutated))
    (output / "mutation.stdout.log").write_text(stream.getvalue(), encoding="utf8")
    assert len(bad.failures) == 2 and not bad.errors
    assert (
        hashlib.sha256((P / "gh-progetto.py").read_bytes()).hexdigest() == fingerprint
    )
    result = dict(
        tests=good.testsRun,
        passed=True,
        mutation_expected_failures=2,
        source_sha256=fingerprint,
        source_unchanged=True,
        fixtures_only=True,
        real_authentication_changed=False,
    )
    (output / "esito-test.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(result))
