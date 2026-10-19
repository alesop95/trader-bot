"""Tests exercise real encoded bytes, images and the incremental ingest loop."""
import contextlib
import gzip
import importlib.util
import io
import json
import lzma
from pathlib import Path
import tempfile
import unittest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


storage = load('storage_under_test', 'cache-storage.py')
ingest = load('ingest_under_test', 'doc-ingest.py')


class StorageTests(unittest.TestCase):
    def test_auto_shrinks_and_roundtrips_real_unicode_bytes(self):
        data = ('# Titolo\r\nUna frase con à, è, ♯ e una tabella.\n' * 2000).encode()
        suffix, encoded = storage.smallest_bytes(data)
        self.assertIn(suffix, {'.gz', '.bz2', '.xz'})
        self.assertLess(len(encoded), len(data) // 10)
        import bz2
        decoded = {'.gz': gzip.decompress, '.bz2': bz2.decompress, '.xz': lzma.decompress}[suffix](encoded)
        self.assertEqual(decoded, data)

    def test_auto_retains_incompressible_small_data(self):
        self.assertEqual(storage.smallest_bytes(b'abc'), ('', b'abc'))

    def test_write_migrates_plain_then_reads_and_restores_plain(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'mirror.md'
            text = 'à\r\ncontesto, armonia e dati\n' * 1000
            base.write_bytes(text.encode())
            destination = storage.write_cached_text(base, text)
            self.assertFalse(base.exists())
            with storage.open_text(destination) as stream:
                self.assertEqual(stream.read(), text)
            self.assertEqual(storage.cache_variant(base), destination)
            self.assertEqual(storage.write_cached_text(base, text, 'plain'), base)
            self.assertFalse(destination.exists())
            self.assertEqual(base.read_bytes(), text.encode())

    def test_corruption_is_not_treated_as_missing_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'mirror.md'
            corrupt = Path(str(base) + '.gz')
            corrupt.write_bytes(b'not gzip')
            with self.assertRaises((OSError, EOFError)):
                with storage.open_text(corrupt) as stream:
                    stream.read()
            self.assertEqual(corrupt.read_bytes(), b'not gzip')

    def test_conflicting_variants_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'mirror.md'
            base.write_text('one', encoding='utf-8')
            Path(str(base) + '.gz').write_bytes(gzip.compress(b'two'))
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                storage.cache_variant(base)

    def test_cache_boundary_rejects_root_outside_and_unlabelled_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for candidate in [root, root.parent / 'outside-cache', root / 'sources']:
                with self.assertRaises(ValueError):
                    storage.confined_cache(root, candidate)
            self.assertEqual(storage.confined_cache(root, root / 'cache')[1], root / 'cache')

    def test_text_selector_excludes_originals_backups_images_and_databases(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'cache'
            for name in ['active.json', 'small.json', 'source.pdf', 'page.png', 'corpus.sqlite',
                         'backup/old.json', 'originals/source.txt']:
                path = cache / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'x' * (2 if name == 'small.json' else 8192))
            self.assertEqual([p.name for p in storage.text_cache_files(cache)], ['active.json'])

    def test_incremental_ingest_migrates_without_converter_or_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            document = source / 'input.html'
            original = b'<html>source remains byte identical</html>'
            document.write_bytes(original)
            cache = Path(directory) / 'cache'
            converter = ingest.convert_file
            calls = []
            def convert(*args):
                calls.append(args)
                return '# Un titolo\n' + 'Contenuto ripetuto con accenti è.\n' * 2000, None
            ingest.convert_file = convert
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertTrue(ingest.run(source, cache, 'markitdown', False, False))
                    self.assertTrue(ingest.run(source, cache, 'markitdown', False, False, compression='auto'))
                    self.assertTrue(ingest.run(source, cache, 'markitdown', False, False, compression='auto'))
                self.assertEqual(len(calls), 1)
                mirror = storage.cache_variant(cache / 'input.html.md')
                self.assertNotEqual(mirror.suffix, '.md')
                self.assertIn(mirror.name, (cache / '_INDEX.md').read_text(encoding='utf-8'))
                self.assertEqual(json.loads((cache / '.manifest.json').read_text())['input.html'], storage.sha256(document))
                self.assertEqual(document.read_bytes(), original)
            finally:
                ingest.convert_file = converter

    def test_source_cannot_be_cache_root(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ingest.run(directory, directory, 'markitdown', False, False)

    def test_generated_raster_keeps_transparency_and_hidden_rgb(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            image = Image.new('RGBA', (60, 40), (23, 67, 120, 0))
            image.putpixel((4, 4), (0, 0, 0, 255))
            path, report = storage.save_smallest_lossless(image, Path(directory) / 'sheet')
            with Image.open(path) as actual:
                self.assertEqual(actual.convert('RGBA').tobytes(), image.tobytes())
            self.assertTrue(report['pixels_unchanged'])

    def test_color_is_not_silently_made_grayscale(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            image = Image.new('RGB', (50, 50), (255, 10, 20))
            path, _ = storage.save_smallest_lossless(image, Path(directory) / 'color')
            with Image.open(path) as actual:
                self.assertEqual(actual.convert('RGB').tobytes(), image.tobytes())

    def test_source_metadata_is_rejected_by_generated_raster_writer(self):
        from PIL import Image
        image = Image.new('RGB', (20, 20))
        image.info['icc_profile'] = b'preserve source metadata'
        with self.assertRaises(ValueError):
            storage.save_smallest_lossless(image, Path('unused'))

    def test_existing_png_preserves_name_pixels_and_dpi(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'page.png'
            image = Image.new('RGB', (300, 300), 'white')
            for number in range(50):
                image.putpixel((number, number), (0, 0, 0))
            image.save(path, dpi=(150, 150))
            before = path.stat().st_size
            with Image.open(path) as old:
                pixels, metadata = old.convert('RGBA').tobytes(), old.info
            result = storage.optimize_png(path, True)
            self.assertIsNotNone(result)
            self.assertLess(path.stat().st_size, before)
            with Image.open(path) as actual:
                self.assertEqual(actual.convert('RGBA').tobytes(), pixels)
                self.assertEqual(actual.info, metadata)

    def test_existing_color_png_is_left_byte_identical(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'color.png'
            Image.new('RGB', (50, 50), (255, 10, 20)).save(path)
            digest = storage.sha256(path)
            self.assertIsNone(storage.optimize_png(path, True))
            self.assertEqual(storage.sha256(path), digest)

    def test_external_report_is_rejected_before_ntfs_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaisesRegex(ValueError, 'Report'):
                storage.compact_ntfs(root, root / 'cache', root.parent / 'report.json', True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
