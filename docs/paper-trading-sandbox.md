# Paper Trading Sandbox Subsystem

## Purpose
This subsystem provides a broker-agnostic simulated account for ongoing paper trading workflows.
It is event-driven (order actions + manual price updates), not historical batch backtesting.

## Architecture
- `src/paper_trading/contracts.py`: canonical account/order/fill/position contracts.
- `src/paper_trading/account.py`: net position, cash, realized/unrealized PnL math.
- `src/paper_trading/orders.py`: order validation + lifecycle state transitions.
- `src/paper_trading/execution.py`: market/limit fill rules and cost application.
- `src/paper_trading/storage.py`: local `state.json` persistence with atomic writes.
- `src/paper_trading/service.py`: orchestration service for order placement, cancel, price updates, reset, and signal intent submit.

## Storage
- Default root: `artifacts/paper_trading` (configurable via `API_DEFAULT_PAPER_TRADING_DIR`).
- File: `state.json`.
- Scope: single-user, single-account local development.

## Fill + Cost Assumptions (Current Phase)
- Market orders:
  - fill immediately using `reference_price` or latest stored mark for symbol.
  - spread/slippage applied as deterministic adverse price adjustment.
- Limit orders:
  - remain open until price touch.
  - fill at limit price.
- Costs:
  - commission supported (`commission_bps`, `commission_fixed`).
  - spread/slippage costs recorded explicitly on fills.

## Order Lifecycle
- `open` -> `filled`
- `open` -> `cancelled`
- `open` -> `rejected`

No partial fills in this phase.

## API Endpoints
- `GET /api/v1/paper/state`
- `POST /api/v1/paper/orders`
- `POST /api/v1/paper/orders/{order_id}/cancel`
- `POST /api/v1/paper/prices`
- `POST /api/v1/paper/signals`
- `POST /api/v1/paper/reset`

## Frontend
- Route: `/paper`
- Supports:
  - account summary
  - order entry (market/limit)
  - price updates
  - open positions
  - open orders (cancel action)
  - recent fills

## Explicitly Deferred
- Live broker integration
- Background/always-on execution loops
- Margin/borrow modeling
- Partial fills and advanced order types
- Multi-user / multi-account auth models

