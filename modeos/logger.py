"""
ModeOS Logging Module
Provides rotating file logs and ANSI-formatted console messages.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from modeos.config import get_log_file

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
DIM = "\033[2m"

class ColoredConsoleFormatter(logging.Formatter):
    def format(self, record):
        msg = record.getMessage()
        # If output is not a TTY, strip or avoid color codes
        if not sys.stdout.isatty():
            return msg

        if record.levelno >= logging.ERROR:
            return f"{RED}{BOLD}[ERROR]{RESET} {RED}{msg}{RESET}"
        elif record.levelno >= logging.WARNING:
            return f"{YELLOW}{BOLD}[WARN]{RESET} {YELLOW}{msg}{RESET}"
        elif "[✔]" in msg or "[SUCCESS]" in msg or "[OK]" in msg:
            return f"{GREEN}{msg}{RESET}"
        elif "[DRY-RUN]" in msg:
            return f"{CYAN}{BOLD}{msg}{RESET}"
        return msg

_logger = None

def setup_logger(verbose: bool = False) -> logging.Logger:
    global _logger
    if _logger is not None:
        if verbose:
            _logger.setLevel(logging.DEBUG)
        return _logger

    logger = logging.getLogger("ModeOS")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    # Clear existing handlers if any
    logger.handlers.clear()

    # Rotating File Handler (max 5MB, keep 3 backups)
    log_file = get_log_file()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError):
        pass  # If log file is unwriteable, console output still works

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)

    _logger = logger
    return _logger

def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger
