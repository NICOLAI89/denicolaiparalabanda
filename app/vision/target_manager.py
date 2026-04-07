from __future__ import annotations

from pathlib import Path

import cv2

from app.utils.image_utils import timestamped_name
from app.utils.paths import TARGETS_DIR


class TargetManager:
    def save_target(self, image, profile_name: str, macro_index: int) -> Path:
        filename = timestamped_name(f"{profile_name}_macro{macro_index}")
        target_path = TARGETS_DIR / filename
        cv2.imwrite(str(target_path), image)
        return target_path

    def load_target(self, path: str):
        p = Path(path)
        if not p.exists():
            return None
        return cv2.imread(str(p), cv2.IMREAD_COLOR)
