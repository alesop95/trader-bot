"""Observable checks for the reusable README synchronizer."""

from __future__ import annotations

import importlib.util
import shutil
import unittest
import uuid
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "sync-readme.py"
SPEC = importlib.util.spec_from_file_location("sync_readme", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SyncReadmeTests(unittest.TestCase):
    def setUp(self) -> None:
        tests_dir = Path(__file__).resolve().parent
        self.root = (tests_dir / f"fixture_{uuid.uuid4().hex}").resolve()
        self.assertEqual(self.root.parent, tests_dir)
        self.root.mkdir()
        self.addCleanup(self.cleanup_fixture)

    def cleanup_fixture(self) -> None:
        self.assertEqual(self.root.resolve().parent, Path(__file__).resolve().parent)
        shutil.rmtree(self.root)

    def write_readme(self, text: str) -> None:
        (self.root / "README.md").write_text(text, encoding="utf-8")

    def test_write_is_idempotent_and_preserves_encoding_shape(self) -> None:
        (self.root / "guide.md").write_text("Guida", encoding="utf-8")
        source = "# Progetto\r\n\r\nDescrizione.\r\n\r\n## Uso\r\n\r\n[Guida](guide.md)\r\n\r\n## Uso\r\n\r\nAltro.\r\n"
        (self.root / "README.md").write_bytes(b"\xef\xbb\xbf" + source.encode("utf-8"))
        self.assertEqual(MODULE.sync(self.root, True, False), 0)
        first = (self.root / "README.md").read_bytes()
        self.assertTrue(first.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(first.count(b"\n"), first.count(b"\r\n"))
        self.assertIn(b"#uso-1", first)
        self.assertEqual(MODULE.sync(self.root, False, False), 0)
        self.assertEqual(MODULE.sync(self.root, True, False), 0)
        self.assertEqual((self.root / "README.md").read_bytes(), first)

    def test_bundle_counts_catalog_rows_with_suffixes(self) -> None:
        package_dir = self.root / ".claude" / "templates" / "alpha"
        package_dir.mkdir(parents=True)
        (package_dir / "README.md").write_text("# Alpha\n\n<!-- readme-summary: descrizione curata -->\n", encoding="utf-8")
        catalog = package_dir.parent / "PACKAGES.md"
        catalog.write_text("### Settore\n\n| `alpha` | Dato |\n| `beta` (MCP) | Esterno |\n", encoding="utf-8")
        self.write_readme("# Progetto\n\n## Indice dei README dei pacchetti\n\n<!-- sync-readme:packages:start -->\n<!-- sync-readme:packages:end -->\n\n## Uso\n")
        self.assertEqual(MODULE.sync(self.root, True, True), 0)
        result = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("**1 pacchetto a cartella** su **2 voci**", result)
        self.assertIn("descrizione curata", result)
        self.assertEqual(MODULE.sync(self.root, False, True), 0)
        catalog.write_text(catalog.read_text(encoding="utf-8") + "| `gamma` | Esterno |\n", encoding="utf-8")
        self.assertEqual(MODULE.sync(self.root, False, True), 1)

    def test_broken_link_does_not_write(self) -> None:
        self.write_readme("# Progetto\n\n## Uso\n\n[Guida](manca.md)\n")
        before = (self.root / "README.md").read_bytes()
        self.assertEqual(MODULE.sync(self.root, True, False), 2)
        self.assertEqual((self.root / "README.md").read_bytes(), before)

    def test_new_package_without_summary_is_rejected(self) -> None:
        package_dir = self.root / ".claude" / "templates" / "alpha"
        package_dir.mkdir(parents=True)
        (package_dir / "README.md").write_text("# Alpha\n", encoding="utf-8")
        (package_dir.parent / "PACKAGES.md").write_text("### Settore\n\n| `alpha` | Dato |\n", encoding="utf-8")
        self.write_readme("# Progetto\n\n## Indice dei README dei pacchetti\n\n<!-- sync-readme:packages:start -->\n<!-- sync-readme:packages:end -->\n")
        self.assertEqual(MODULE.sync(self.root, True, True), 2)


if __name__ == "__main__":
    unittest.main()
