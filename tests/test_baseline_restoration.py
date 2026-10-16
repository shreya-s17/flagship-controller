import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('materialize',ROOT/'scripts/materialize_baseline_runtime.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SourceRestorationTests(unittest.TestCase):
    def test_all_archived_versions_load_as_isolated_runtime_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name,count in [('baseline-dev-001',6),('baseline-dev-002',7),('baseline-dev-003',8)]:
                source=ROOT/'results'/name;destination=Path(temporary)/name
                self.assertEqual(module.materialize(source,destination),count)
                plan=json.loads((source/'manifest.json').read_text())
                for archived,expected in plan['source_hashes'].items():
                    self.assertEqual(hashlib.sha256((destination/'flagship_controller'/module.NAMES[archived]).read_bytes()).hexdigest(),expected)
                result=subprocess.run(['python3','-m','flagship_controller.baseline_development','freeze','--help'],cwd=destination,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                with self.assertRaisesRegex(ValueError,'existing'):module.materialize(source,destination)

    def test_tampered_source_rejected_before_destination_creation(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'source';source.mkdir()
            original=ROOT/'results/baseline-dev-001'
            shutil.copy(original/'manifest.json',source/'manifest.json')
            for filename in json.loads((source/'manifest.json').read_text())['source_hashes']:
                shutil.copy(original/filename,source/filename)
            (source/'adapter-source.py').write_text('tampered')
            destination=Path(temporary)/'out'
            with self.assertRaisesRegex(ValueError,'mismatch'):module.materialize(source,destination)
            self.assertFalse(destination.exists())
