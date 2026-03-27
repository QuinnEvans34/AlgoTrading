"""Account and position math for paper trading state transitions."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Mapping

from market_data import Instrument

from .contracts import PaperAccountState, PaperOrderSide, PaperPosition


_EPSILON = 1e-12


def symbol_key(symbol: str) -> str:
    return symbol.strip().upper()


def signed_quantity(side: PaperOrderSide, quantity: float) -> float:
    return quantity if side == PaperOrderSide.BUY else -quantity


def apply_fill_to_account(
    *,
    account: PaperAccountState,
    positions: Mapping[str, PaperPosition],
    instrument: Instrument,
    side: PaperOrderSide,
    quantity: float,
    fill_price: float,
    commission: float,
    timestamp: datetime,
) -> tuple[PaperAccountState, dict[str, PaperPosition], float]:
    """Apply a fill to net position/account state and return realized PnL delta."""

    key = symbol_key(instrument.symbol)
    existing = positions.get(key)
    old_qty = 0.0 if existing is None else existing.quantity
    old_avg = 0.0 if existing is None else existing.average_price

    fill_signed = signed_quantity(side, quantity)
    new_qty = old_qty + fill_signed
    realized_delta = 0.0

    if abs(old_qty) < _EPSILON:
        next_avg = fill_price
    elif _same_sign(old_qty, fill_signed):
        total_abs = abs(old_qty) + abs(fill_signed)
        next_avg = ((abs(old_qty) * old_avg) + (abs(fill_signed) * fill_price)) / total_abs
    else:
        closed_qty = min(abs(old_qty), abs(fill_signed))
        if old_qty > 0:
            realized_delta = (fill_price - old_avg) * closed_qty
        else:
            realized_delta = (old_avg - fill_price) * closed_qty
        if abs(new_qty) < _EPSILON:
            next_avg = 0.0
        elif _same_sign(new_qty, old_qty):
            next_avg = old_avg
        else:
            next_avg = fill_price

    updated_positions = dict(positions)
    if abs(new_qty) < _EPSILON:
        updated_positions.pop(key, None)
    else:
        prior_realized = 0.0 if existing is None else existing.realized_pnl
        updated_positions[key] = PaperPosition(
            instrument=instrument,
            quantity=new_qty,
            average_price=next_avg,
            mark_price=(fill_price if existing is None else existing.mark_price),
            unrealized_pnl=(0.0 if existing is None else existing.unrealized_pnl),
            realized_pnl=prior_realized + realized_delta,
            updated_at=timestamp,
        )

    notional_signed = fill_signed * fill_price
    new_cash = account.cash - notional_signed - commission
    updated_account = replace(
        account,
        cash=new_cash,
        realized_pnl=account.realized_pnl + realized_delta,
        total_fees=account.total_fees + commission,
        updated_at=timestamp,
    )
    return updated_account, updated_positions, realized_delta


def mark_to_market(
    *,
    account: PaperAccountState,
    positions: Mapping[str, PaperPosition],
    price_book: Mapping[str, float],
    timestamp: datetime,
) -> tuple[PaperAccountState, dict[str, PaperPosition]]:
    """Revalue unrealized PnL and equity from the latest mark prices."""

    unrealized_total = 0.0
    updated_positions: dict[str, PaperPosition] = {}
    for key, position in positions.items():
        mark = price_book.get(key, position.mark_price if position.mark_price is not None else position.average_price)
        if mark is None:
            mark = position.average_price
        if position.quantity >= 0:
            unrealized = (mark - position.average_price) * position.quantity
        else:
            unrealized = (position.average_price - mark) * abs(position.quantity)
        unrealized_total += unrealized
        updated_positions[key] = replace(
            position,
            mark_price=mark,
            unrealized_pnl=unrealized,
            updated_at=timestamp,
        )

    equity = account.cash + sum(
        position.quantity * (position.mark_price if position.mark_price is not None else position.average_price)
        for position in updated_positions.values()
    )
    updated_account = replace(
        account,
        unrealized_pnl=unrealized_total,
        equity=equity,
        updated_at=timestamp,
    )
    return updated_account, updated_positions


def _same_sign(a: float, b: float) -> bool:
    return (a > 0 and b > 0) or (a < 0 and b < 0)

