from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import LOGS_DIR, ensure_data_dirs


def setup_logger() -> logging.Logger:
    ensure_data_dirs()
    logger = logging.getLogger("macro_tool_v2")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    file_handler = RotatingFileHandler(LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


LOGGER = setup_logger()
