"""Saved-run history and compare API orchestration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from config import AppSettings
from persistence import PersistenceUnavailableError, ResearchRunMetadataRecord, ResearchRunMetadataRepository
from research import (
    RunHistoryQuery,
    compare_saved_runs,
    list_run_history,
    load_persisted_run_summary,
    load_saved_run_bundle,
)

from ..config import APISettings
from ..errors import APIError
from ..history_schemas import (
    CompareRunsRequestSchema,
    CompareRunsResponseSchema,
    HistoryReadResponseSchema,
    RunHistoryItemSchema,
    RunHistoryListResponseSchema,
)
from ..schemas import (
    RunDetailResponseSchema,
    RunSummaryResponseSchema,
    StoredRunSummaryListResponseSchema,
)
from ..serializers import (
    serialize_compare_runs_result,
    serialize_manifest_view,
    serialize_persisted_run_detail,
    serialize_persisted_run_summary,
    serialize_run_history_item,
)
from .common import ensure_feature_enabled, history_root

LOGGER = logging.getLogger(__name__)


class HistoryAPIService:
    def __init__(
        self,
        *,
        settings: APISettings,
        app_settings: AppSettings,
        metadata_repository: ResearchRunMetadataRepository | None = None,
    ) -> None:
        self._settings = settings
        self._app_settings = app_settings
        self._metadata_repository = metadata_repository

    def _load_metadata(self, run_id: str) -> ResearchRunMetadataRecord | None:
        if self._metadata_repository is None:
            return None
        try:
            return self._metadata_repository.get_run_metadata(run_id)
        except PersistenceUnavailableError as exc:
            LOGGER.warning(
                "Research metadata DB unavailable during run read; falling back to artifacts. %s",
                exc,
            )
            return None

    def list_saved_run_summaries(self, *, limit: int = 50) -> StoredRunSummaryListResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        history = self.list_history_runs(limit=limit, offset=0)
        items = []
        for run in history.items:
            items.append(
                {
                    "run_id": run.run_id,
                    "run_name": run.run_name,
                    "workflow_type": run.workflow_type,
                    "status": run.status,
                    "started_at": run.started_at,
                    "ended_at": run.ended_at,
                    "summary_path": f"{run.run_id}/summary.json",
                }
            )
        return StoredRunSummaryListResponseSchema.model_validate({"runs": items})

    def get_saved_run_summary(self, run_id: str) -> RunSummaryResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        try:
            summary = load_persisted_run_summary(
                history_root(self._settings),
                run_id,
                metadata=self._load_metadata(run_id),
            )
            return serialize_persisted_run_summary(summary)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_summary_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_summary_read_error",
                message=f"Failed to read summary for run_id '{run_id}'",
            ) from exc

    def get_saved_run_detail(self, run_id: str) -> RunDetailResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        try:
            detail = load_saved_run_bundle(
                history_root(self._settings),
                run_id,
                metadata=self._load_metadata(run_id),
            ).detail
            return serialize_persisted_run_detail(detail)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_detail_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_detail_read_error",
                message=f"Failed to read detail for run_id '{run_id}'",
            ) from exc

    def list_history_runs(
        self,
        *,
        workflow_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "started_desc",
    ) -> RunHistoryListResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        result = list_run_history(
            history_root(self._settings),
            RunHistoryQuery(
                workflow_type=workflow_type,
                status=status,
                search=search,
                started_after=started_after,
                started_before=started_before,
                limit=limit,
                offset=offset,
                sort=sort,
            ),
            metadata_repository=self._metadata_repository,
        )
        items = [
            serialize_run_history_item(record)
            for record in result.items
        ]
        return RunHistoryListResponseSchema(
            items=items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            warnings=list(result.warnings),
        )

    def get_history_run(self, run_id: str) -> HistoryReadResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        try:
            bundle = load_saved_run_bundle(
                history_root(self._settings),
                run_id,
                metadata=self._load_metadata(run_id),
            )
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_read_error",
                message=f"Failed to load run artifacts for '{run_id}'",
            ) from exc
        summary = serialize_persisted_run_summary(bundle.summary)
        detail = serialize_persisted_run_detail(bundle.detail)
        return HistoryReadResponseSchema.model_validate(
            {
                "manifest": serialize_manifest_view(bundle.manifest),
                "summary": summary.model_dump(),
                "detail": detail.model_dump(),
            }
        )

    def compare_runs(self, request: CompareRunsRequestSchema) -> CompareRunsResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "compare_api_enabled",
            code="compare_disabled",
            message="Run comparison endpoint is disabled by feature flag.",
        )
        try:
            result = compare_saved_runs(
                root_dir=history_root(self._settings),
                run_ids=request.run_ids,
                mode=request.mode,
                metadata_repository=self._metadata_repository,
            )
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="compare_invalid",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="compare_read_error",
                message="Failed to compare selected runs",
            ) from exc
        return serialize_compare_runs_result(result)
