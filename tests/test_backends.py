"""
Unit tests for ModeOS hardware backends (Audio, Display, Night Light, Mock)
"""

import unittest
from unittest.mock import patch, MagicMock
from modeos.backends.audio import (
    AlsaBackend,
    MockAudioBackend,
    PulseAudioBackend,
    WirePlumberBackend,
    get_audio_backend
)
from modeos.backends.display import (
    BrightnessctlBackend,
    MockDisplayBackend,
    SysfsBacklightBackend,
    XrandrBackend,
    get_display_backend
)
from modeos.backends.nightlight import (
    GammastepBackend,
    GnomeNightLightBackend,
    KdeNightLightBackend,
    MockNightLightBackend,
    RedshiftBackend,
    get_nightlight_backend
)

class TestAudioBackends(unittest.TestCase):
    def test_mock_audio_backend(self):
        backend = MockAudioBackend(initial_volume=45)
        self.assertEqual(backend.get_volume(), 45)
        
        # Test dry-run
        self.assertTrue(backend.set_volume(80, dry_run=True))
        self.assertEqual(backend.get_volume(), 45) # unchanged

        # Test live set
        self.assertTrue(backend.set_volume(80, dry_run=False))
        self.assertEqual(backend.get_volume(), 80)

        # Test bounds clamping
        self.assertTrue(backend.set_volume(150, dry_run=False))
        self.assertEqual(backend.get_volume(), 100)
        self.assertTrue(backend.set_volume(-10, dry_run=False))
        self.assertEqual(backend.get_volume(), 0)

    @patch("subprocess.run")
    def test_wireplumber_get_volume(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: 0.65\n")
        wp = WirePlumberBackend()
        self.assertEqual(wp.get_volume(), 65)

    @patch("subprocess.run")
    def test_wireplumber_set_volume(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        wp = WirePlumberBackend()
        self.assertTrue(wp.set_volume(50, dry_run=False))
        mock_run.assert_called_with(
            ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.50"],
            capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_pulseaudio_get_volume(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: front-left: 32768 /  50% / -18.06 dB\n")
        pulse = PulseAudioBackend()
        self.assertEqual(pulse.get_volume(), 50)


class TestDisplayBackends(unittest.TestCase):
    def test_mock_display_backend(self):
        backend = MockDisplayBackend(initial_brightness=70)
        self.assertEqual(backend.get_brightness(), 70)

        # Test dry-run
        self.assertTrue(backend.set_brightness(30, dry_run=True))
        self.assertEqual(backend.get_brightness(), 70)

        # Test live set
        self.assertTrue(backend.set_brightness(30, dry_run=False))
        self.assertEqual(backend.get_brightness(), 30)

    @patch("subprocess.run")
    def test_brightnessctl_get(self, mock_run):
        # mock cur=500, max=1000
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="500\n"),
            MagicMock(returncode=0, stdout="1000\n")
        ]
        bctl = BrightnessctlBackend()
        self.assertEqual(bctl.get_brightness(), 50)


class TestNightLightBackends(unittest.TestCase):
    def test_mock_nightlight_backend(self):
        backend = MockNightLightBackend(initial_state=False)
        self.assertFalse(backend.get_night_light())

        # Test dry-run
        self.assertTrue(backend.set_night_light(True, dry_run=True))
        self.assertFalse(backend.get_night_light())

        # Test live set
        self.assertTrue(backend.set_night_light(True, dry_run=False))
        self.assertTrue(backend.get_night_light())

    @patch("subprocess.run")
    def test_gnome_nightlight(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
        gnome = GnomeNightLightBackend()
        self.assertTrue(gnome.get_night_light())


class TestFactoryFallbacks(unittest.TestCase):
    def test_force_mock_factories(self):
        audio = get_audio_backend(force_mock=True)
        self.assertIsInstance(audio, MockAudioBackend)

        display = get_display_backend(force_mock=True)
        self.assertIsInstance(display, MockDisplayBackend)

        nl = get_nightlight_backend(force_mock=True)
        self.assertIsInstance(nl, MockNightLightBackend)

if __name__ == "__main__":
    unittest.main()
