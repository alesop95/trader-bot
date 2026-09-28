#!/usr/bin/env python3
"""Prove isolate del comando chiudi per Bash, senza operazioni Git reali."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]


class ChiudiLinuxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chiudi-linux-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo con spazi"
        (self.repo / "tools").mkdir(parents=True)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.gitlog = self.base / "git.log"
        fake_git = self.bin / "git"
        fake_git.write_text("""#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$GIT_LOG"
case "$1" in
  rev-parse)
    if [ "$2" = --show-toplevel ]; then printf '%s\\n' "$FAKE_ROOT"; else printf '%s\\n' abcdef1234567890; fi ;;
  symbolic-ref) echo main ;;
  remote) [ "${NO_ORIGIN:-0}" = 1 ] || echo origin ;;
  status) [ "${DIRTY:-0}" = 1 ] && echo ' M file.txt' ;;
  config) [ "$3" = user.name ] && echo '<NOME>' || echo '<EMAIL>' ;;
  ls-remote) printf '%s\\trefs/heads/main\\n' "${REMOTE_HASH:-abcdef1234567890}" ;;
  push|add|commit|--no-pager) exit 0 ;;
esac
""")
        fake_git.chmod(0o755)
        pgrep = self.bin / "pgrep"
        pgrep.write_text("#!/usr/bin/env bash\nexit 1\n")
        pgrep.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", GIT_LOG=str(self.gitlog), FAKE_ROOT=str(self.repo))

    def run_cmd(self, *args, cwd=None, env=None, input_text=None):
        return subprocess.run(args, cwd=cwd or self.repo, env=env or self.env, input=input_text, text=True, capture_output=True)

    def test_installer_is_idempotent_and_function_uses_current_repo(self):
        profile = self.base / "profile"
        profile.write_text("# impostazioni esistenti\n")
        installer = TOOLS / "installa-chiudi.sh"
        for _ in range(2):
            result = self.run_cmd("bash", str(installer), "--shell", "bash", "--profilo", str(profile))
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(profile.read_text().count("# >>> chiudi"), 1)
        self.assertEqual(self.run_cmd("bash", str(installer), "--shell", "bash", "--profilo", str(profile), "--verifica").returncode, 0)
        capture = self.base / "args.txt"
        launcher = self.repo / "tools" / "chiudi-sessione.sh"
        launcher.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" > \"$CAPTURE\"\n")
        env = dict(self.env, CAPTURE=str(capture))
        result = self.run_cmd("bash", "-c", 'source "$1"; chiudi --solo-controlli', "bash", str(profile), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture.read_text().strip(), f"--radice {self.repo} --solo-controlli")

    def test_push_checks_origin_branch_before_registering(self):
        verifier = self.repo / "tools" / "verifica-ripresa.py"
        verifier.write_text("import os\nfrom pathlib import Path\nPath(os.environ['VERIFY_MARKER']).write_text('ok')\n")
        marker = self.base / "verified"
        env = dict(self.env, VERIFY_MARKER=str(marker))
        script = TOOLS / "chiudi-sessione.sh"
        result = self.run_cmd("bash", str(script), "--radice", str(self.repo), "--no-wipe", env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("push -u origin HEAD:refs/heads/main", self.gitlog.read_text())
        self.assertIn("ls-remote --exit-code origin refs/heads/main", self.gitlog.read_text())
        self.assertTrue(marker.exists())
        marker.unlink()
        result = self.run_cmd("bash", str(script), "--radice", str(self.repo), "--no-wipe", env=dict(env, REMOTE_HASH="different"))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(marker.exists())

    def test_wipe_accepts_account_path_with_spaces(self):
        home = self.base / "home"
        hooks = home / ".claude-account 2" / "hooks"
        hooks.mkdir(parents=True)
        marker = self.base / "wiped"
        wipe = hooks / "session-end-wipe.sh"
        wipe.write_text("#!/usr/bin/env bash\nprintf '%s' \"$0\" > \"$WIPE_MARKER\"\n")
        result = self.run_cmd("bash", str(TOOLS / "chiudi-sessione.sh"), "--radice", str(self.repo), "--account", "account 2", env=dict(self.env, HOME=str(home), NO_ORIGIN="1", WIPE_MARKER=str(marker)))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(marker.read_text(), str(wipe))

    def test_commit_requires_confirmation_and_uses_prepared_message(self):
        notes = self.repo / "_notes"
        notes.mkdir()
        message = notes / "COMMIT-MSG.txt"
        message.write_text("Aggiornato chiudi Linux\n")
        env = dict(self.env, DIRTY="1", NO_ORIGIN="1")
        script = TOOLS / "chiudi-sessione.sh"
        refused = self.run_cmd("bash", str(script), "--radice", str(self.repo), "--no-wipe", env=env)
        self.assertEqual(refused.returncode, 1)
        self.assertTrue(message.exists())
        self.assertNotIn("add -A", self.gitlog.read_text())
        accepted = self.run_cmd("bash", str(script), "--radice", str(self.repo), "--no-wipe", env=env, input_text="s\n")
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        self.assertIn("add -A", self.gitlog.read_text())
        self.assertIn("commit -m Aggiornato chiudi Linux", self.gitlog.read_text())
        self.assertFalse(message.exists())

    def test_missing_option_value_fails_cleanly(self):
        result = self.run_cmd("bash", str(TOOLS / "chiudi-sessione.sh"), "--account")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Valore mancante", result.stderr)


if __name__ == "__main__":
    unittest.main()
