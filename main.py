#!/usr/bin/env python3
"""
ModeOS - Adaptive OS Mode Manager
Root executable wrapper delegating to the modeos package.
"""

import sys
import os

# Ensure local package is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modeos.cli import main

if __name__ == "__main__":
    main()
