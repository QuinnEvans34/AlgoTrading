"""Paper trading service orchestrating order actions and persisted state."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Iterable

from .account import apply_fill_to_account, mark_to_market, symbol_key
from .contracts import (
    PaperAccountConfig,
    PaperCancelActionResult,
    PaperFill,
    PaperOrder,
    PaperOrderActionResult,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPriceUpdateResult,
    PaperSignalDirection,
    PaperSignalIntent,
    PaperStateSnapshot,
    PaperTradingState,
    PriceUpdate,
    utcnow,
)
from .execution import compute_limit_fill, compute_market_fill, is_limit_marketable
from .orders import (
    ensure_unique_client_order_id,
    generate_fill_id,
    generate_order_id,
    mark_order_cancelled,
    mark_order_filled,
    mark_order_rejected,
    new_open_order,
    validate_order_request,
)
from .storage import PaperTradingStorage


class PaperTradingService:
    def __init__(
        self,
        *,
        storage: PaperTradingStorage,
        default_config: PaperAccountConfig,
    ) -> None:
        self._storage = storage
        self._default_config = default_config

    def get_state(self, *, fills_limit: int = 100) -> PaperStateSnapshot:
        state = self._storage.load_or_initialize(self._default_config)
        return self._snapshot(state, fills_limit=fills_limit)

    def reset_account(
        self,
        *,
        config: PaperAccountConfig | None = None,
        fills_limit: int = 100,
    ) -> PaperStateSnapshot:
        state = self._storage.reset_state(config or self._default_config)
        return self._snapshot(state, fills_limit=fills_limit)

    def place_order(
        self,
        request: PaperOrderRequest,
        *,
        fills_limit: int = 100,
    ) -> PaperOrderActionResult:
        validate_order_request(request)
        state = self._storage.load_or_initialize(self._default_config)
        ensure_unique_client_order_id(state.orders, request.client_order_id)
        self._validate_short_policy(state, request)

        now = utcnow()
        order = new_open_order(
            order_id=generate_order_id(state.next_order_sequence),
            request=request,
            now=now,
        )
        state = replace(
            state,
            orders=tuple(list(state.orders) + [order]),
            next_order_sequence=state.next_order_sequence + 1,
            updated_at=now,
        )

        created_fills: list[PaperFill] = []
        if order.order_type == PaperOrderType.MARKET:
            reference = request.reference_price
            if reference is None:
                reference = state.price_book.get(symbol_key(order.instrument.symbol))
            if reference is None:
                rejected = mark_order_rejected(
                    order,
                    reason="reference_price_required_for_market_fill",
                    now=now,
                )
                state = self._replace_order(state, rejected)
                order = rejected
            else:
                state, order, fill = self._fill_order(
                    state=state,
                    order=order,
                    market_price=reference,
                    now=now,
                )
                created_fills.append(fill)
        else:
            market = request.reference_price
            if market is None:
                market = state.price_book.get(symbol_key(order.instrument.symbol))
            if market is not None and is_limit_marketable(order, market):
                state, order, fill = self._fill_order(
                    state=state,
                    order=order,
                    market_price=market,
                    now=now,
                )
                created_fills.append(fill)

        state = self._revalue_state(state, now)
        self._storage.save_state(state)
        return PaperOrderActionResult(
            order=order,
            fills=tuple(created_fills),
            state=self._snapshot(state, fills_limit=fills_limit),
        )

    def cancel_order(
        self,
        order_id: str,
        *,
        fills_limit: int = 100,
    ) -> PaperCancelActionResult:
        state = self._storage.load_or_initialize(self._default_config)
        order = self._get_order(state.orders, order_id)
        if order.status != PaperOrderStatus.OPEN:
            raise ValueError(f"Only open orders can be cancelled (status={order.status.value})")

        now = utcnow()
        cancelled = mark_order_cancelled(order, now=now)
        state = self._replace_order(state, cancelled)
        state = self._revalue_state(state, now)
        self._storage.save_state(state)
        return PaperCancelActionResult(
            order=cancelled,
            state=self._snapshot(state, fills_limit=fills_limit),
        )

    def process_price_update(
        self,
        update: PriceUpdate,
        *,
        fills_limit: int = 100,
    ) -> PaperPriceUpdateResult:
        if update.price <= 0:
            raise ValueError("Price update must be > 0")

        state = self._storage.load_or_initialize(self._default_config)
        key = symbol_key(update.instrument.symbol)
        price_book = dict(state.price_book)
        price_book[key] = update.price
        state = replace(state, price_book=price_book, updated_at=update.timestamp)

        filled_order_ids: list[str] = []
        open_limits = [
            order
            for order in state.orders
            if order.status == PaperOrderStatus.OPEN
            and order.order_type == PaperOrderType.LIMIT
            and symbol_key(order.instrument.symbol) == key
        ]
        for order in open_limits:
            if is_limit_marketable(order, update.price):
                state, filled_order, _fill = self._fill_order(
                    state=state,
                    order=order,
                    market_price=update.price,
                    now=update.timestamp,
                )
                filled_order_ids.append(filled_order.order_id)

        state = self._revalue_state(state, update.timestamp)
        self._storage.save_state(state)
        return PaperPriceUpdateResult(
            filled_order_ids=tuple(filled_order_ids),
            state=self._snapshot(state, fills_limit=fills_limit),
        )

    def submit_signal_intent(
        self,
        intent: PaperSignalIntent,
        *,
        fills_limit: int = 100,
    ) -> PaperOrderActionResult:
        if intent.quantity <= 0:
            raise ValueError("Signal quantity must be > 0")
        side = (
            PaperOrderSide.BUY
            if intent.direction == PaperSignalDirection.BUY
            else PaperOrderSide.SELL
        )
        request = PaperOrderRequest(
            instrument=intent.instrument,
            side=side,
            order_type=PaperOrderType.MARKET,
            quantity=intent.quantity,
            reference_price=intent.reference_price,
            client_order_id=intent.client_order_id,
            metadata=dict(intent.metadata),
        )
        return self.place_order(request, fills_limit=fills_limit)

    def _fill_order(
        self,
        *,
        state: PaperTradingState,
        order: PaperOrder,
        market_price: float,
        now: datetime,
    ) -> tuple[PaperTradingState, PaperOrder, PaperFill]:
        if order.order_type == PaperOrderType.MARKET:
            comp = compute_market_fill(order=order, base_price=market_price, config=state.config)
        else:
            comp = compute_limit_fill(order=order, config=state.config)

        positions_map = {symbol_key(position.instrument.symbol): position for position in state.positions}
        updated_account, updated_positions, realized_delta = apply_fill_to_account(
            account=state.account,
            positions=positions_map,
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            fill_price=comp.fill_price,
            commission=comp.commission,
            timestamp=now,
        )
        fill = PaperFill(
            fill_id=generate_fill_id(state.next_fill_sequence),
            order_id=order.order_id,
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            fill_price=comp.fill_price,
            notional=abs(order.quantity * comp.fill_price),
            commission=comp.commission,
            spread_cost=comp.spread_cost,
            slippage_cost=comp.slippage_cost,
            realized_pnl_delta=realized_delta,
            timestamp=now,
        )
        filled_order = mark_order_filled(order, fill_price=comp.fill_price, now=now)

        price_book = dict(state.price_book)
        price_book[symbol_key(order.instrument.symbol)] = market_price
        next_state = replace(
            state,
            account=updated_account,
            positions=self._sorted_positions(updated_positions.values()),
            orders=self._replace_order_tuple(state.orders, filled_order),
            fills=tuple(list(state.fills) + [fill]),
            next_fill_sequence=state.next_fill_sequence + 1,
            price_book=price_book,
            updated_at=now,
        )
        return next_state, filled_order, fill

    def _revalue_state(self, state: PaperTradingState, now: datetime) -> PaperTradingState:
        positions_map = {symbol_key(position.instrument.symbol): position for position in state.positions}
        account, positions = mark_to_market(
            account=state.account,
            positions=positions_map,
            price_book=state.price_book,
            timestamp=now,
        )
        return replace(
            state,
            account=account,
            positions=self._sorted_positions(positions.values()),
            updated_at=now,
        )

    @staticmethod
    def _sorted_positions(positions: Iterable) -> tuple:
        return tuple(sorted(positions, key=lambda position: symbol_key(position.instrument.symbol)))

    @staticmethod
    def _replace_order_tuple(orders: tuple[PaperOrder, ...], replacement: PaperOrder) -> tuple[PaperOrder, ...]:
        out = []
        found = False
        for order in orders:
            if order.order_id == replacement.order_id:
                out.append(replacement)
                found = True
            else:
                out.append(order)
        if not found:
            out.append(replacement)
        return tuple(out)

    def _replace_order(self, state: PaperTradingState, replacement: PaperOrder) -> PaperTradingState:
        return replace(
            state,
            orders=self._replace_order_tuple(state.orders, replacement),
            updated_at=replacement.updated_at,
        )

    @staticmethod
    def _get_order(orders: tuple[PaperOrder, ...], order_id: str) -> PaperOrder:
        for order in orders:
            if order.order_id == order_id:
                return order
        raise KeyError(f"Order '{order_id}' not found")

    @staticmethod
    def _snapshot(state: PaperTradingState, *, fills_limit: int) -> PaperStateSnapshot:
        open_orders = tuple(order for order in state.orders if order.status == PaperOrderStatus.OPEN)
        if fills_limit <= 0:
            fills = state.fills
        else:
            fills = state.fills[-fills_limit:]
        return PaperStateSnapshot(
            config=state.config,
            account=state.account,
            positions=state.positions,
            open_orders=open_orders,
            fills=fills,
            price_book=dict(state.price_book),
            updated_at=state.updated_at,
        )

    @staticmethod
    def _validate_short_policy(state: PaperTradingState, request: PaperOrderRequest) -> None:
        if request.side != PaperOrderSide.SELL:
            return
        if state.config.allow_short:
            return
        key = symbol_key(request.instrument.symbol)
        current = 0.0
        for position in state.positions:
            if symbol_key(position.instrument.symbol) == key:
                current = position.quantity
                break
        if current <= 0:
            raise ValueError("Short selling is disabled for this paper account")
        if request.quantity > current:
            raise ValueError("Order would create a short position but short selling is disabled")

