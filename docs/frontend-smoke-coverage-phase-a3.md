# Frontend Smoke Coverage Phase A3

## Test Framework / Tooling Used
- Browser framework: Playwright via `@playwright/test`
- Runtime model: the existing Vite frontend is started through Playwright `webServer`
- Browser scope: Chromium only
- Backend dependency: none during smoke execution; API calls are intercepted in-browser at `**/api/v1/**`
- Shared support:
  - `frontend/tests/smoke/support/apiMock.ts`
  - `frontend/tests/smoke/support/fixtures.ts`
  - `frontend/tests/smoke/support/testHarness.ts`

## Workflows Covered
- Strategy research page
  - page load
  - capabilities bootstrap
  - key form controls render
  - representative successful submit
  - representative API failure
- ML research page
  - page load
  - key form controls render
  - representative successful submit
  - representative API failure
- Run history page
  - populated history render
  - degraded-but-valid response with warnings
  - compare selection flow from history into compare
  - empty history state
- Compare runs page
  - no-selection state
  - compatible compare success render
  - incompatible/error state
- Paper trading page
  - populated account/order/fill render
  - representative order submit flow
  - empty operational state
  - request failure state
- Settings page
  - safe runtime/settings snapshot render
  - mixed configured / not-configured values
- Live execution page
  - fail-closed readiness render
  - guardrail table render
  - recent attempts render
  - validate intent flow
  - guarded manual submit rejection flow
  - readiness load failure state

## Pages / States Not Fully Covered
- Detail pages under `/runs/:runId/strategy` and `/runs/:runId/ml` are not covered in this phase.
- Settings request-error handling is not separately smoke-tested because the generic alert path is already exercised on multiple other pages.
- Paper cancel flow and price-update flow are not separately covered; the suite currently favors one practical order-submit path plus load/error coverage.
- Live success submission is intentionally not simulated; this phase keeps emphasis on guarded fail-closed behavior and rejection handling.
- History/detail corruption edge cases are still primarily covered at the backend/API level from Phase A.2 rather than through browser-driven detail-page tests.

## How To Run
1. Install frontend dependencies:
   - `npm --prefix frontend install`
2. Install the Playwright browser once per environment:
   - `npx --prefix frontend playwright install chromium`
3. Run the frontend build/typecheck:
   - `npm --prefix frontend run build`
4. Run the smoke suite:
   - `npm --prefix frontend run smoke`
5. Optional headed run for local debugging:
   - `npm --prefix frontend run smoke:headed`

## Selectors / Helpers Introduced
- Minimal accessibility labels were added where the existing markup did not expose stable names:
  - compare selection input and mode select
  - live manual-order inputs/selects/checkbox
  - run-history selection checkboxes
- No broad `data-testid` layer was added.
- `ApiMock` fails closed on unexpected API requests so contract drift becomes a test failure instead of silently passing with partial mocks.
- Typed fixture builders mirror the current frontend contract types, including A.2-style normalized history/compare payload fields such as warnings and partial availability flags.

## Instability / Known Gaps Found
- Some pages reuse identical field labels across multiple forms. The suite scopes those selectors to the intended form rather than adding more UI-only markup.
- Live validation preview is rendered inside a collapsed `<details>` block, so the smoke test expands it before asserting preview content.
- The suite is deliberately smoke-level only. It checks route initialization, representative interactions, and key render states, but it does not attempt exhaustive UI state exploration.

## Post-A.1 / A.2 Alignment
- The smoke suite does not bypass or collapse the A.1 API split.
- History and compare mocks reflect the hardened A.2 behavior by using normalized saved-run fields, warnings, and deterministic compare cards/rows.
- Live execution coverage preserves the existing guarded fail-closed and rejection semantics rather than weakening them for convenience.

## Validation Run
- `npm --prefix frontend run build`
- `npx --prefix frontend playwright install chromium`
- `npm --prefix frontend run smoke`

All of the above passed during implementation.
