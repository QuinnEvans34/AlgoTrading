"""Order validation and lifecycle transitions for paper trading."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Iterable

from .contracts import (
    PaperOrder,
    PaperOrderRequest,
    PaperOrderStatus,
    PaperOrderType,
)


def generate_order_id(sequence: int) -> str:
    return f"paper-order-{sequence:08d}"


def generate_fill_id(sequence: int) -> str:
    return f"paper-fill-{sequence:08d}"


def validate_order_request(request: PaperOrderRequest) -> None:
    if request.quantity <= 0:
        raise ValueError("Order quantity must be > 0")
    if request.order_type == PaperOrderType.LIMIT:
        if request.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if request.limit_price <= 0:
            raise ValueError("limit_price must be > 0")
    if request.reference_price is not None and request.reference_price <= 0:
        raise ValueError("reference_price must be > 0 when provided")
    if request.client_order_id is not None and request.client_order_id.strip() == "":
        raise ValueError("client_order_id cannot be empty when provided")
    if request.instrument.symbol.strip() == "":
        raise ValueError("instrument.symbol cannot be empty")


def ensure_unique_client_order_id(
    orders: Iterable[PaperOrder],
    client_order_id: str | None,
) -> None:
    if client_order_id is None:
        return
    for order in orders:
        if order.client_order_id == client_order_id:
            raise ValueError(f"Duplicate client_order_id '{client_order_id}'")


def new_open_order(
    *,
    order_id: str,
    request: PaperOrderRequest,
    now: datetime,
) -> PaperOrder:
    return PaperOrder(
        order_id=order_id,
        instrument=request.instrument,
        side=request.side,
        order_type=request.order_type,
        quantity=request.quantity,
        status=PaperOrderStatus.OPEN,
        created_at=now,
        updated_at=now,
        limit_price=request.limit_price,
        reference_price=request.reference_price,
        client_order_id=request.client_order_id,
        metadata=dict(request.metadata),
    )


def mark_order_filled(
    order: PaperOrder,
    *,
    fill_price: float,
    now: datetime,
) -> PaperOrder:
    return replace(
        order,
        status=PaperOrderStatus.FILLED,
        filled_quantity=order.quantity,
        average_fill_price=fill_price,
        updated_at=now,
        rejection_reason=None,
    )


def mark_order_rejected(order: PaperOrder, *, reason: str, now: datetime) -> PaperOrder:
    return replace(
        order,
        status=PaperOrderStatus.REJECTED,
        rejection_reason=reason,
        updated_at=now,
    )


def mark_order_cancelled(order: PaperOrder, *, now: datetime) -> PaperOrder:
    return replace(
        order,
        status=PaperOrderStatus.CANCELLED,
        updated_at=now,
    )

