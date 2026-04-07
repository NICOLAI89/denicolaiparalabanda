from __future__ import annotations

import json
from pathlib import Path

from app.core.models import AppProfile
from app.utils.logger import LOGGER
from app.utils.paths import PROFILES_DIR, ensure_data_dirs


class ProfileManager:
    def __init__(self) -> None:
        ensure_data_dirs()

    def profile_path(self, name: str) -> Path:
        safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")) or "default"
        return PROFILES_DIR / f"{safe}.json"

    def list_profiles(self) -> list[str]:
        return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))

    def save(self, profile: AppProfile, new_name: str | None = None) -> Path:
        if new_name:
            profile.name = new_name
        path = self.profile_path(profile.name)
        path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
        LOGGER.info("Profile saved: %s", path)
        return path

    def load(self, name: str) -> AppProfile:
        path = self.profile_path(name)
        if not path.exists():
            raise FileNotFoundError(name)
        data = json.loads(path.read_text(encoding="utf-8"))
        profile = AppProfile.from_dict(data)
        LOGGER.info("Profile loaded: %s", path)
        return profile

    def delete(self, name: str) -> None:
        path = self.profile_path(name)
        if path.exists():
            path.unlink()
            LOGGER.info("Profile deleted: %s", path)

    def ensure_default(self) -> AppProfile:
        if not self.list_profiles():
            profile = AppProfile()
            self.save(profile)
            return profile
        return self.load(self.list_profiles()[0])
