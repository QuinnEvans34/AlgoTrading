# Grounded AI Research Phase C2

## Summary

Phase C2 makes the Asset Detail AI tab real.

The implementation adds a user-triggered grounded AI research layer with:

- structured memo generation for stocks and forex
- single-turn prompt-driven research Q&A
- explicit grounding metadata and warnings
- honest degraded behavior when data is missing

This phase does not add chatbot sessions, background generation, or memo persistence.

## Grounding Data Actually Available

The current repo can ground AI outputs with these real inputs:

- shared curated asset catalog metadata from the C1 browsing layer
- DB-primary research run history metadata
- saved research configs from B3 workflow persistence
- provider-backed historical market-data preview when a compatible provider is configured

Current limits that remain real and explicit:

- no live filings backend feed
- no live fundamentals backend feed
- no live macro backend feed
- stock market preview is often unavailable with the current provider stack because the live provider path is forex-oriented

## Stock Memo Grounding Inputs

Stock memos now use:

- shared catalog profile context
- shared catalog filings-focus checklist
- related saved run metadata for the same symbol
- saved strategy and ML configs for the same symbol
- market preview only when a compatible provider actually returns data

If provider-backed stock preview is unavailable, the performance section narrows and the response includes warnings instead of inventing price commentary.

## Forex Memo Grounding Inputs

Forex memos now use:

- shared catalog pair profile context
- shared catalog macro-driver context
- related saved run metadata for the same pair
- saved configs for the same pair
- provider-backed historical candles when available, which is the strongest current real grounding path

If FX preview is unavailable, the memo narrows to catalog and workflow context and says so explicitly.

## API Endpoints Added

Two new endpoints were added under `/api/v1/asset-research`:

- `POST /api/v1/asset-research/memos`
- `POST /api/v1/asset-research/questions`

The backend wiring follows the existing post-A.1 structure:

- domain logic in `src/asset_research/`
- thin API orchestration in `src/api/_services/asset_research_service.py`
- thin routes in `src/api/routes/asset_research.py`

## Output Structure

Memo output is structured, not chat-like.

Stock memo sections:

- Overview
- Recent Price / Performance Context
- Business / Profile Context
- Filing / Fundamental Highlights
- Risks / Open Questions
- Bottom-Line Takeaway

Forex memo sections:

- Overview
- Recent Price / Performance Context
- Macro Context
- Key Drivers
- Risks / Open Questions
- Bottom-Line Takeaway

Question answers are single-turn and grounded.

Both memo and Q&A responses also include:

- `grounding[]`
- `warnings[]`

## Frontend AI Tab Behavior

`AssetDetailPage` now supports:

- `Generate Research Memo` button
- prompt suggestion chips populated from the shared catalog
- one grounded question input
- empty, loading, success, and error states
- structured memo rendering instead of chat transcript rendering

The UI remains user-triggered only. Nothing auto-runs on page load.

## Degraded-Data Behavior

C2 intentionally degrades narrowly when data is weak:

- no compatible market preview: memo still runs, but with explicit narrowed-scope warnings
- no saved configs: memo still runs without template context
- no related runs: memo still runs without run-history context
- missing filings/fundamental/macro feeds: sections explicitly acknowledge that those live feeds are not currently wired
- provider/config not available: endpoints return structured API errors rather than fake content

## Memo Persistence

Memo persistence was intentionally deferred.

C2 is stateless beyond existing watchlist and recent-asset continuity. No memo-history table or saved AI session model was added.

## Validation

The following checks passed:

- `py -3 -m compileall src tests`
- `py -3 -m unittest tests.research.test_asset_research_service tests.api.test_asset_research_endpoints`
- `py -3 -m unittest discover tests`
- `npm --prefix frontend run build`
- `npm --prefix frontend run smoke`
- `py -3 scripts/smoke_check.py` against a temporary local backend

## Recommended Next Phase

The next clean follow-up phase is richer grounding, not broader chat behavior.

Recommended focus:

- real filings and fundamentals ingestion for equities
- real macro/event context for forex
- optional lightweight memo persistence only after those grounding inputs improve
