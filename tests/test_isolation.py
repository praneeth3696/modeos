"""
Guards that the test suite itself stays out of the user's home directory.
"""

import unittest
from pathlib import Path

from modeos.config import get_app_cache_file, get_log_file, get_state_file


class TestSandboxedPaths(unittest.TestCase):
    def test_runtime_files_are_outside_home(self):
        home = Path.home().resolve()
        for path in (get_log_file(), get_state_file(), get_app_cache_file()):
            with self.subTest(path=path):
                self.assertNotIn(home, path.resolve().parents)


if __name__ == "__main__":
    unittest.main()
