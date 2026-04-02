"""Database-backed persistence for workflow continuity objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .errors import PersistenceUnavailableError
from .models import (
    RecentAssetModel,
    RecentCompareSetModel,
    SavedResearchConfigModel,
    WatchlistItemModel,
)

SAVED_CONFIG_SCHEMA_VERSION = 1
ALLOWED_SAVED_CONFIG_TYPES = frozenset({"strategy", "ml"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def compute_recent_compare_fingerprint(compare_mode: str, run_ids: list[str]) -> str:
    canonical = json.dumps(
        {
            "compare_mode": compare_mode,
            "run_ids": list(run_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SavedResearchConfigRecord:
    id: str
    config_type: str
    name: str
    description: str | None
    config_schema_version: int
    payload_json: dict[str, Any]
    instrument_symbol: str
    asset_class: str
    interval: str
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None


@dataclass(frozen=True)
class WatchlistItemRecord:
    id: str
    symbol: str
    asset_class: str
    source_context: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RecentAssetRecord:
    id: str
    symbol: str
    asset_class: str
    source_context: str | None
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RecentCompareSetRecord:
    id: str
    fingerprint: str
    compare_mode: str
    run_ids: tuple[str, ...]
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime


class WorkflowPersistenceRepository(Protocol):
    def list_saved_configs(
        self,
        *,
        config_type: str | None = None,
        limit: int = 100,
    ) -> tuple[SavedResearchConfigRecord, ...]: ...

    def create_saved_config(
        self,
        record: SavedResearchConfigRecord,
    ) -> SavedResearchConfigRecord: ...

    def get_saved_config(self, config_id: str) -> SavedResearchConfigRecord | None: ...

    def update_saved_config(
        self,
        record: SavedResearchConfigRecord,
    ) -> SavedResearchConfigRecord: ...

    def delete_saved_config(self, config_id: str) -> bool: ...

    def mark_saved_config_used(
        self,
        config_id: str,
    ) -> SavedResearchConfigRecord | None: ...

    def list_watchlist_items(self, *, limit: int = 100) -> tuple[WatchlistItemRecord, ...]: ...

    def upsert_watchlist_item(
        self,
        *,
        symbol: str,
        asset_class: str,
        source_context: str | None = None,
    ) -> WatchlistItemRecord: ...

    def delete_watchlist_item(self, *, asset_class: str, symbol: str) -> bool: ...

    def list_recent_assets(self, *, limit: int = 20) -> tuple[RecentAssetRecord, ...]: ...

    def touch_recent_asset(
        self,
        *,
        symbol: str,
        asset_class: str,
        source_context: str | None = None,
    ) -> RecentAssetRecord: ...

    def list_recent_compare_sets(
        self,
        *,
        limit: int = 20,
    ) -> tuple[RecentCompareSetRecord, ...]: ...

    def touch_recent_compare_set(
        self,
        *,
        compare_mode: str,
        run_ids: list[str],
    ) -> RecentCompareSetRecord: ...


def _saved_config_model_to_record(model: SavedResearchConfigModel) -> SavedResearchConfigRecord:
    return SavedResearchConfigRecord(
        id=model.id,
        config_type=model.config_type,
        name=model.name,
        description=model.description,
        config_schema_version=model.config_schema_version,
        payload_json=dict(model.payload_json),
        instrument_symbol=model.instrument_symbol,
        asset_class=model.asset_class,
        interval=model.interval,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_used_at=model.last_used_at,
    )


def _saved_config_record_to_model(record: SavedResearchConfigRecord) -> SavedResearchConfigModel:
    return SavedResearchConfigModel(
        id=record.id,
        config_type=record.config_type,
        name=record.name,
        description=record.description,
        config_schema_version=record.config_schema_version,
        payload_json=record.payload_json,
        instrument_symbol=record.instrument_symbol,
        asset_class=record.asset_class,
        interval=record.interval,
        created_at=record.created_at,
        updated_at=record.updated_at,
        last_used_at=record.last_used_at,
    )


def _watchlist_model_to_record(model: WatchlistItemModel) -> WatchlistItemRecord:
    return WatchlistItemRecord(
        id=model.id,
        symbol=model.symbol,
        asset_class=model.asset_class,
        source_context=model.source_context,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _recent_asset_model_to_record(model: RecentAssetModel) -> RecentAssetRecord:
    return RecentAssetRecord(
        id=model.id,
        symbol=model.symbol,
        asset_class=model.asset_class,
        source_context=model.source_context,
        last_used_at=model.last_used_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _recent_compare_model_to_record(model: RecentCompareSetModel) -> RecentCompareSetRecord:
    return RecentCompareSetRecord(
        id=model.id,
        fingerprint=model.fingerprint,
        compare_mode=model.compare_mode,
        run_ids=tuple(model.run_ids_json),
        last_used_at=model.last_used_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyWorkflowPersistenceRepository:
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_saved_configs(
        self,
        *,
        config_type: str | None = None,
        limit: int = 100,
    ) -> tuple[SavedResearchConfigRecord, ...]:
        try:
            with self._session_factory() as session:
                statement = select(SavedResearchConfigModel)
                if config_type is not None:
                    statement = statement.where(
                        SavedResearchConfigModel.config_type == config_type
                    )
                models = session.scalars(
                    statement.order_by(
                        func.coalesce(
                            SavedResearchConfigModel.last_used_at,
                            SavedResearchConfigModel.updated_at,
                        ).desc(),
                        SavedResearchConfigModel.updated_at.desc(),
                        SavedResearchConfigModel.id.desc(),
                    ).limit(limit)
                ).all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to list saved research configs."
            ) from exc
        return tuple(_saved_config_model_to_record(model) for model in models)

    def create_saved_config(
        self,
        record: SavedResearchConfigRecord,
    ) -> SavedResearchConfigRecord:
        try:
            with self._session_factory() as session:
                model = _saved_config_record_to_model(record)
                session.add(model)
                session.commit()
                session.refresh(model)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to create saved research config."
            ) from exc
        return _saved_config_model_to_record(model)

    def get_saved_config(self, config_id: str) -> SavedResearchConfigRecord | None:
        try:
            with self._session_factory() as session:
                model = session.get(SavedResearchConfigModel, config_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to load saved research config."
            ) from exc
        if model is None:
            return None
        return _saved_config_model_to_record(model)

    def update_saved_config(
        self,
        record: SavedResearchConfigRecord,
    ) -> SavedResearchConfigRecord:
        try:
            with self._session_factory() as session:
                model = session.get(SavedResearchConfigModel, record.id)
                if model is None:
                    raise KeyError(record.id)
                model.config_type = record.config_type
                model.name = record.name
                model.description = record.description
                model.config_schema_version = record.config_schema_version
                model.payload_json = record.payload_json
                model.instrument_symbol = record.instrument_symbol
                model.asset_class = record.asset_class
                model.interval = record.interval
                model.created_at = record.created_at
                model.updated_at = record.updated_at
                model.last_used_at = record.last_used_at
                session.commit()
                session.refresh(model)
        except KeyError:
            raise
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to update saved research config."
            ) from exc
        return _saved_config_model_to_record(model)

    def delete_saved_config(self, config_id: str) -> bool:
        try:
            with self._session_factory() as session:
                model = session.get(SavedResearchConfigModel, config_id)
                if model is None:
                    return False
                session.delete(model)
                session.commit()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to delete saved research config."
            ) from exc
        return True

    def mark_saved_config_used(
        self,
        config_id: str,
    ) -> SavedResearchConfigRecord | None:
        try:
            with self._session_factory() as session:
                model = session.get(SavedResearchConfigModel, config_id)
                if model is None:
                    return None
                model.last_used_at = _utcnow()
                model.updated_at = model.updated_at
                session.commit()
                session.refresh(model)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to update saved research config usage."
            ) from exc
        return _saved_config_model_to_record(model)

    def list_watchlist_items(self, *, limit: int = 100) -> tuple[WatchlistItemRecord, ...]:
        try:
            with self._session_factory() as session:
                models = session.scalars(
                    select(WatchlistItemModel)
                    .order_by(WatchlistItemModel.updated_at.desc(), WatchlistItemModel.symbol.asc())
                    .limit(limit)
                ).all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to list watchlist items."
            ) from exc
        return tuple(_watchlist_model_to_record(model) for model in models)

    def upsert_watchlist_item(
        self,
        *,
        symbol: str,
        asset_class: str,
        source_context: str | None = None,
    ) -> WatchlistItemRecord:
        now = _utcnow()
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(WatchlistItemModel).where(
                        WatchlistItemModel.symbol == symbol,
                        WatchlistItemModel.asset_class == asset_class,
                    )
                )
                if model is None:
                    model = WatchlistItemModel(
                        id=_new_id("wl"),
                        symbol=symbol,
                        asset_class=asset_class,
                        source_context=source_context,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(model)
                else:
                    model.source_context = source_context
                    model.updated_at = now
                session.commit()
                session.refresh(model)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("Failed to update watchlist.") from exc
        return _watchlist_model_to_record(model)

    def delete_watchlist_item(self, *, asset_class: str, symbol: str) -> bool:
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(WatchlistItemModel).where(
                        WatchlistItemModel.symbol == symbol,
                        WatchlistItemModel.asset_class == asset_class,
                    )
                )
                if model is None:
                    return False
                session.delete(model)
                session.commit()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("Failed to delete watchlist item.") from exc
        return True

    def list_recent_assets(self, *, limit: int = 20) -> tuple[RecentAssetRecord, ...]:
        try:
            with self._session_factory() as session:
                models = session.scalars(
                    select(RecentAssetModel)
                    .order_by(RecentAssetModel.last_used_at.desc(), RecentAssetModel.id.desc())
                    .limit(limit)
                ).all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("Failed to list recent assets.") from exc
        return tuple(_recent_asset_model_to_record(model) for model in models)

    def touch_recent_asset(
        self,
        *,
        symbol: str,
        asset_class: str,
        source_context: str | None = None,
    ) -> RecentAssetRecord:
        now = _utcnow()
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(RecentAssetModel).where(
                        RecentAssetModel.symbol == symbol,
                        RecentAssetModel.asset_class == asset_class,
                    )
                )
                if model is None:
                    model = RecentAssetModel(
                        id=_new_id("ra"),
                        symbol=symbol,
                        asset_class=asset_class,
                        source_context=source_context,
                        last_used_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(model)
                else:
                    model.source_context = source_context
                    model.last_used_at = now
                    model.updated_at = now
                session.commit()
                session.refresh(model)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("Failed to update recent assets.") from exc
        return _recent_asset_model_to_record(model)

    def list_recent_compare_sets(
        self,
        *,
        limit: int = 20,
    ) -> tuple[RecentCompareSetRecord, ...]:
        try:
            with self._session_factory() as session:
                models = session.scalars(
                    select(RecentCompareSetModel)
                    .order_by(
                        RecentCompareSetModel.last_used_at.desc(),
                        RecentCompareSetModel.id.desc(),
                    )
                    .limit(limit)
                ).all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to list recent compare selections."
            ) from exc
        return tuple(_recent_compare_model_to_record(model) for model in models)

    def touch_recent_compare_set(
        self,
        *,
        compare_mode: str,
        run_ids: list[str],
    ) -> RecentCompareSetRecord:
        now = _utcnow()
        fingerprint = compute_recent_compare_fingerprint(compare_mode, run_ids)
        try:
            with self._session_factory() as session:
                model = session.scalar(
                    select(RecentCompareSetModel).where(
                        RecentCompareSetModel.fingerprint == fingerprint
                    )
                )
                if model is None:
                    model = RecentCompareSetModel(
                        id=_new_id("cmp"),
                        fingerprint=fingerprint,
                        compare_mode=compare_mode,
                        run_ids_json=list(run_ids),
                        last_used_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(model)
                else:
                    model.compare_mode = compare_mode
                    model.run_ids_json = list(run_ids)
                    model.last_used_at = now
                    model.updated_at = now
                session.commit()
                session.refresh(model)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to update recent compare selections."
            ) from exc
        return _recent_compare_model_to_record(model)

