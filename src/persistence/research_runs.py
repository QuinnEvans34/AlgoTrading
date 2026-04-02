"""Typed contracts and repository for research-run metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .errors import PersistenceUnavailableError
from .models import ResearchRunMetadataModel

if TYPE_CHECKING:
    from research.persisted_models import PersistedManifestView, PersistedRunSummary

METADATA_SCHEMA_VERSION = 1
METADATA_SOURCE_DUAL_WRITE = "dual_write"
METADATA_SOURCE_LEGACY_BACKFILL = "legacy_backfill"
METADATA_SOURCE_ARTIFACT_RECONCILED = "artifact_reconciled"
ALLOWED_METADATA_SOURCES = frozenset(
    {
        METADATA_SOURCE_DUAL_WRITE,
        METADATA_SOURCE_LEGACY_BACKFILL,
        METADATA_SOURCE_ARTIFACT_RECONCILED,
    }
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value):  # noqa: ANN001
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ResearchRunMetadataRecord:
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    instrument_symbol: str
    asset_class: str | None
    interval: str | None
    candle_count: int | None
    candle_source_type: str | None
    has_strategy: bool
    has_ml: bool
    strategy_id: str | None
    total_trades: int | None
    total_return_pct: float | None
    total_net_pnl: float | None
    max_drawdown_pct: float | None
    sharpe_ratio: float | None
    ml_task_type: str | None
    ml_target_label: str | None
    ml_best_model_id: str | None
    ml_primary_metric_name: str | None
    ml_best_validation_value: float | None
    ml_best_test_value: float | None
    ml_model_count_executed: int | None
    ml_model_count_skipped: int | None
    ml_warning_count: int | None
    summary_path: str
    detail_path: str | None
    manifest_path: str | None
    metadata_schema_version: int
    artifact_schema_version: int | None
    metadata_source: str
    manifest_synthetic: bool
    summary_available: bool
    detail_available: bool
    created_at: datetime
    updated_at: datetime
    artifact_fingerprint: str | None
    last_synced_at: datetime | None


@dataclass(frozen=True)
class ResearchRunMetadataQuery:
    workflow_type: str | None = None
    status: str | None = None
    search: str | None = None
    started_after: datetime | None = None
    started_before: datetime | None = None
    sort: str = "started_desc"
    limit: int | None = None
    offset: int = 0


@dataclass(frozen=True)
class ResearchRunMetadataListResult:
    items: tuple[ResearchRunMetadataRecord, ...]
    total: int
    limit: int | None
    offset: int


class ResearchRunMetadataRepository(Protocol):
    def upsert_run_metadata(self, record: ResearchRunMetadataRecord) -> None: ...

    def get_run_metadata(self, run_id: str) -> ResearchRunMetadataRecord | None: ...

    def list_run_metadata(
        self,
        query: ResearchRunMetadataQuery,
    ) -> ResearchRunMetadataListResult: ...

    def list_known_run_ids(self) -> set[str]: ...


def metadata_record_fingerprint_payload(
    record: ResearchRunMetadataRecord,
) -> dict[str, object | None]:
    payload = asdict(record)
    payload.pop("metadata_source", None)
    payload.pop("artifact_fingerprint", None)
    payload.pop("last_synced_at", None)
    return _json_safe(payload)


def compute_artifact_fingerprint(record: ResearchRunMetadataRecord) -> str:
    canonical = json.dumps(
        metadata_record_fingerprint_payload(record),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_run_metadata_record(
    *,
    root_dir: Path,
    summary: "PersistedRunSummary",
    manifest: "PersistedManifestView",
    metadata_source: str,
    last_synced_at: datetime | None = None,
) -> ResearchRunMetadataRecord:
    from research.persisted_models import LEGACY_ARTIFACT_SCHEMA_VERSION

    if metadata_source not in ALLOWED_METADATA_SOURCES:
        raise ValueError(f"Unsupported metadata_source '{metadata_source}'")

    strategy = summary.strategy
    ml = summary.ml
    record = ResearchRunMetadataRecord(
        run_id=summary.run_id,
        run_name=summary.run_name,
        workflow_type=summary.workflow_type,
        status=summary.status,
        started_at=summary.started_at,
        ended_at=summary.ended_at,
        duration_ms=summary.duration_ms,
        instrument_symbol=summary.instrument.symbol,
        asset_class=summary.instrument.asset_class,
        interval=summary.interval,
        candle_count=summary.candle_count,
        candle_source_type=summary.candle_source_type,
        has_strategy=strategy is not None,
        has_ml=ml is not None,
        strategy_id=None if strategy is None else strategy.strategy_id,
        total_trades=None if strategy is None else strategy.total_trades,
        total_return_pct=None if strategy is None else strategy.total_return_pct,
        total_net_pnl=None if strategy is None else strategy.total_net_pnl,
        max_drawdown_pct=None if strategy is None else strategy.max_drawdown_pct,
        sharpe_ratio=None if strategy is None else strategy.sharpe_ratio,
        ml_task_type=None if ml is None else ml.task_type,
        ml_target_label=None if ml is None else ml.target_label,
        ml_best_model_id=None if ml is None else ml.best_model_id,
        ml_primary_metric_name=None if ml is None else ml.primary_metric_name,
        ml_best_validation_value=None if ml is None else ml.best_validation_value,
        ml_best_test_value=None if ml is None else ml.best_test_value,
        ml_model_count_executed=None if ml is None else ml.model_count_executed,
        ml_model_count_skipped=None if ml is None else ml.model_count_skipped,
        ml_warning_count=None if ml is None else ml.warning_count,
        summary_path=manifest.summary_path,
        detail_path=manifest.detail_path,
        manifest_path=f"{summary.run_id}/manifest.json",
        metadata_schema_version=METADATA_SCHEMA_VERSION,
        artifact_schema_version=(
            manifest.schema_version
            if manifest.schema_version is not None
            else LEGACY_ARTIFACT_SCHEMA_VERSION
        ),
        metadata_source=metadata_source,
        manifest_synthetic=manifest.synthetic,
        summary_available=(root_dir / manifest.summary_path).exists(),
        detail_available=(
            False
            if manifest.detail_path is None
            else (root_dir / manifest.detail_path).exists()
        ),
        created_at=manifest.created_at or summary.started_at,
        updated_at=manifest.updated_at or summary.ended_at,
        artifact_fingerprint=None,
        last_synced_at=last_synced_at or _utcnow(),
    )
    return replace(record, artifact_fingerprint=compute_artifact_fingerprint(record))


def _model_to_record(model: ResearchRunMetadataModel) -> ResearchRunMetadataRecord:
    return ResearchRunMetadataRecord(
        run_id=model.run_id,
        run_name=model.run_name,
        workflow_type=model.workflow_type,
        status=model.status,
        started_at=model.started_at,
        ended_at=model.ended_at,
        duration_ms=model.duration_ms,
        instrument_symbol=model.instrument_symbol,
        asset_class=model.asset_class,
        interval=model.interval,
        candle_count=model.candle_count,
        candle_source_type=model.candle_source_type,
        has_strategy=model.has_strategy,
        has_ml=model.has_ml,
        strategy_id=model.strategy_id,
        total_trades=model.total_trades,
        total_return_pct=model.total_return_pct,
        total_net_pnl=model.total_net_pnl,
        max_drawdown_pct=model.max_drawdown_pct,
        sharpe_ratio=model.sharpe_ratio,
        ml_task_type=model.ml_task_type,
        ml_target_label=model.ml_target_label,
        ml_best_model_id=model.ml_best_model_id,
        ml_primary_metric_name=model.ml_primary_metric_name,
        ml_best_validation_value=model.ml_best_validation_value,
        ml_best_test_value=model.ml_best_test_value,
        ml_model_count_executed=model.ml_model_count_executed,
        ml_model_count_skipped=model.ml_model_count_skipped,
        ml_warning_count=model.ml_warning_count,
        summary_path=model.summary_path,
        detail_path=model.detail_path,
        manifest_path=model.manifest_path,
        metadata_schema_version=model.metadata_schema_version,
        artifact_schema_version=model.artifact_schema_version,
        metadata_source=model.metadata_source,
        manifest_synthetic=model.manifest_synthetic,
        summary_available=model.summary_available,
        detail_available=model.detail_available,
        created_at=model.created_at,
        updated_at=model.updated_at,
        artifact_fingerprint=model.artifact_fingerprint,
        last_synced_at=model.last_synced_at,
    )


def _record_to_model(record: ResearchRunMetadataRecord) -> ResearchRunMetadataModel:
    return ResearchRunMetadataModel(
        run_id=record.run_id,
        run_name=record.run_name,
        workflow_type=record.workflow_type,
        status=record.status,
        started_at=record.started_at,
        ended_at=record.ended_at,
        duration_ms=record.duration_ms,
        instrument_symbol=record.instrument_symbol,
        asset_class=record.asset_class,
        interval=record.interval,
        candle_count=record.candle_count,
        candle_source_type=record.candle_source_type,
        has_strategy=record.has_strategy,
        has_ml=record.has_ml,
        strategy_id=record.strategy_id,
        total_trades=record.total_trades,
        total_return_pct=record.total_return_pct,
        total_net_pnl=record.total_net_pnl,
        max_drawdown_pct=record.max_drawdown_pct,
        sharpe_ratio=record.sharpe_ratio,
        ml_task_type=record.ml_task_type,
        ml_target_label=record.ml_target_label,
        ml_best_model_id=record.ml_best_model_id,
        ml_primary_metric_name=record.ml_primary_metric_name,
        ml_best_validation_value=record.ml_best_validation_value,
        ml_best_test_value=record.ml_best_test_value,
        ml_model_count_executed=record.ml_model_count_executed,
        ml_model_count_skipped=record.ml_model_count_skipped,
        ml_warning_count=record.ml_warning_count,
        summary_path=record.summary_path,
        detail_path=record.detail_path,
        manifest_path=record.manifest_path,
        metadata_schema_version=record.metadata_schema_version,
        artifact_schema_version=record.artifact_schema_version,
        metadata_source=record.metadata_source,
        manifest_synthetic=record.manifest_synthetic,
        summary_available=record.summary_available,
        detail_available=record.detail_available,
        created_at=record.created_at,
        updated_at=record.updated_at,
        artifact_fingerprint=record.artifact_fingerprint,
        last_synced_at=record.last_synced_at,
    )


class SQLAlchemyResearchRunMetadataRepository:
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_run_metadata(self, record: ResearchRunMetadataRecord) -> None:
        try:
            with self._session_factory() as session:
                session.merge(_record_to_model(record))
                session.commit()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to persist research run metadata."
            ) from exc

    def get_run_metadata(self, run_id: str) -> ResearchRunMetadataRecord | None:
        try:
            with self._session_factory() as session:
                model = session.get(ResearchRunMetadataModel, run_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to load research run metadata."
            ) from exc
        if model is None:
            return None
        return _model_to_record(model)

    def list_run_metadata(
        self,
        query: ResearchRunMetadataQuery,
    ) -> ResearchRunMetadataListResult:
        try:
            with self._session_factory() as session:
                filtered = self._filtered_statement(query)
                total = session.scalar(
                    select(func.count()).select_from(filtered.subquery())
                )
                ordered = self._ordered_statement(filtered, query.sort)
                if query.offset > 0:
                    ordered = ordered.offset(query.offset)
                if query.limit is not None:
                    ordered = ordered.limit(query.limit)
                models = tuple(session.scalars(ordered).all())
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to query research run metadata."
            ) from exc
        return ResearchRunMetadataListResult(
            items=tuple(_model_to_record(model) for model in models),
            total=0 if total is None else int(total),
            limit=query.limit,
            offset=query.offset,
        )

    def list_known_run_ids(self) -> set[str]:
        try:
            with self._session_factory() as session:
                values = session.scalars(select(ResearchRunMetadataModel.run_id)).all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "Failed to list persisted research run ids."
            ) from exc
        return {str(value) for value in values}

    @staticmethod
    def _filtered_statement(query: ResearchRunMetadataQuery):
        statement = select(ResearchRunMetadataModel)
        if query.workflow_type:
            statement = statement.where(
                ResearchRunMetadataModel.workflow_type == query.workflow_type
            )
        if query.status:
            statement = statement.where(ResearchRunMetadataModel.status == query.status)
        if query.search:
            needle = f"%{query.search.lower()}%"
            statement = statement.where(
                or_(
                    func.lower(ResearchRunMetadataModel.run_id).like(needle),
                    func.lower(ResearchRunMetadataModel.run_name).like(needle),
                    func.lower(ResearchRunMetadataModel.instrument_symbol).like(needle),
                )
            )
        if query.started_after is not None:
            statement = statement.where(
                ResearchRunMetadataModel.started_at.is_not(None),
                ResearchRunMetadataModel.started_at >= query.started_after,
            )
        if query.started_before is not None:
            statement = statement.where(
                ResearchRunMetadataModel.started_at.is_not(None),
                ResearchRunMetadataModel.started_at <= query.started_before,
            )
        return statement

    @staticmethod
    def _ordered_statement(statement, sort: str):  # noqa: ANN001
        order_column = func.coalesce(
            ResearchRunMetadataModel.started_at,
            ResearchRunMetadataModel.updated_at,
        )
        if sort == "started_asc":
            return statement.order_by(order_column.asc(), ResearchRunMetadataModel.run_id.asc())
        return statement.order_by(order_column.desc(), ResearchRunMetadataModel.run_id.desc())
