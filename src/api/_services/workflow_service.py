"""Workflow persistence API orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from persistence import (
    ALLOWED_SAVED_CONFIG_TYPES,
    SAVED_CONFIG_SCHEMA_VERSION,
    PersistenceUnavailableError,
    RecentAssetRecord,
    RecentCompareSetRecord,
    SavedResearchConfigRecord,
    WatchlistItemRecord,
    WorkflowPersistenceRepository,
)

from ..errors import APIError
from ..workflow_schemas import (
    DeleteWorkflowObjectResponseSchema,
    RecentAssetListResponseSchema,
    RecentAssetResponseSchema,
    RecentAssetTouchSchema,
    RecentCompareSetListResponseSchema,
    RecentCompareSetResponseSchema,
    RecentCompareTouchSchema,
    SavedMLConfigPayloadSchema,
    SavedResearchConfigListResponseSchema,
    SavedResearchConfigResponseSchema,
    SavedResearchConfigWriteSchema,
    SavedStrategyConfigPayloadSchema,
    WatchlistItemResponseSchema,
    WatchlistItemWriteSchema,
    WatchlistResponseSchema,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_saved_config_id(config_type: str) -> str:
    return f"{config_type}_cfg_{uuid4().hex[:12]}"


class WorkflowAPIService:
    def __init__(
        self,
        *,
        workflow_repository: WorkflowPersistenceRepository | None,
    ) -> None:
        self._workflow_repository = workflow_repository

    def _require_repository(self) -> WorkflowPersistenceRepository:
        if self._workflow_repository is None:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Workflow persistence requires a configured database.",
            )
        return self._workflow_repository

    @staticmethod
    def _validate_schema_version(version: int) -> None:
        if version != SAVED_CONFIG_SCHEMA_VERSION:
            raise APIError(
                status_code=400,
                code="saved_config_invalid",
                message=(
                    f"Unsupported saved config schema version '{version}'. "
                    f"Expected version {SAVED_CONFIG_SCHEMA_VERSION}."
                ),
            )

    @staticmethod
    def _sanitize_write_payload(request: SavedResearchConfigWriteSchema) -> dict[str, Any]:
        if request.config_type == "strategy":
            payload = SavedStrategyConfigPayloadSchema.model_validate(
                request.payload.model_dump()
            )
            return payload.model_dump(mode="json", exclude_none=True)
        payload = SavedMLConfigPayloadSchema.model_validate(request.payload.model_dump())
        return payload.model_dump(mode="json", exclude_none=True)

    def _payload_for_record(self, record: SavedResearchConfigRecord) -> dict[str, Any]:
        self._validate_schema_version(record.config_schema_version)
        try:
            if record.config_type == "strategy":
                return SavedStrategyConfigPayloadSchema.model_validate(
                    record.payload_json
                ).model_dump(mode="json", exclude_none=True)
            if record.config_type == "ml":
                return SavedMLConfigPayloadSchema.model_validate(
                    record.payload_json
                ).model_dump(mode="json", exclude_none=True)
        except Exception as exc:  # noqa: BLE001
            raise APIError(
                status_code=500,
                code="saved_config_corrupt",
                message=f"Saved config '{record.id}' could not be validated.",
            ) from exc
        raise APIError(
            status_code=500,
            code="saved_config_corrupt",
            message=f"Saved config '{record.id}' has unsupported type '{record.config_type}'.",
        )

    @staticmethod
    def _saved_config_response(record: SavedResearchConfigRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "config_type": record.config_type,
            "name": record.name,
            "description": record.description,
            "config_schema_version": record.config_schema_version,
            "instrument_symbol": record.instrument_symbol,
            "asset_class": record.asset_class,
            "interval": record.interval,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "last_used_at": record.last_used_at,
        }

    def list_saved_configs(
        self,
        *,
        config_type: str | None = None,
        limit: int = 100,
    ) -> SavedResearchConfigListResponseSchema:
        repository = self._require_repository()
        if config_type is not None and config_type not in ALLOWED_SAVED_CONFIG_TYPES:
            raise APIError(
                status_code=400,
                code="saved_config_invalid",
                message=f"Unsupported config_type '{config_type}'.",
            )
        try:
            records = repository.list_saved_configs(config_type=config_type, limit=limit)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to query saved workflow objects.",
            ) from exc
        return SavedResearchConfigListResponseSchema.model_validate(
            {"items": [self._saved_config_response(record) for record in records]}
        )

    def create_saved_config(
        self,
        request: SavedResearchConfigWriteSchema,
    ) -> SavedResearchConfigResponseSchema:
        repository = self._require_repository()
        self._validate_schema_version(request.config_schema_version)
        payload = self._sanitize_write_payload(request)
        now = _utcnow()
        record = SavedResearchConfigRecord(
            id=_new_saved_config_id(request.config_type),
            config_type=request.config_type,
            name=request.name.strip(),
            description=(request.description.strip() if request.description else None),
            config_schema_version=request.config_schema_version,
            payload_json=payload,
            instrument_symbol=str(payload["instrument"]["symbol"]),
            asset_class=str(payload["instrument"]["asset_class"]),
            interval=str(payload["interval"]),
            created_at=now,
            updated_at=now,
            last_used_at=None,
        )
        try:
            created = repository.create_saved_config(record)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to create saved workflow config.",
            ) from exc
        return SavedResearchConfigResponseSchema.model_validate(
            {
                **self._saved_config_response(created),
                "payload": self._payload_for_record(created),
            }
        )

    def get_saved_config(self, config_id: str) -> SavedResearchConfigResponseSchema:
        repository = self._require_repository()
        try:
            record = repository.mark_saved_config_used(config_id)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to load saved workflow config.",
            ) from exc
        if record is None:
            raise APIError(
                status_code=404,
                code="saved_config_not_found",
                message=f"Saved config '{config_id}' was not found.",
            )
        return SavedResearchConfigResponseSchema.model_validate(
            {
                **self._saved_config_response(record),
                "payload": self._payload_for_record(record),
            }
        )

    def update_saved_config(
        self,
        config_id: str,
        request: SavedResearchConfigWriteSchema,
    ) -> SavedResearchConfigResponseSchema:
        repository = self._require_repository()
        self._validate_schema_version(request.config_schema_version)
        try:
            existing = repository.get_saved_config(config_id)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to load saved workflow config.",
            ) from exc
        if existing is None:
            raise APIError(
                status_code=404,
                code="saved_config_not_found",
                message=f"Saved config '{config_id}' was not found.",
            )
        if existing.config_type != request.config_type:
            raise APIError(
                status_code=400,
                code="saved_config_invalid",
                message="config_type cannot change when updating a saved config.",
            )
        payload = self._sanitize_write_payload(request)
        updated_record = SavedResearchConfigRecord(
            id=existing.id,
            config_type=existing.config_type,
            name=request.name.strip(),
            description=(request.description.strip() if request.description else None),
            config_schema_version=request.config_schema_version,
            payload_json=payload,
            instrument_symbol=str(payload["instrument"]["symbol"]),
            asset_class=str(payload["instrument"]["asset_class"]),
            interval=str(payload["interval"]),
            created_at=existing.created_at,
            updated_at=_utcnow(),
            last_used_at=existing.last_used_at,
        )
        try:
            updated = repository.update_saved_config(updated_record)
        except KeyError as exc:
            raise APIError(
                status_code=404,
                code="saved_config_not_found",
                message=f"Saved config '{config_id}' was not found.",
            ) from exc
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to update saved workflow config.",
            ) from exc
        return SavedResearchConfigResponseSchema.model_validate(
            {
                **self._saved_config_response(updated),
                "payload": self._payload_for_record(updated),
            }
        )

    def delete_saved_config(self, config_id: str) -> DeleteWorkflowObjectResponseSchema:
        repository = self._require_repository()
        try:
            deleted = repository.delete_saved_config(config_id)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to delete saved workflow config.",
            ) from exc
        if not deleted:
            raise APIError(
                status_code=404,
                code="saved_config_not_found",
                message=f"Saved config '{config_id}' was not found.",
            )
        return DeleteWorkflowObjectResponseSchema(deleted=True)

    @staticmethod
    def _watchlist_item_response(record: WatchlistItemRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "symbol": record.symbol,
            "asset_class": record.asset_class,
            "source_context": record.source_context,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def list_watchlist(self, *, limit: int = 100) -> WatchlistResponseSchema:
        repository = self._require_repository()
        try:
            items = repository.list_watchlist_items(limit=limit)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to load watchlist.",
            ) from exc
        return WatchlistResponseSchema.model_validate(
            {"items": [self._watchlist_item_response(item) for item in items]}
        )

    def add_watchlist_item(
        self,
        request: WatchlistItemWriteSchema,
    ) -> WatchlistItemResponseSchema:
        repository = self._require_repository()
        try:
            item = repository.upsert_watchlist_item(
                symbol=request.symbol.strip().upper(),
                asset_class=request.asset_class.strip(),
                source_context=request.source_context,
            )
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to update watchlist.",
            ) from exc
        return WatchlistItemResponseSchema.model_validate(self._watchlist_item_response(item))

    def delete_watchlist_item(
        self,
        *,
        asset_class: str,
        symbol: str,
    ) -> DeleteWorkflowObjectResponseSchema:
        repository = self._require_repository()
        try:
            deleted = repository.delete_watchlist_item(
                asset_class=asset_class,
                symbol=symbol.upper(),
            )
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to update watchlist.",
            ) from exc
        if not deleted:
            raise APIError(
                status_code=404,
                code="watchlist_item_not_found",
                message=f"Watchlist item '{asset_class}:{symbol}' was not found.",
            )
        return DeleteWorkflowObjectResponseSchema(deleted=True)

    @staticmethod
    def _recent_asset_response(record: RecentAssetRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "symbol": record.symbol,
            "asset_class": record.asset_class,
            "source_context": record.source_context,
            "last_used_at": record.last_used_at,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def list_recent_assets(self, *, limit: int = 20) -> RecentAssetListResponseSchema:
        repository = self._require_repository()
        try:
            items = repository.list_recent_assets(limit=limit)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to load recent assets.",
            ) from exc
        return RecentAssetListResponseSchema.model_validate(
            {"items": [self._recent_asset_response(item) for item in items]}
        )

    def touch_recent_asset(
        self,
        request: RecentAssetTouchSchema,
    ) -> RecentAssetResponseSchema:
        repository = self._require_repository()
        try:
            item = repository.touch_recent_asset(
                symbol=request.symbol.strip().upper(),
                asset_class=request.asset_class.strip(),
                source_context=request.source_context,
            )
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to update recent assets.",
            ) from exc
        return RecentAssetResponseSchema.model_validate(self._recent_asset_response(item))

    @staticmethod
    def _recent_compare_response(record: RecentCompareSetRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "compare_mode": record.compare_mode,
            "run_ids": list(record.run_ids),
            "fingerprint": record.fingerprint,
            "last_used_at": record.last_used_at,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def list_recent_compares(
        self,
        *,
        limit: int = 20,
    ) -> RecentCompareSetListResponseSchema:
        repository = self._require_repository()
        try:
            items = repository.list_recent_compare_sets(limit=limit)
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to load recent compare selections.",
            ) from exc
        return RecentCompareSetListResponseSchema.model_validate(
            {"items": [self._recent_compare_response(item) for item in items]}
        )

    def touch_recent_compare(
        self,
        request: RecentCompareTouchSchema,
    ) -> RecentCompareSetResponseSchema:
        repository = self._require_repository()
        try:
            item = repository.touch_recent_compare_set(
                compare_mode=request.compare_mode,
                run_ids=[run_id.strip() for run_id in request.run_ids],
            )
        except PersistenceUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="workflow_persistence_unavailable",
                message="Failed to update recent compare selections.",
            ) from exc
        return RecentCompareSetResponseSchema.model_validate(
            self._recent_compare_response(item)
        )
