#!/usr/bin/env python3
"""Check shell guards without downloading source or installing any dependencies."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
# macOS supplies Bash 3.2 here; do not accidentally test a Homebrew Bash instead.
BASH = '/bin/bash'


def generated_launcher():
    patch = (REPO / 'intel-monterey.patch').read_text()
    marker = 'diff --git a/Start-Intel-Monterey.command b/Start-Intel-Monterey.command\n'
    added = patch.split(marker, 1)[1].split('\ndiff --git ', 1)[0]
    return '\n'.join(line[1:] for line in added.splitlines()
                     if line.startswith('+') and not line.startswith('+++')) + '\n'


class ShellGuardTests(unittest.TestCase):
    def test_variable_names_are_delimited_before_non_ascii_text(self):
        scripts = {
            'Setup-Intel-Monterey.command': (REPO / 'Setup-Intel-Monterey.command').read_text(),
            'Start-Intel-Monterey.command': generated_launcher(),
        }
        # Old Bash/libc combinations can classify UTF-8 bytes as identifier characters.
        unsafe = re.compile(r'\$[A-Za-z_][A-Za-z_0-9]*[^\x00-\x7f]')
        for name, source in scripts.items():
            with self.subTest(script=name):
                self.assertIsNone(unsafe.search(source), name + ': brace variables before non-ASCII text')

    def test_generated_and_bootstrap_scripts_parse(self):
        for source in ((REPO / 'Setup-Intel-Monterey.command').read_text(), generated_launcher()):
            result = subprocess.run([BASH, '-n'], input=source, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_tool_message_in_c_and_available_utf8_locales(self):
        available = subprocess.check_output(['locale', '-a'], text=True).splitlines()
        locales = ['C'] + [name for name in available if 'utf8' in name.lower().replace('-', '')]
        with tempfile.TemporaryDirectory(prefix='monterey-shell-guard-') as directory:
            root = Path(directory)
            script = root / 'Setup-Intel-Monterey.command'
            shutil.copy2(REPO / script.name, script)
            (root / 'intel-monterey.patch').write_text('not reached\n')
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            (bin_dir / 'dirname').symlink_to(shutil.which('dirname'))
            uname = bin_dir / 'uname'
            uname.write_text('#!/bin/sh\nif [ "$1" = -s ]; then echo Darwin; else echo x86_64; fi\n')
            uname.chmod(0o755)
            # Only dirname and uname are available: curl must be the missing prerequisite.
            for locale_name in locales:
                with self.subTest(locale=locale_name):
                    env = {**os.environ, 'PATH': str(bin_dir), 'LC_ALL': locale_name, 'LANG': locale_name}
                    result = subprocess.run([BASH, str(script)], env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn('缺少 curl，请先按使用说明准备工具。', result.stderr)
                    self.assertNotIn('unbound variable', result.stderr)
                    self.assertFalse(list(root.glob('.harness-setup.*')))
                    self.assertFalse((root / 'deepseek-harness-intel').exists())


unittest.main()
