# Research Product Alignment Phase C1

## What the gaps were before this phase
- The home route was still a backend health page rather than a real dashboard.
- There were no dedicated stocks, forex, or asset-detail browsing routes.
- Watchlist and recent-asset persistence existed from B.3, but they were mostly confined to Strategy Lab and ML Lab.
- There was no coherent browsing-to-research handoff into Strategy Lab, ML Lab, or filtered History from the product surface layer.
- Compare already supported deep links, but the broader browsing layer did not surface those paths in a practical way.

## What changed
- The `/` route is now a dashboard focused on research entry points, watchlist continuity, recent assets, saved config snapshots, recent runs, recent compares, and compact system status.
- Added curated frontend-local explorer routes for:
  - `/stocks`
  - `/forex`
  - `/assets/:assetClass/:symbol`
- Added a frontend catalog for curated stock and FX assets with structured profile, filings or macro, performance, and AI research framing.
- Added an asset-detail page that acts as the main research destination with:
  - watchlist toggle
  - recent-asset touch behavior
  - tabs for profile, filings or macro, performance, and AI
  - launch links into Strategy Lab, ML Lab, History, and compare-ready paths where applicable
- Added URL-prefill support so:
  - Strategy Lab reads `symbol`, `assetClass`, `interval`, and optional `configId`
  - ML Lab reads `symbol`, `assetClass`, `interval`, and optional `configId`
  - History reads `q` from the URL so asset detail can deep-link into filtered run history

## How B.3 workflow persistence is now surfaced
- Dashboard now renders persisted watchlist, recent assets, recent compares, and saved-config snapshots.
- Stocks and forex explorers show watchlist-aware interactions directly on browsing cards.
- Asset detail pages persist recent-asset usage and reuse the existing watchlist model rather than inventing a parallel asset-state path.
- Saved configs are surfaced on the dashboard and on asset detail AI tabs, and they can now hand off directly into Strategy Lab or ML Lab through `configId` URL loading.

## Reused and added research-page/backend endpoints
- Reused backend endpoints:
  - `/api/v1/workflow/watchlist`
  - `/api/v1/workflow/recent-assets`
  - `/api/v1/workflow/recent-compares`
  - `/api/v1/workflow/saved-configs`
  - `/api/v1/history/runs`
  - `/api/v1/health`
  - `/api/v1/metadata/capabilities`
  - `/api/v1/market-data/historical-preview`
- No new backend endpoint was added in C1.
- Added frontend-only support code for:
  - curated asset catalog records
  - asset-detail routing and handoff helpers
  - market-data preview client
  - browser smoke scenarios covering dashboard, explorer, and asset-detail flows

## What remains intentionally deferred
- No new backend catalog, profile, filings, or macro content API was introduced.
- Stock and FX detail content still uses curated structured research framing rather than a new ingestion pipeline.
- Performance previews remain constrained by the currently configured provider path; unsupported assets show an explicit unavailable state instead of fake data.
- No paper-trading or live-execution persistence behavior was changed.
- The overall shell and visual system were not broadly redesigned beyond the navigation and research-surface alignment needed for this phase.

## Recommended next follow-up phase
- Add deeper asset intelligence behind the new browsing shell:
  - richer market or profile metadata from a real backend source
  - stronger symbol-level recent-run filtering and compare suggestions
  - expanded dashboard summaries that reuse the same research-first entry-point model without turning the page into a noisy control center

## Validation
- `npm --prefix frontend run build`
- `npm --prefix frontend run smoke`
