"""Runtime settings API orchestration."""

from __future__ import annotations

from config import AppSettings, build_safe_system_settings_snapshot

from ..settings_schemas import SystemSettingsResponseSchema


class SettingsAPIService:
    def __init__(self, *, app_settings: AppSettings) -> None:
        self._app_settings = app_settings

    def get_system_settings(self) -> SystemSettingsResponseSchema:
        snapshot = build_safe_system_settings_snapshot(self._app_settings)
        return SystemSettingsResponseSchema.model_validate(snapshot.to_dict())

