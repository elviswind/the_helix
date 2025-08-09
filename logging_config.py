import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def ensure_logs_directory(logs_dir: str) -> None:
    """Ensure the logs directory exists."""
    Path(logs_dir).mkdir(parents=True, exist_ok=True)


def get_file_logger(
    logger_name: str,
    log_file_path: str,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Create or retrieve a configured logger that writes to a rotating file.

    - logger_name: Unique name for the logger
    - log_file_path: Absolute or project-relative path to the log file
    - level: Logging level (default INFO)
    - max_bytes: Max file size before rotation (default 10MB)
    - backup_count: Number of rotated backups to keep (default 5)
    """
    logs_dir = os.path.dirname(os.path.abspath(log_file_path)) or "."
    ensure_logs_directory(logs_dir)

    logger = logging.getLogger(logger_name)
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Also add a concise stderr handler at WARNING+ for visibility when run manually
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Do not propagate to root to avoid duplicate logs
    logger.propagate = False

    return logger


