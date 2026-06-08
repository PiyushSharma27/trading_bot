"""
logging_config.py
-----------------
Sets up TWO loggers:
  1. File logger  → writes everything (DEBUG and above) to trading_bot.log
  2. Console logger → shows INFO and above in the terminal

Think of a "logger" like a diary. Every time something important happens
(an API call, an error, a success), we write it in the diary.
"""

import logging
import os

LOG_FILE = "trading_bot.log"


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """
    Create and return a configured logger.

    Parameters
    ----------
    name : str
        The name tag that appears in every log line so you know where
        the message came from.

    Returns
    -------
    logging.Logger
        A ready-to-use logger object.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if setup_logger is called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # capture everything at DEBUG level and above

    # ── File handler ──────────────────────────────────────────────────────────
    # Writes logs to a file so you have a permanent record
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # ── Console handler ───────────────────────────────────────────────────────
    # Prints INFO/WARNING/ERROR to the terminal so you see what's happening live
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_fmt = logging.Formatter(
        fmt="%(levelname)-8s │ %(message)s",
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
