# Reference Repo Setup (Audit Preparation)

This repository is the clean base for the new capstone platform.

## Temporary donor/reference clone

- Reference repo: `https://github.com/QuinnEvans34/forex_signal_scanner.git`
- Local path: `legacy_reference/forex_signal_scanner`
- Pinned commit: `bc365a92453b55d7ea34971d96e3af949ea727c7`

## Why this exists

The cloned forex repo is present only as temporary donor/reference material for inspection and audit. It is not part of the new platform source tree, and it should not define the new architecture.

## Scope boundary

- Build the new capstone platform in this clean repo.
- Do not merge or refactor the donor repo into the new app during setup.
- Reuse only audited subsystems that are explicitly selected for migration later.

## Next step

Run a structured audit of reusable subsystems (for example: backtesting, execution/broker integration, signal logic, data adapters, training helpers, metrics, and configuration handling) before any migration work.
