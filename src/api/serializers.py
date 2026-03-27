"""Serialization helpers from domain artifacts to API schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from market_data import HistoricalCandleResponse
from paper_trading import (
    PaperCancelActionResult,
    PaperFill,
    PaperOrder,
    PaperOrderActionResult,
    PaperPosition,
    PaperPriceUpdateResult,
    PaperStateSnapshot,
)
from research import ResearchRunArtifact

from .paper_trading_schemas import (
    PaperCancelActionResponseSchema,
    PaperFillSchema,
    PaperOrderActionResponseSchema,
    PaperOrderSchema,
    PaperPositionSchema,
    PaperPriceUpdateResponseSchema,
    PaperStateResponseSchema,
)
from .schemas import (
    MarketDataPreviewResponseSchema,
    RunDetailResponseSchema,
    RunSummaryResponseSchema,
    StoredRunSummaryListItemSchema,
)


def serialize_market_data_preview(
    response: HistoricalCandleResponse,
) -> MarketDataPreviewResponseSchema:
    return MarketDataPreviewResponseSchema.model_validate(
        {
            "provider": response.provider,
            "instrument": {
                "symbol": response.instrument.symbol,
                "asset_class": response.instrument.asset_class,
                "venue": response.instrument.venue,
                "quote_currency": response.instrument.quote_currency,
            },
            "interval": response.interval,
            "candles": [
                {
                    "timestamp": candle.timestamp,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in response.candles
            ],
            "metadata": dict(response.metadata),
        }
    )


def serialize_run_summary(artifact: ResearchRunArtifact) -> RunSummaryResponseSchema:
    return RunSummaryResponseSchema.model_validate(artifact.to_summary_dict())


def serialize_stored_run_summary(summary_payload: dict[str, Any]) -> RunSummaryResponseSchema:
    return RunSummaryResponseSchema.model_validate(summary_payload)


def serialize_stored_run_detail(detail_payload: dict[str, Any]) -> RunDetailResponseSchema:
    return RunDetailResponseSchema.model_validate(detail_payload)


def serialize_run_detail_from_summary(
    summary_payload: dict[str, Any],
) -> RunDetailResponseSchema:
    return RunDetailResponseSchema.model_validate(
        {
            "summary": summary_payload,
            "strategy_detail": None,
            "ml_detail": None,
        }
    )


def serialize_stored_list_item(
    *,
    summary_payload: dict[str, Any],
    path: Path,
) -> StoredRunSummaryListItemSchema:
    return StoredRunSummaryListItemSchema.model_validate(
        {
            "run_id": summary_payload.get("run_id", path.parent.name),
            "run_name": summary_payload.get("run_name"),
            "workflow_type": summary_payload.get("workflow_type"),
            "status": summary_payload.get("status"),
            "started_at": summary_payload.get("started_at"),
            "ended_at": summary_payload.get("ended_at"),
            "summary_path": str(path.as_posix()),
        }
    )


def serialize_paper_state(snapshot: PaperStateSnapshot) -> PaperStateResponseSchema:
    return PaperStateResponseSchema.model_validate(
        {
            "config": {
                "account_id": snapshot.config.account_id,
                "base_currency": snapshot.config.base_currency,
                "initial_cash": snapshot.config.initial_cash,
                "allow_short": snapshot.config.allow_short,
                "default_spread_bps": snapshot.config.default_spread_bps,
                "default_slippage_bps": snapshot.config.default_slippage_bps,
                "commission_bps": snapshot.config.commission_bps,
                "commission_fixed": snapshot.config.commission_fixed,
            },
            "account": {
                "account_id": snapshot.account.account_id,
                "base_currency": snapshot.account.base_currency,
                "cash": snapshot.account.cash,
                "realized_pnl": snapshot.account.realized_pnl,
                "unrealized_pnl": snapshot.account.unrealized_pnl,
                "equity": snapshot.account.equity,
                "total_fees": snapshot.account.total_fees,
                "updated_at": snapshot.account.updated_at,
            },
            "positions": [serialize_paper_position(position).model_dump() for position in snapshot.positions],
            "open_orders": [serialize_paper_order(order).model_dump() for order in snapshot.open_orders],
            "fills": [serialize_paper_fill(fill).model_dump() for fill in snapshot.fills],
            "price_book": dict(snapshot.price_book),
            "updated_at": snapshot.updated_at,
        }
    )


def serialize_paper_position(position: PaperPosition) -> PaperPositionSchema:
    return PaperPositionSchema.model_validate(
        {
            "instrument": {
                "symbol": position.instrument.symbol,
                "asset_class": position.instrument.asset_class,
                "venue": position.instrument.venue,
                "quote_currency": position.instrument.quote_currency,
            },
            "quantity": position.quantity,
            "average_price": position.average_price,
            "mark_price": position.mark_price,
            "unrealized_pnl": position.unrealized_pnl,
            "realized_pnl": position.realized_pnl,
            "updated_at": position.updated_at,
        }
    )


def serialize_paper_order(order: PaperOrder) -> PaperOrderSchema:
    return PaperOrderSchema.model_validate(
        {
            "order_id": order.order_id,
            "instrument": {
                "symbol": order.instrument.symbol,
                "asset_class": order.instrument.asset_class,
                "venue": order.instrument.venue,
                "quote_currency": order.instrument.quote_currency,
            },
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": order.quantity,
            "status": order.status.value,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "limit_price": order.limit_price,
            "reference_price": order.reference_price,
            "client_order_id": order.client_order_id,
            "rejection_reason": order.rejection_reason,
            "filled_quantity": order.filled_quantity,
            "average_fill_price": order.average_fill_price,
            "metadata": dict(order.metadata),
        }
    )


def serialize_paper_fill(fill: PaperFill) -> PaperFillSchema:
    return PaperFillSchema.model_validate(
        {
            "fill_id": fill.fill_id,
            "order_id": fill.order_id,
            "instrument": {
                "symbol": fill.instrument.symbol,
                "asset_class": fill.instrument.asset_class,
                "venue": fill.instrument.venue,
                "quote_currency": fill.instrument.quote_currency,
            },
            "side": fill.side.value,
            "quantity": fill.quantity,
            "fill_price": fill.fill_price,
            "notional": fill.notional,
            "commission": fill.commission,
            "spread_cost": fill.spread_cost,
            "slippage_cost": fill.slippage_cost,
            "realized_pnl_delta": fill.realized_pnl_delta,
            "timestamp": fill.timestamp,
        }
    )


def serialize_paper_order_action(
    result: PaperOrderActionResult,
) -> PaperOrderActionResponseSchema:
    return PaperOrderActionResponseSchema.model_validate(
        {
            "order": serialize_paper_order(result.order).model_dump(),
            "fills": [serialize_paper_fill(fill).model_dump() for fill in result.fills],
            "state": serialize_paper_state(result.state).model_dump(),
        }
    )


def serialize_paper_cancel_action(
    result: PaperCancelActionResult,
) -> PaperCancelActionResponseSchema:
    return PaperCancelActionResponseSchema.model_validate(
        {
            "order": serialize_paper_order(result.order).model_dump(),
            "state": serialize_paper_state(result.state).model_dump(),
        }
    )


def serialize_paper_price_update(
    result: PaperPriceUpdateResult,
) -> PaperPriceUpdateResponseSchema:
    return PaperPriceUpdateResponseSchema.model_validate(
        {
            "filled_order_ids": list(result.filled_order_ids),
            "state": serialize_paper_state(result.state).model_dump(),
        }
    )
