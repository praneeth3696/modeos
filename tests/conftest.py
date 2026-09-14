"""
Point XDG directories at a throwaway sandbox before any modeos module is
imported, so test runs never write logs, state or app caches into the
developer's real ~/.config, ~/.local/state or ~/.cache.
"""

import os
import tempfile

_sandbox = tempfile.mkdtemp(prefix="modeos-tests-")

for _var in ("XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
    os.environ[_var] = os.path.join(_sandbox, _var.lower())
