"""Run history browsing and read endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..history_schemas import HistoryReadResponseSchema, RunHistoryListResponseSchema
from ..services import APIService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/runs", response_model=RunHistoryListResponseSchema)
async def list_history_runs(
    workflow_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="started_desc", pattern="^(started_desc|started_asc)$"),
    api_service: APIService = Depends(get_api_service),
) -> RunHistoryListResponseSchema:
    return await run_in_threadpool(
        api_service.list_history_runs,
        workflow_type=workflow_type,
        status=status,
        search=q,
        started_after=started_after,
        started_before=started_before,
        limit=limit,
        offset=offset,
        sort=sort,
    )


@router.get("/runs/{run_id}", response_model=HistoryReadResponseSchema)
async def read_history_run(
    run_id: str,
    api_service: APIService = Depends(get_api_service),
) -> HistoryReadResponseSchema:
    return await run_in_threadpool(api_service.get_history_run, run_id)
