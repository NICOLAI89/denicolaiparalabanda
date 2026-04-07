from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2


def timestamped_name(prefix: str, suffix: str = ".png") -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"


def save_bgr_image(path: Path, image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)
