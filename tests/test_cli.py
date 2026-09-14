"""
End-to-end and integration tests for ModeOS CLI commands
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from modeos.cli import main

class TestCLI(unittest.TestCase):

    def run_cli(self, args_list):
        """Helper to run CLI with argument list and capture stdout."""
        import logging
        from modeos.logger import get_logger
        stdout_buf = StringIO()
        log = get_logger()
        handler = logging.StreamHandler(stdout_buf)
        log.addHandler(handler)
        try:
            with patch.object(sys, "argv", ["modeos"] + args_list), \
                 patch("sys.stdout", stdout_buf):
                try:
                    main()
                except SystemExit as e:
                    return e.code, stdout_buf.getvalue()
            return 0, stdout_buf.getvalue()
        finally:
            log.removeHandler(handler)

    def test_cli_list(self):
        code, out = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Available ModeOS Modes", out)
        self.assertIn("deep_work", out)
        self.assertIn("gaming", out)

    def test_cli_validate(self):
        code, out = self.run_cli(["validate", "deep_work"])
        self.assertEqual(code, 0)
        self.assertIn("Configuration syntax and structure are valid", out)

    def test_cli_doctor(self):
        code, out = self.run_cli(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("ModeOS System Diagnostics", out)
        self.assertIn("Audio Control Providers", out)

    @patch("modeos.process.get_running_user_processes")
    def test_cli_mode_dry_run_mock(self, mock_procs):
        proc = MagicMock(pid=100)
        proc.info = {'name': 'code'}
        proc.name.return_value = 'code'
        proc.nice.return_value = 0
        mock_procs.return_value = [proc]

        code, out = self.run_cli(["mode", "deep_work", "--dry-run", "--mock"])
        self.assertEqual(code, 0)
        self.assertIn("[DRY-RUN] [MODE] DEEP_WORK", out)
        self.assertIn("[✔] MODE DEEP_WORK APPLIED", out)

    @patch("modeos.process.get_running_user_processes")
    def test_cli_reset_dry_run_mock(self, mock_procs):
        proc = MagicMock(pid=100)
        proc.info = {'name': 'code'}
        proc.name.return_value = 'code'
        proc.nice.return_value = -5
        mock_procs.return_value = [proc]

        code, out = self.run_cli(["reset", "--dry-run", "--mock"])
        self.assertEqual(code, 0)
        self.assertIn("=== [DRY-RUN] Resetting System to Default State ===", out)

    def test_cli_fix_permissions(self):
        code, out = self.run_cli(["fix-permissions"])
        self.assertEqual(code, 0)
        self.assertIn("Permissions healthy", out)


class TestMockFlag(unittest.TestCase):
    """--mock must reach the engine whether it is given before or after the subcommand."""

    def parse_force_mock(self, args_list):
        seen = {}

        def record(*args, **kwargs):
            seen["force_mock"] = kwargs.get("force_mock")
            return True

        with patch("modeos.cli.apply_mode", side_effect=record), \
             patch("modeos.cli.reset_system", side_effect=record), \
             patch("modeos.cli.revert_system", side_effect=record), \
             patch.object(sys, "argv", ["modeos"] + args_list):
            main()
        return seen["force_mock"]

    def test_global_mock_flag_before_subcommand(self):
        self.assertTrue(self.parse_force_mock(["--mock", "mode", "gaming"]))
        self.assertTrue(self.parse_force_mock(["--mock", "reset"]))
        self.assertTrue(self.parse_force_mock(["--mock", "revert"]))

    def test_mock_flag_after_subcommand(self):
        self.assertTrue(self.parse_force_mock(["mode", "gaming", "--mock"]))
        self.assertTrue(self.parse_force_mock(["reset", "--mock"]))
        self.assertTrue(self.parse_force_mock(["revert", "--mock"]))

    def test_no_mock_flag(self):
        self.assertFalse(self.parse_force_mock(["mode", "gaming"]))
        self.assertFalse(self.parse_force_mock(["revert"]))

if __name__ == "__main__":
    unittest.main()
