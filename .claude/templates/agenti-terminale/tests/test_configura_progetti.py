import importlib.util
import json
import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('agent_projects', Path(__file__).resolve().parents[1] / 'tools/configura-progetti.py')
projects = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projects)


class ProjectSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'approved-project'
        (self.project / '.codex').mkdir(parents=True)
        (self.project / '.claude').mkdir()
        (self.project / '.codex/config.toml').write_text('[mcp_servers.fixture]\ncommand="fixture"\n')
        (self.project / '.mcp.json').write_text(json.dumps({'mcpServers': {'fixture': {'command': 'fixture'}}}))
        (self.project / '.claude/settings.local.json').write_text(json.dumps({'enabledMcpjsonServers': ['fixture']}))
        self.registry = self.root / 'registry.json'
        self.registry.write_text(json.dumps({'schema': 'agent-projects-0.1', 'projects': [
            {'path': str(self.project), 'mcp_servers': ['fixture']}]}))
        for agent in ['codex', 'claude']:
            for n in [4, 5]:
                account = self.root / f'.{agent}-account{n}'
                account.mkdir()
                (account / 'auth.json').write_text('fixture credentials must stay untouched')
                if agent == 'codex':
                    (account / 'config.toml').write_bytes(b'approval_policy = "on-request"\r\nsandbox_mode = "workspace-write"\r\n')

    def test_new_account_gets_project_trust_and_keeps_auth_and_policies(self):
        config = self.root / '.codex-account4/config.toml'
        before = config.read_bytes()
        auth = self.root / '.codex-account4/auth.json'
        secret = auth.read_bytes()
        changes, _ = projects.prepare(self.registry, 'codex', [4], self.root)
        self.assertEqual(config.read_bytes(), before)  # verify is read-only
        projects.apply(changes)
        self.assertTrue(config.read_bytes().startswith(before))
        parsed = tomllib.loads(config.read_text())
        self.assertIn(str(self.project), parsed.get('projects', {}))
        self.assertEqual(parsed['projects'][str(self.project)]['trust_level'], 'trusted')
        self.assertEqual(parsed['approval_policy'], 'on-request')
        self.assertEqual(auth.read_bytes(), secret)
        self.assertEqual(projects.prepare(self.registry, 'codex', [4], self.root)[0], [])
        self.assertNotIn('fixture credentials', config.read_text())

    def test_conflicting_trust_in_second_account_blocks_all_writes(self):
        config = self.root / '.codex-account5/config.toml'
        config.write_text('[projects.' + json.dumps(str(self.project)) + ']\ntrust_level="untrusted"\n')
        first = self.root / '.codex-account4/config.toml'
        before = first.read_bytes()
        with self.assertRaises(ValueError):
            projects.prepare(self.registry, 'codex', [4, 5], self.root)
        self.assertEqual(first.read_bytes(), before)

    def test_claude_uses_project_definition_without_account_mcp_copy(self):
        self.assertEqual(projects.prepare(self.registry, 'claude', [4], self.root)[0], [])
        self.assertFalse((self.root / '.claude-account4/mcp.json').exists())
        (self.project / '.mcp.json').unlink()
        with self.assertRaises(OSError):
            projects.prepare(self.registry, 'claude', [4], self.root)

    def test_missing_or_disabled_project_server_refused(self):
        for text in ['[mcp_servers.other]\ncommand="fixture"', '[mcp_servers.fixture]\nenabled=false']:
            (self.project / '.codex/config.toml').write_text(text)
            with self.assertRaises(ValueError):
                projects.prepare(self.registry, 'codex', [4], self.root)

    @unittest.skipUnless(os.name == 'nt', 'Installatore Windows')
    def test_actual_installer_applies_default_machine_registry_to_new_account(self):
        local_data = self.root / 'local-app-data'
        registry = local_data / 'agenti-terminale/progetti.json'
        registry.parent.mkdir(parents=True)
        registry.write_bytes(self.registry.read_bytes())
        environment = dict(os.environ, USERPROFILE=str(self.root), LOCALAPPDATA=str(local_data))
        script = Path(__file__).resolve().parents[1] / 'tools/Installa-Codex.ps1'
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                 '-File', str(script), '-Account', '6'], env=environment,
                                capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
        root = self.root / '.codex-account6'
        config = tomllib.loads((root / 'config.toml').read_text(encoding='utf-8-sig'))
        self.assertIn(str(self.project), config.get('projects', {}))
        self.assertEqual(config['projects'][str(self.project)]['trust_level'], 'trusted')
        self.assertFalse((root / 'auth.json').exists())


if __name__ == '__main__':
    unittest.main()
