"""Configuration helpers for research orchestration runs."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import uuid

from .contracts import ResearchRunConfig


def generate_run_id(prefix: str = "research") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = uuid.uuid4().hex[:8]
    return f"{prefix}-{stamp}-{token}"


def resolve_run_config(config: ResearchRunConfig | None) -> ResearchRunConfig:
    cfg = config or ResearchRunConfig()
    run_id = cfg.run_id or generate_run_id()
    run_name = cfg.run_name or run_id
    output_dir = cfg.output_dir
    if cfg.persist_summary and output_dir is None:
        output_dir = "artifacts/research_runs"
    return replace(cfg, run_id=run_id, run_name=run_name, output_dir=output_dir)


def summary_output_path(config: ResearchRunConfig) -> Path | None:
    if not config.persist_summary:
        return None
    if config.output_dir is None or config.run_id is None:
        return None
    return Path(config.output_dir) / config.run_id / "summary.json"


def detail_output_path(config: ResearchRunConfig) -> Path | None:
    if not config.persist_summary:
        return None
    if config.output_dir is None or config.run_id is None:
        return None
    return Path(config.output_dir) / config.run_id / "detail.json"


def manifest_output_path(config: ResearchRunConfig) -> Path | None:
    if not config.persist_summary:
        return None
    if config.output_dir is None or config.run_id is None:
        return None
    return Path(config.output_dir) / config.run_id / "manifest.json"


def index_output_path(config: ResearchRunConfig) -> Path | None:
    if not config.persist_summary:
        return None
    if config.output_dir is None:
        return None
    return Path(config.output_dir) / "index.json"
