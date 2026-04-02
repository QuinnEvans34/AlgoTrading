# Workflow Persistence Phase B3

## Summary

Phase B3 adds the first persistent product workflow objects beyond saved runs:

- saved strategy configurations
- saved ML configurations
- one shared watchlist for research assets
- recent assets
- recent compare selections

This phase keeps the existing run system intact:

- saved configs are reusable templates
- saved runs remain executed research results
- history/detail/compare keep their current artifact-backed behavior

## Which Workflow Objects Were Chosen And Why

### Saved Research Configs

Chosen because the Strategy Lab and ML Lab already expose stable request shapes and are the highest-value repeated operator workflows in the product.

This phase supports:

- save current Strategy form state as a reusable template
- save current ML form state as a reusable template
- list saved templates
- load a saved template back into the page form
- update an already loaded template
- delete an obsolete template

### Watchlist

Chosen instead of separate favorites and watchlists to avoid overlapping concepts.

This phase uses one clean persistent watchlist model for research assets. The same list is reused by Strategy and ML pages.

### Recents

Chosen because they add continuity without introducing a large preference system.

This phase persists:

- recent assets touched by successful Strategy or ML runs
- recent compare selections touched by successful compare loads

## Schema / Tables Introduced

Added in migration [0003_workflow_persistence_objects.py](/c:/Users/quinn/Desktop/CapstoneProject/alembic/versions/0003_workflow_persistence_objects.py):

- `saved_research_configs`
- `watchlist_items`
- `recent_assets`
- `recent_compare_sets`

The SQLAlchemy models already lived in [models.py](/c:/Users/quinn/Desktop/CapstoneProject/src/persistence/models.py); this phase wires them through a real repository and API surface.

## Persistence Design

### Saved Configs

Implemented in [workflow_objects.py](/c:/Users/quinn/Desktop/CapstoneProject/src/persistence/workflow_objects.py) and exposed through [workflow_service.py](/c:/Users/quinn/Desktop/CapstoneProject/src/api/_services/workflow_service.py).

Saved configs store:

- stable `id`
- `config_type` of `strategy` or `ml`
- user-visible `name`
- optional `description`
- `config_schema_version`
- controlled JSON `payload_json`
- listing helpers: `instrument_symbol`, `asset_class`, `interval`
- `created_at`, `updated_at`, `last_used_at`

### Watchlist

`watchlist_items` stores:

- stable `id`
- `symbol`
- `asset_class`
- optional `source_context`
- `created_at`, `updated_at`

It uses a unique constraint on `(symbol, asset_class)` so repeated add actions remain idempotent.

### Recent Assets

`recent_assets` stores:

- stable `id`
- `symbol`
- `asset_class`
- optional `source_context`
- `last_used_at`
- `created_at`, `updated_at`

It also dedupes by `(symbol, asset_class)`.

### Recent Compare Sets

`recent_compare_sets` stores:

- stable `id`
- deterministic `fingerprint`
- `compare_mode`
- ordered `run_ids_json`
- `last_used_at`
- `created_at`, `updated_at`

The fingerprint is derived from compare mode plus ordered run IDs, so different orderings remain distinct on purpose.

## API Endpoints / Resources Added

New route family: [workflow.py](/c:/Users/quinn/Desktop/CapstoneProject/src/api/routes/workflow.py)

- `GET /api/v1/workflow/saved-configs`
- `POST /api/v1/workflow/saved-configs`
- `GET /api/v1/workflow/saved-configs/{config_id}`
- `PUT /api/v1/workflow/saved-configs/{config_id}`
- `DELETE /api/v1/workflow/saved-configs/{config_id}`
- `GET /api/v1/workflow/watchlist`
- `POST /api/v1/workflow/watchlist/items`
- `DELETE /api/v1/workflow/watchlist/items/{asset_class}/{symbol}`
- `GET /api/v1/workflow/recent-assets`
- `POST /api/v1/workflow/recent-assets/touch`
- `GET /api/v1/workflow/recent-compares`
- `POST /api/v1/workflow/recent-compares/touch`

These are wired through the existing API facade in [services.py](/c:/Users/quinn/Desktop/CapstoneProject/src/api/services.py) and dependency wiring in [dependencies.py](/c:/Users/quinn/Desktop/CapstoneProject/src/api/dependencies.py).

## Frontend Entry Points Added

### Strategy Page

[StrategyRunPage.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/pages/StrategyRunPage.tsx)

Added:

- page-owned draft state
- Strategy Config Library panel
- watchlist panel
- recent assets panel

### ML Page

[MLRunPage.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/pages/MLRunPage.tsx)

Added:

- page-owned draft state
- ML Config Library panel
- shared watchlist panel
- recent assets panel

### Compare Page

[CompareRunsPage.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/pages/CompareRunsPage.tsx)

Added:

- recent compare list
- recent compare touch after successful compare
- reuse-selection action

### Shared Frontend Workflow Layer

New frontend workflow modules:

- [api.ts](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/lib/workflow/api.ts)
- [types.ts](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/lib/workflow/types.ts)
- [drafts.ts](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/lib/workflow/drafts.ts)

Shared UI panels:

- [ConfigLibraryPanel.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/components/workflow/ConfigLibraryPanel.tsx)
- [AssetWorkflowPanel.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/components/workflow/AssetWorkflowPanel.tsx)
- [RecentComparePanel.tsx](/c:/Users/quinn/Desktop/CapstoneProject/frontend/src/components/workflow/RecentComparePanel.tsx)

## Saved Configs Vs Saved Runs

They are now explicitly separate:

- saved configs are editable input templates for future runs
- saved runs are immutable executed results discovered through history/detail/compare

Saved configs do not replace:

- run artifacts
- run history
- run compare inputs
- result detail payloads

## Watchlist / Favorites Model Choice

This phase intentionally implements one watchlist model and does not add a second favorites concept.

Reason:

- the current product does not have enough differentiated UI behavior to justify both
- one list is easier to persist, reason about, and reuse across Strategy and ML
- it avoids future cleanup of overlapping concepts

## Payload Compatibility / Versioning

Saved configs use controlled JSON payloads with `config_schema_version = 1`.

Reason for JSON rather than normalized config tables:

- Strategy and ML request shapes are nested
- they are already natural request-template payloads
- they are more likely to evolve than the database schema should
- extracted listing fields still make list views efficient

Version compatibility rules in this phase:

- only schema version `1` is accepted for writes
- backend validates and normalizes payloads before persistence
- backend revalidates payloads on read and treats corrupt rows as errors instead of silently returning bad shapes

The saved config payload intentionally stores a research template, not a raw executed request. For inline sample data, configs store `inline_sample` with `inline_bars` instead of full generated candle arrays.

## What Was Intentionally Deferred

- multi-user/auth ownership
- multiple named watchlists
- tags, notes search, and richer config organization
- persistence for paper trading workflows
- persistence for live execution workflows
- moving run detail payloads into Postgres
- broader preference/profile persistence

## Validation Coverage Added

Backend:

- [test_workflow_repository.py](/c:/Users/quinn/Desktop/CapstoneProject/tests/persistence/test_workflow_repository.py)
- [test_workflow_endpoints.py](/c:/Users/quinn/Desktop/CapstoneProject/tests/api/test_workflow_endpoints.py)

Frontend smoke:

- [research.smoke.spec.ts](/c:/Users/quinn/Desktop/CapstoneProject/frontend/tests/smoke/research.smoke.spec.ts)
- [history-compare.smoke.spec.ts](/c:/Users/quinn/Desktop/CapstoneProject/frontend/tests/smoke/history-compare.smoke.spec.ts)

Validation run for this phase:

- `py -3 -m compileall src tests`
- `py -3 -m unittest tests.persistence.test_workflow_repository`
- `py -3 -m unittest tests.api.test_workflow_endpoints`
- `py -3 -m unittest discover tests`
- `npm --prefix frontend run build`
- `npm --prefix frontend run smoke`
- `py -3 scripts/smoke_check.py` against a temporary local backend

All of the above passed.

## Recommended Next Follow-Up Phase

The next clean follow-up is a user/session foundation phase:

- introduce a lightweight workspace-user or authenticated-user ownership model
- scope saved configs, watchlists, and recents to that owner
- add migration paths from the current single-workspace context
- then decide whether paper/live continuity objects belong in the same model or a separate operational persistence boundary
