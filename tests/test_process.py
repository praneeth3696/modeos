"""
Unit tests for ModeOS Process Manager (safety, whitelist, dry-run, nice tracking)
"""

import unittest
from unittest.mock import patch, MagicMock
from modeos.process import (
    SYSTEM_EXCEPTIONS,
    adjust_priorities,
    is_system_protected,
    kill_all_except,
    kill_apps,
    matches_app,
    reset_all_priorities,
    restore_process_priorities,
    terminate_process_list
)

class TestProcessManager(unittest.TestCase):

    def test_system_whitelist_protection(self):
        proc = MagicMock()
        proc.info = {"name": "systemd"}
        proc.name.return_value = "systemd"
        self.assertTrue(is_system_protected(proc))

        proc.info = {"name": "wireplumber"}
        proc.name.return_value = "wireplumber"
        self.assertTrue(is_system_protected(proc))

        proc.info = {"name": "bash"}
        proc.name.return_value = "bash"
        self.assertTrue(is_system_protected(proc))

        proc.info = {"name": "discord"}
        proc.name.return_value = "discord"
        self.assertFalse(is_system_protected(proc))

    def test_matches_app(self):
        proc = MagicMock()
        proc.info = {"name": "gnome-terminal-server", "cmdline": ["/usr/bin/gnome-terminal-server"]}
        proc.name.return_value = "gnome-terminal-server"
        proc.exe.return_value = "/usr/bin/gnome-terminal-server"

        self.assertTrue(matches_app(proc, "gnome-terminal-server"))
        self.assertTrue(matches_app(proc, "gnome-terminal")) # 15-char comm prefix match

    def test_terminate_process_list_dry_run(self):
        proc1 = MagicMock(pid=101)
        proc1.info = {"name": "steam"}
        proc1.name.return_value = "steam"

        killed = terminate_process_list([proc1], dry_run=True)
        self.assertEqual(len(killed), 1)
        self.assertEqual(killed[0], (101, "steam"))
        # Ensure terminate() and kill() were NOT called
        proc1.terminate.assert_not_called()
        proc1.kill.assert_not_called()

    @patch("modeos.process.get_running_user_processes")
    def test_kill_apps_dry_run(self, mock_get_procs):
        proc1 = MagicMock(pid=201)
        proc1.info = {"name": "discord"}
        proc1.name.return_value = "discord"
        mock_get_procs.return_value = [proc1]

        installed = {"discord": "discord"}
        killed = kill_apps(["discord"], installed, dry_run=True)
        self.assertEqual(len(killed), 1)
        self.assertEqual(killed[0], (201, "discord"))
        proc1.terminate.assert_not_called()

    @patch("modeos.process.get_running_user_processes")
    def test_adjust_priorities_dry_run_and_tracking(self, mock_get_procs):
        proc1 = MagicMock(pid=301)
        proc1.info = {"name": "code"}
        proc1.name.return_value = "code"
        proc1.nice.return_value = 0
        mock_get_procs.return_value = [proc1]

        installed = {"code": "code"}
        modified = adjust_priorities({"code": -10}, installed, dry_run=True)

        # In dry run, it recorded PID 301's original nice (0)
        self.assertEqual(modified, {301: 0})
        # nice(target) was not called with arguments to change it
        proc1.nice.assert_called_with() # called with 0 args to read original_nice

    @patch("psutil.Process")
    @patch("psutil.pid_exists")
    def test_restore_process_priorities(self, mock_exists, mock_proc_cls):
        mock_exists.return_value = True
        proc_instance = MagicMock()
        proc_instance.nice.return_value = -10
        mock_proc_cls.return_value = proc_instance

        # Test dry-run restore
        count = restore_process_priorities({401: 0}, dry_run=True)
        self.assertEqual(count, 1)
        # did not mutate nice
        proc_instance.nice.assert_called_with()

        # Test live restore
        count = restore_process_priorities({401: 0}, dry_run=False)
        self.assertEqual(count, 1)
        proc_instance.nice.assert_called_with(0)

if __name__ == "__main__":
    unittest.main()
