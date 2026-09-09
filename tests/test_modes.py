"""
Unit tests validating all bundled YAML mode definitions
"""

import unittest
from modeos.core import list_available_modes, load_mode_config

class TestBundledModes(unittest.TestCase):

    def test_all_bundled_modes_load(self):
        modes = list_available_modes()
        self.assertGreaterEqual(len(modes), 10, "Expected at least 10 bundled modes")

        for m in modes:
            # Check brightness
            if m.brightness is not None:
                self.assertGreaterEqual(m.brightness, 0)
                self.assertLessEqual(m.brightness, 100)

            # Check volume
            if m.volume is not None:
                self.assertGreaterEqual(m.volume, 0)
                self.assertLessEqual(m.volume, 100)

            # Check night light
            if m.night_light is not None:
                self.assertIsInstance(m.night_light, bool)

            # Check CPU limit
            if m.cpu_limit is not None:
                self.assertGreaterEqual(m.cpu_limit, 1)
                self.assertLessEqual(m.cpu_limit, 100)

            # Check nice values
            for app, nice in m.boost_apps.items():
                self.assertGreaterEqual(nice, -20)
                self.assertLessEqual(nice, 19)

            for app, nice in m.reduce_apps.items():
                self.assertGreaterEqual(nice, -20)
                self.assertLessEqual(nice, 19)

    def test_load_specific_modes(self):
        deep_work = load_mode_config("deep_work")
        self.assertIsNotNone(deep_work)
        self.assertEqual(deep_work.brightness, 80)
        self.assertEqual(deep_work.volume, 10)
        self.assertTrue(deep_work.night_light)
        self.assertTrue(deep_work.kill_all_except_allow)
        self.assertIn("code", deep_work.allow_apps)

        gaming = load_mode_config("gaming")
        self.assertIsNotNone(gaming)
        self.assertEqual(gaming.brightness, 100)
        self.assertEqual(gaming.volume, 80)
        self.assertFalse(gaming.night_light)

if __name__ == "__main__":
    unittest.main()
