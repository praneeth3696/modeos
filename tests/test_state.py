"""
Unit tests for ModeOS State Management & Rollback
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from modeos.state import capture_current_state, load_last_state, restore_state, save_state

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
