"""Minimal demo: initialize paper account, place orders, and process fills."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, Instrument  # noqa: E402
from paper_trading import (  # noqa: E402
    PaperAccountConfig,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderType,
    PaperTradingService,
    PaperTradingStorage,
    PriceUpdate,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        service = PaperTradingService(
            storage=PaperTradingStorage(Path(tempdir)),
            default_config=PaperAccountConfig(
                initial_cash=100_000.0,
                allow_short=False,
                default_spread_bps=0.5,
                default_slippage_bps=0.5,
            ),
        )
        instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)

        print("Initial State")
        print("-------------")
        initial = service.get_state()
        print(
            f"cash={initial.account.cash:.2f} equity={initial.account.equity:.2f} "
            f"positions={len(initial.positions)} open_orders={len(initial.open_orders)}"
        )

        entry = service.place_order(
            PaperOrderRequest(
                instrument=instrument,
                side=PaperOrderSide.BUY,
                order_type=PaperOrderType.MARKET,
                quantity=10.0,
                reference_price=100.0,
            )
        )
        print()
        print("After Market Buy")
        print("----------------")
        print(
            f"order_status={entry.order.status.value} fills={len(entry.fills)} "
            f"cash={entry.state.account.cash:.2f} realized={entry.state.account.realized_pnl:.2f}"
        )

        limit = service.place_order(
            PaperOrderRequest(
                instrument=instrument,
                side=PaperOrderSide.SELL,
                order_type=PaperOrderType.LIMIT,
                quantity=10.0,
                limit_price=105.0,
            )
        )
        print()
        print("After Limit Sell Submit")
        print("-----------------------")
        print(
            f"order_status={limit.order.status.value} open_orders={len(limit.state.open_orders)}"
        )

        update = service.process_price_update(
            PriceUpdate(instrument=instrument, price=105.0)
        )
        print()
        print("After Price Update")
        print("------------------")
        print(
            f"filled_orders={list(update.filled_order_ids)} "
            f"cash={update.state.account.cash:.2f} "
            f"realized={update.state.account.realized_pnl:.2f} "
            f"positions={len(update.state.positions)}"
        )


if __name__ == "__main__":
    main()

