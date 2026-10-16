from pathlib import Path
import importlib.util
import shutil
import tempfile
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('restore_evidence',root/'scripts/restore_live_evidence.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class EvidenceBundleTests(unittest.TestCase):
    def test_clean_restore_and_changed_file_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            shutil.copytree(root/'artifacts/live-evidence-2026-10-16',target/'artifacts/live-evidence-2026-10-16')
            self.assertEqual(module.restore(target),len(__import__("json").loads((root/"artifacts/live-evidence-2026-10-16/manifest.json").read_text())["files"]))
            self.assertEqual(module.restore(target),len(__import__("json").loads((root/"artifacts/live-evidence-2026-10-16/manifest.json").read_text())["files"]))
            path=target/'results/paired-pilot-001/predictions.jsonl'
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError,'overwrite'):module.restore(target)
            self.assertEqual(path.read_text(),'changed')

    def test_tampered_part_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            folder=target/'artifacts/live-evidence-2026-10-16'
            shutil.copytree(root/'artifacts/live-evidence-2026-10-16',folder)
            part=next(folder.glob('*.part*'));part.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'integrity'):module.restore(target)
            self.assertFalse((target/'results').exists())
