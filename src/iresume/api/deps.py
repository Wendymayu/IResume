from functools import lru_cache

from iresume.config import Settings, settings
from iresume.storage.history_repository import HistoryRepository
from iresume.storage.profile_repository import ProfileRepository


@lru_cache
def get_settings() -> Settings:
    return settings


def get_profile_repo() -> ProfileRepository:
    return ProfileRepository(settings.profile_dir)


@lru_cache
def get_history_repo() -> HistoryRepository:
    return HistoryRepository(settings.history_db_path)
