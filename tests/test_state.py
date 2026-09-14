"""
Unit tests for ModeOS State Management & Rollback
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from modeos.state import capture_current_state, load_last_state, restore_state, save_state

@patch.dict("os.environ", {"MODEOS_MOCK": "0"})
class TestForceMockPropagation(unittest.TestCase):
    """A --mock session must never read or write real hardware during save/revert."""

    @patch("modeos.state.get_nightlight_backend")
    @patch("modeos.state.get_display_backend")
    @patch("modeos.state.get_audio_backend")
    def test_capture_uses_mock_backends_when_forced(self, audio, display, nightlight):
        capture_current_state(force_mock=True)
        audio.assert_called_once_with(force_mock=True)
        display.assert_called_once_with(force_mock=True)
        nightlight.assert_called_once_with(force_mock=True)

    @patch("modeos.state.load_last_state", return_value={"volume": 40})
    @patch("modeos.state.get_nightlight_backend")
    @patch("modeos.state.get_display_backend")
    @patch("modeos.state.get_audio_backend")
    def test_restore_uses_mock_backends_when_forced(self, audio, display, nightlight, _load):
        restore_state(dry_run=True, force_mock=True)
        audio.assert_called_once_with(force_mock=True)
        display.assert_called_once_with(force_mock=True)
        nightlight.assert_called_once_with(force_mock=True)

    @patch("modeos.core.restore_state", return_value=True)
    def test_revert_system_passes_force_mock(self, restore):
        from modeos.core import revert_system
        revert_system(dry_run=False, force_mock=True)
        restore.assert_called_once_with(dry_run=False, force_mock=True)

    @patch("modeos.core.adjust_priorities", return_value={1234: 0})
    @patch("modeos.core.kill_all_except", return_value=[])
    @patch("modeos.core.kill_apps", return_value=[])
    @patch("modeos.core.get_installed_apps", return_value={})
    @patch("modeos.core.save_state", return_value=True)
    def test_apply_mode_saves_state_with_force_mock(self, save, *_process_mocks):
        from modeos.core import apply_mode
        self.assertTrue(apply_mode("deep_work", dry_run=False, force_mock=True))
        self.assertGreaterEqual(save.call_count, 1)
        for call in save.call_args_list:
            self.assertTrue(call.kwargs.get("force_mock"))


class TestStateManager(unittest.TestCase):

    @patch("modeos.state.get_state_file")
    def test_save_and_load_state(self, mock_get_file):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "test_state.json"
            mock_get_file.return_value = state_file

            success = save_state(
                active_mode="gaming",
                modified_priorities={123: 0},
                terminated_apps=[(456, "slack")]
            )
            self.assertTrue(success)
            self.assertTrue(state_file.exists())

            loaded = load_last_state()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.get("active_mode"), "gaming")
            self.assertEqual(loaded.get("modified_priorities"), {"123": 0})
            self.assertEqual(loaded.get("terminated_apps"), [[456, "slack"]])

    @patch("modeos.state.load_last_state")
    @patch("modeos.state.get_audio_backend")
    @patch("modeos.state.get_display_backend")
    @patch("modeos.state.get_nightlight_backend")
    @patch("modeos.state.restore_process_priorities")
    def test_restore_state(self, mock_priors, mock_nl, mock_disp, mock_audio, mock_load):
        mock_load.return_value = {
            "volume": 75,
            "brightness": 50,
            "night_light": True,
            "modified_priorities": {"100": 0}
        }
        success = restore_state(dry_run=True)
        self.assertTrue(success)
        mock_audio().set_volume.assert_called_with(75, dry_run=True)
        mock_disp().set_brightness.assert_called_with(50, dry_run=True)
        mock_nl().set_night_light.assert_called_with(True, dry_run=True)
        mock_priors.assert_called_with({"100": 0}, dry_run=True)

if __name__ == "__main__":
    unittest.main()
