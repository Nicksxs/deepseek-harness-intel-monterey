#!/usr/bin/env python3
"""Exercise the narrow existing-source repair without installing or building anything."""
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
REVISION = '639ed015397290b3745d163aafe02ffee4aa3f84'


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='monterey-repair-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'SOURCE_REVISION').write_text(REVISION + '\n')
        self.launcher = self.root / 'Start-Intel-Monterey.command'
        self.original = '#!/bin/bash\n# Preserve my comment\npnpm run dev:desktop\n'
        self.launcher.write_text(self.original)
        self.launcher.chmod(0o755)

    def run_repair(self):
        return subprocess.run(['node', str(REPO / 'repair-existing-source.mjs'), str(self.root)], capture_output=True, text=True)

    def test_repairs_once_preserves_edits_mode_and_backup(self):
        result = self.run_repair()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.launcher.read_text()
        self.assertIn('# Preserve my comment', content)
        self.assertTrue(content.endswith('pnpm run build\npnpm run start:desktop\n'))
        self.assertEqual(self.launcher.stat().st_mode & 0o777, 0o755)
        backup = Path(str(self.launcher) + '.before-build-order-fix')
        self.assertEqual(backup.read_text(), self.original)
        self.assertEqual(self.run_repair().returncode, 0)
        self.assertEqual(self.launcher.read_text(), content)
        self.assertEqual(backup.read_text(), self.original)

    def test_unknown_source_revision_is_unchanged(self):
        (self.root / 'SOURCE_REVISION').write_text('different')
        self.assertNotEqual(self.run_repair().returncode, 0)
        self.assertEqual(self.launcher.read_text(), self.original)

    def test_unrecognized_launcher_is_unchanged(self):
        self.launcher.write_text('custom launcher\n')
        self.assertNotEqual(self.run_repair().returncode, 0)
        self.assertEqual(self.launcher.read_text(), 'custom launcher\n')

    def test_existing_backup_is_not_overwritten(self):
        backup = Path(str(self.launcher) + '.before-build-order-fix')
        backup.write_text('keep backup')
        self.assertNotEqual(self.run_repair().returncode, 0)
        self.assertEqual(backup.read_text(), 'keep backup')
        self.assertEqual(self.launcher.read_text(), self.original)


unittest.main()
