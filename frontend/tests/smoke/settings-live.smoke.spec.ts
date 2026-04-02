import {
  liveAttemptsResponse,
  liveReadinessResponse,
  liveValidationResponse,
  manualLiveRejectedResponse,
  settingsResponse
} from "./support/fixtures";
import { expect, test } from "./support/testHarness";

test.describe("settings and live execution smoke flows", () => {
  test("renders the settings snapshot and configured state mix", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/settings/system", settingsResponse());

    await page.goto("/settings");

    await expect(page.getByRole("heading", { name: "System Settings" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "System Runtime" })).toBeVisible();
    await expect(page.getByText("capstone-api")).toBeVisible();
    await expect(page.getByText("artifacts/runs")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Feature Flags" })).toBeVisible();
    await expect(page.getByText("live_execution_submit_enabled")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Live Execution Safety" })).toBeVisible();
    await expect(page.getByText("EXECUTE LIVE ORDER")).toBeVisible();
    await expect(page.getByText("No").first()).toBeVisible();
  });

  test("renders guarded live readiness, validation, and rejected manual submit flows", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson(
      "GET",
      "/live-execution/readiness",
      liveReadinessResponse()
    );
    apiMock.onJson(
      "GET",
      "/live-execution/attempts?limit=25",
      liveAttemptsResponse()
    );
    apiMock.onJson(
      "POST",
      "/live-execution/intents/validate",
      liveValidationResponse()
    );
    apiMock.onJson(
      "POST",
      "/live-execution/manual-orders",
      manualLiveRejectedResponse()
    );

    await page.goto("/live-execution");

    await expect(
      page.getByRole("heading", {
        name: "Live Execution (Manual, Strictly Guarded)"
      })
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Live Readiness" })).toBeVisible();
    await expect(
      page.getByText("Live execution is disabled until every guard is satisfied.")
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Guardrail Checks" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "feature_disabled" }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent Live Attempts" })).toBeVisible();
    await expect(page.getByText("attempt-001")).toBeVisible();

    await page.getByLabel("Live Operator ID").fill("operator-7");
    await page.getByLabel("Confirm live execution").check();
    await page.getByLabel("Live Confirmation Text").fill("EXECUTE LIVE ORDER");

    await page.getByRole("button", { name: "Validate Intent" }).click();
    await expect(page.getByRole("heading", { name: "Intent Validation" })).toBeVisible();
    await expect(
      page.getByText(
        "Live execution remains fail-closed until submission is explicitly enabled."
      )
    ).toBeVisible();
    await page.getByText("Payload Preview").click();
    await expect(page.locator("pre.debug-json").first()).toContainText("\"symbol\": \"EUR_USD\"");

    await page.getByRole("button", { name: "Submit Manual Order" }).click();
    await expect(page.getByRole("heading", { name: "Manual Submit Result" })).toBeVisible();
    await expect(page.getByText("manual_confirmation_required")).toBeVisible();
    await expect(
      page.getByText(
        "Manual confirmation phrase did not satisfy guarded live submission requirements."
      )
    ).toBeVisible();
    apiMock.assertCalled("POST /live-execution/intents/validate");
    apiMock.assertCalled("POST /live-execution/manual-orders");
  });

  test("renders live-readiness load failures", async ({ apiMock, page }) => {
    apiMock.onError(
      "GET",
      "/live-execution/readiness",
      503,
      "live_readiness_unavailable",
      "Live execution readiness is temporarily unavailable."
    );
    apiMock.onJson(
      "GET",
      "/live-execution/attempts?limit=25",
      liveAttemptsResponse()
    );

    await page.goto("/live-execution");

    await expect(page.getByRole("alert")).toContainText(
      "API Error: live_readiness_unavailable"
    );
    await expect(page.getByRole("alert")).toContainText(
      "Live execution readiness is temporarily unavailable."
    );
  });
});
