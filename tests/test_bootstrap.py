#!/usr/bin/env python3
"""Test bootstrap safety with real archive/patch operations and mocked Mac tools."""
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
REVISION = '639ed015397290b3745d163aafe02ffee4aa3f84'
SHA256 = 'bbc09e888e1df3aa37be049abdb7720951e76442d21e5432365d87a465d628f1'
if len(sys.argv) != 2:
    raise SystemExit('Usage: python3 tests/test_bootstrap.py /path/to/pinned-source.tar.gz')
ARCHIVE = Path(sys.argv.pop()).resolve()
if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != SHA256:
    raise SystemExit('Input archive does not match the pinned official SHA256')


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='intel-monterey-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'adapter with spaces'
        self.repo.mkdir()
        for name in ('Setup-Intel-Monterey.command', 'intel-monterey.patch', '使用说明.txt', 'VERIFICATION.txt'):
            shutil.copy2(REPO / name, self.repo / name)
        # Exercise a real cloned-adapter layout: patch application must not use its parent .git.
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'calls'
        programs = {
            'uname': 'if [ "$1" = -s ]; then echo Darwin; else echo x86_64; fi',
            'sw_vers': 'echo 12.6.6',
            'node': 'exit 0',
            'xcode-select': 'echo /Library/Developer/CommandLineTools',
            'pnpm': 'if [ "$1" = --version ]; then echo 11.7.0; else echo "$*" >> "$MOCK_LOG"; fi',
            'curl': 'for last; do :; done; cp ' + shlex.quote(str(ARCHIVE)) + ' "$last"',
        }
        for name, body in programs.items():
            self.write_tool(name, body)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'], 'MOCK_LOG': str(self.log)}
        self.env.pop('GIT_DIR', None)
        self.env.pop('GIT_WORK_TREE', None)

    def write_tool(self, name, body):
        tool = self.bin / name
        tool.write_text('#!/bin/sh\n' + body + '\n')
        tool.chmod(0o755)

    def run_setup(self):
        return subprocess.run(['bash', str(self.repo / 'Setup-Intel-Monterey.command')],
                              env=self.env, capture_output=True, text=True)

    def test_prepares_patched_source_inside_git_clone(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.repo / 'deepseek-harness-intel'
        self.assertEqual((source / 'SOURCE_REVISION').read_text().strip(), REVISION)
        self.assertIn('43.7.7', (source / 'apps/desktop/package.json').read_text())
        self.assertTrue((source / 'Start-Intel-Monterey.command').exists())
        self.assertEqual(self.log.read_text().splitlines(), ['install --frozen-lockfile', 'run build', 'run start:desktop'])
        self.assertFalse(list(self.repo.glob('.harness-setup.*')))

    def test_failed_build_never_starts_desktop(self):
        self.write_tool('pnpm', 'if [ "$1" = --version ]; then echo 11.7.0; else echo "$*" >> "$MOCK_LOG"; [ "$*" != "run build" ] || exit 42; fi')
        result = self.run_setup()
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), ['install --frozen-lockfile', 'run build'])
        self.assertTrue((self.repo / 'deepseek-harness-intel/SOURCE_REVISION').exists())

    def test_existing_directory_is_not_overwritten(self):
        source = self.repo / 'deepseek-harness-intel'
        source.mkdir()
        marker = source / 'keep.txt'
        marker.write_text('keep')
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('不会覆盖', result.stderr)
        self.assertEqual(marker.read_text(), 'keep')
        self.assertFalse(self.log.exists())

    def test_corrupt_archive_is_not_extracted_or_launched(self):
        self.write_tool('curl', 'for last; do :; done; echo corrupt > "$last"')
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / 'deepseek-harness-intel').exists())
        self.assertFalse(list(self.repo.glob('.harness-setup.*')))
        self.assertFalse(self.log.exists())

    def test_unsupported_platform_stops_before_download(self):
        self.write_tool('uname', 'echo Linux')
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Intel Mac', result.stderr)
        self.assertFalse(list(self.repo.glob('.harness-setup.*')))
        self.assertFalse(self.log.exists())


unittest.main()
