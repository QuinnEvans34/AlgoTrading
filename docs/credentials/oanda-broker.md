# Credential Placeholder: OANDA Broker (Live Execution)

- Service name: OANDA REST Trading API
- Used for: future live broker adapter order submission/account state sync (not enabled in current phase)
- Planned wiring: `src/live_execution/brokers/oanda_stub.py` -> future real `oanda` adapter implementation
- Environment variable placeholders:
  - `LIVE_OANDA_API_TOKEN`
  - `LIVE_OANDA_ACCOUNT_ID`
  - `LIVE_OANDA_ENVIRONMENT`
- Setup status: NOT YET CONFIGURED

## Notes
- Current implementation is stub-only and does not place real orders.
- No real credentials are required for local development or tests in this phase.

