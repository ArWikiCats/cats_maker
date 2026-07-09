"""
Logging configuration with colored output.
"""

import logging
import os
import sys
from pathlib import Path

import colorlog


def prepare_log_file(log_file, project_logger):
    log_file = os.path.expandvars(str(log_file))
    log_file = Path(log_file).expanduser()

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        project_logger.error(f"Failed to create log directory: {e}")
        log_file = None
    return log_file


def setup_logging(
    level: str = "INFO",
    name: str = "cats_maker_new",
    log_file: str | None = None,
) -> None:
    """
    Configure logging for the entire project namespace only.
    """
    project_logger = logging.getLogger(name)

    if project_logger.handlers:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO) if isinstance(level, str) else level
    project_logger.setLevel(numeric_level)
    project_logger.propagate = False

    formatter = colorlog.ColoredFormatter(
        fmt="%(filename)s:%(lineno)s %(funcName)s() - %(log_color)s%(levelname)-s %(reset)s%(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    console_handler.setLevel(numeric_level)

    project_logger.addHandler(console_handler)

    # Optional file handler (no colors)
    if not log_file:
        log_file = os.getenv("CATS_MAKER_LOG_FILE", None)

    if log_file:
        log_file_path = prepare_log_file(log_file, project_logger)
        setup_file_handler(project_logger, log_file_path, numeric_level)

        # Separate error log file
        log_file2 = f"{str(log_file)}.err"
        setup_file_handler(project_logger, log_file2, logging.WARNING)


def setup_file_handler(project_logger, log_file, level) -> None:
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        project_logger.addHandler(file_handler)
    except Exception as e:
        project_logger.error(f"Failed to create log file: {e}")
