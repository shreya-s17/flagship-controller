import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packaging = load('package_live_evidence')
restoration = load('restore_live_evidence')


class EvidencePackagingTests(unittest.TestCase):
    def test_explicit_archive_restores_original_bytes_and_is_metadata_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'results/run').mkdir(parents=True)
            source = root/'results/run/trace.jsonl'
            data = bytes(range(256))*500
            source.write_bytes(data)
            first = packaging.package(root, 'first', ['results/run/trace.jsonl'], 'fixture')
            source.chmod(0o600)
            second = packaging.package(root, 'second', ['results/run/trace.jsonl'], 'fixture')
            self.assertEqual(first['archive_sha256'], second['archive_sha256'])
            source.unlink()
            self.assertEqual(restoration.restore(root, 'first'), 1)
            self.assertEqual(source.read_bytes(), data)
            with self.assertRaisesRegex(ValueError, 'existing bundle'):
                packaging.package(root, 'first', ['results/run/trace.jsonl'], 'fixture')

    def test_secret_traversal_and_symlink_paths_are_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'results').mkdir()
            (root/'secret').write_text('fixture secret')
            (root/'results/link').symlink_to(root/'secret')
            for name in ('secret', 'results/../secret', str(root/'secret'), 'results/link', ''):
                with self.assertRaises(ValueError):
                    packaging.package(root, 'rejected', [name], 'fixture')
                self.assertFalse((root/'artifacts/rejected').exists())

    def test_empty_or_duplicate_manifest_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            for names in ([], ['results/a', 'results/a']):
                with self.assertRaisesRegex(ValueError, 'Empty or duplicate'):
                    packaging.package(temporary, 'rejected', names, 'fixture')
