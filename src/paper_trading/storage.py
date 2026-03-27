"""Local persistence for paper trading state."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from market_data import AssetClass, Instrument

from .contracts import (
    PaperAccountConfig,
    PaperAccountState,
    PaperFill,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPosition,
    PaperTradingState,
    utcnow,
)

STATE_FILENAME = "state.json"
SCHEMA_VERSION = 1


def _parse_dt(raw: str | None) -> datetime:
    if raw is None:
        return utcnow()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return utcnow()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)


def _instrument_to_dict(instrument: Instrument) -> dict[str, Any]:
    return {
        "symbol": instrument.symbol,
        "asset_class": instrument.asset_class.value,
        "venue": instrument.venue,
        "quote_currency": instrument.quote_currency,
    }


def _instrument_from_dict(payload: Mapping[str, Any]) -> Instrument:
    return Instrument(
        symbol=str(payload.get("symbol", "UNKNOWN")),
        asset_class=AssetClass(str(payload.get("asset_class", AssetClass.STOCK.value))),
        venue=(None if payload.get("venue") is None else str(payload.get("venue"))),
        quote_currency=(
            None if payload.get("quote_currency") is None else str(payload.get("quote_currency"))
        ),
    )


def _config_to_dict(config: PaperAccountConfig) -> dict[str, Any]:
    return asdict(config)


def _config_from_dict(payload: Mapping[str, Any]) -> PaperAccountConfig:
    return PaperAccountConfig(
        account_id=str(payload.get("account_id", "paper-main")),
        base_currency=str(payload.get("base_currency", "USD")),
        initial_cash=float(payload.get("initial_cash", 100_000.0)),
        allow_short=bool(payload.get("allow_short", False)),
        default_spread_bps=float(payload.get("default_spread_bps", 0.0)),
        default_slippage_bps=float(payload.get("default_slippage_bps", 0.0)),
        commission_bps=float(payload.get("commission_bps", 0.0)),
        commission_fixed=float(payload.get("commission_fixed", 0.0)),
    )


def _account_to_dict(account: PaperAccountState) -> dict[str, Any]:
    payload = asdict(account)
    payload["updated_at"] = account.updated_at.isoformat()
    return payload


def _account_from_dict(payload: Mapping[str, Any]) -> PaperAccountState:
    return PaperAccountState(
        account_id=str(payload.get("account_id", "paper-main")),
        base_currency=str(payload.get("base_currency", "USD")),
        cash=float(payload.get("cash", 0.0)),
        realized_pnl=float(payload.get("realized_pnl", 0.0)),
        unrealized_pnl=float(payload.get("unrealized_pnl", 0.0)),
        equity=float(payload.get("equity", payload.get("cash", 0.0))),
        total_fees=float(payload.get("total_fees", 0.0)),
        updated_at=_parse_dt(payload.get("updated_at")),
    )


def _position_to_dict(position: PaperPosition) -> dict[str, Any]:
    return {
        "instrument": _instrument_to_dict(position.instrument),
        "quantity": position.quantity,
        "average_price": position.average_price,
        "mark_price": position.mark_price,
        "unrealized_pnl": position.unrealized_pnl,
        "realized_pnl": position.realized_pnl,
        "updated_at": position.updated_at.isoformat(),
    }


def _position_from_dict(payload: Mapping[str, Any]) -> PaperPosition:
    return PaperPosition(
        instrument=_instrument_from_dict(payload.get("instrument", {})),
        quantity=float(payload.get("quantity", 0.0)),
        average_price=float(payload.get("average_price", 0.0)),
        mark_price=(None if payload.get("mark_price") is None else float(payload.get("mark_price"))),
        unrealized_pnl=float(payload.get("unrealized_pnl", 0.0)),
        realized_pnl=float(payload.get("realized_pnl", 0.0)),
        updated_at=_parse_dt(payload.get("updated_at")),
    )


def _order_to_dict(order: PaperOrder) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "instrument": _instrument_to_dict(order.instrument),
        "side": order.side.value,
        "order_type": order.order_type.value,
        "quantity": order.quantity,
        "status": order.status.value,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "limit_price": order.limit_price,
        "reference_price": order.reference_price,
        "client_order_id": order.client_order_id,
        "rejection_reason": order.rejection_reason,
        "filled_quantity": order.filled_quantity,
        "average_fill_price": order.average_fill_price,
        "metadata": dict(order.metadata),
    }


def _order_from_dict(payload: Mapping[str, Any]) -> PaperOrder:
    return PaperOrder(
        order_id=str(payload.get("order_id", "")),
        instrument=_instrument_from_dict(payload.get("instrument", {})),
        side=PaperOrderSide(str(payload.get("side", PaperOrderSide.BUY.value))),
        order_type=PaperOrderType(str(payload.get("order_type", PaperOrderType.MARKET.value))),
        quantity=float(payload.get("quantity", 0.0)),
        status=PaperOrderStatus(str(payload.get("status", PaperOrderStatus.OPEN.value))),
        created_at=_parse_dt(payload.get("created_at")),
        updated_at=_parse_dt(payload.get("updated_at")),
        limit_price=(None if payload.get("limit_price") is None else float(payload.get("limit_price"))),
        reference_price=(
            None if payload.get("reference_price") is None else float(payload.get("reference_price"))
        ),
        client_order_id=(
            None if payload.get("client_order_id") is None else str(payload.get("client_order_id"))
        ),
        rejection_reason=(
            None if payload.get("rejection_reason") is None else str(payload.get("rejection_reason"))
        ),
        filled_quantity=float(payload.get("filled_quantity", 0.0)),
        average_fill_price=(
            None if payload.get("average_fill_price") is None else float(payload.get("average_fill_price"))
        ),
        metadata=(
            {}
            if not isinstance(payload.get("metadata"), Mapping)
            else dict(payload.get("metadata", {}))
        ),
    )


def _fill_to_dict(fill: PaperFill) -> dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "order_id": fill.order_id,
        "instrument": _instrument_to_dict(fill.instrument),
        "side": fill.side.value,
        "quantity": fill.quantity,
        "fill_price": fill.fill_price,
        "notional": fill.notional,
        "commission": fill.commission,
        "spread_cost": fill.spread_cost,
        "slippage_cost": fill.slippage_cost,
        "realized_pnl_delta": fill.realized_pnl_delta,
        "timestamp": fill.timestamp.isoformat(),
    }


def _fill_from_dict(payload: Mapping[str, Any]) -> PaperFill:
    return PaperFill(
        fill_id=str(payload.get("fill_id", "")),
        order_id=str(payload.get("order_id", "")),
        instrument=_instrument_from_dict(payload.get("instrument", {})),
        side=PaperOrderSide(str(payload.get("side", PaperOrderSide.BUY.value))),
        quantity=float(payload.get("quantity", 0.0)),
        fill_price=float(payload.get("fill_price", 0.0)),
        notional=float(payload.get("notional", 0.0)),
        commission=float(payload.get("commission", 0.0)),
        spread_cost=float(payload.get("spread_cost", 0.0)),
        slippage_cost=float(payload.get("slippage_cost", 0.0)),
        realized_pnl_delta=float(payload.get("realized_pnl_delta", 0.0)),
        timestamp=_parse_dt(payload.get("timestamp")),
    )


class PaperTradingStorage:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._state_path = root_dir / STATE_FILENAME

    @property
    def state_path(self) -> Path:
        return self._state_path

    def load_or_initialize(self, config: PaperAccountConfig) -> PaperTradingState:
        if self._state_path.exists():
            return self._load_state()
        state = self._new_state(config)
        self.save_state(state)
        return state

    def reset_state(self, config: PaperAccountConfig) -> PaperTradingState:
        state = self._new_state(config)
        self.save_state(state)
        return state

    def save_state(self, state: PaperTradingState) -> None:
        _atomic_write_json(self._state_path, self._to_dict(state))

    def _load_state(self) -> PaperTradingState:
        payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        return self._from_dict(payload)

    @staticmethod
    def _new_state(config: PaperAccountConfig) -> PaperTradingState:
        now = utcnow()
        account = PaperAccountState.from_config(config)
        return PaperTradingState(
            config=config,
            account=account,
            positions=(),
            orders=(),
            fills=(),
            price_book={},
            next_order_sequence=1,
            next_fill_sequence=1,
            updated_at=now,
        )

    def _to_dict(self, state: PaperTradingState) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "config": _config_to_dict(state.config),
            "account": _account_to_dict(state.account),
            "positions": [_position_to_dict(position) for position in state.positions],
            "orders": [_order_to_dict(order) for order in state.orders],
            "fills": [_fill_to_dict(fill) for fill in state.fills],
            "price_book": dict(state.price_book),
            "next_order_sequence": state.next_order_sequence,
            "next_fill_sequence": state.next_fill_sequence,
            "updated_at": state.updated_at.isoformat(),
        }

    def _from_dict(self, payload: Mapping[str, Any]) -> PaperTradingState:
        config = _config_from_dict(payload.get("config", {}))
        account = _account_from_dict(payload.get("account", {}))
        positions = tuple(
            _position_from_dict(item)
            for item in payload.get("positions", [])
            if isinstance(item, Mapping)
        )
        orders = tuple(
            _order_from_dict(item)
            for item in payload.get("orders", [])
            if isinstance(item, Mapping)
        )
        fills = tuple(
            _fill_from_dict(item)
            for item in payload.get("fills", [])
            if isinstance(item, Mapping)
        )
        raw_price_book = payload.get("price_book", {})
        price_book = {
            str(symbol): float(price)
            for symbol, price in raw_price_book.items()
            if isinstance(symbol, str)
        }
        return PaperTradingState(
            config=config,
            account=account,
            positions=positions,
            orders=orders,
            fills=fills,
            price_book=price_book,
            next_order_sequence=int(payload.get("next_order_sequence", 1)),
            next_fill_sequence=int(payload.get("next_fill_sequence", 1)),
            updated_at=_parse_dt(payload.get("updated_at")),
        )

