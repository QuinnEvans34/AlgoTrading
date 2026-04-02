import { paperStateResponse } from "./support/fixtures";
import { expect, test } from "./support/testHarness";

test.describe("paper trading smoke flows", () => {
  test("renders account data and submits a representative paper order", async ({
    apiMock,
    page
  }) => {
    const initialState = paperStateResponse();
    const nextState = paperStateResponse({
      open_orders: [
        ...initialState.open_orders,
        {
          order_id: "ord-200",
          instrument: {
            symbol: "NVDA",
            asset_class: "stock"
          },
          side: "buy",
          order_type: "limit",
          quantity: 3,
          status: "open",
          created_at: "2026-03-26T12:05:00.000Z",
          updated_at: "2026-03-26T12:05:00.000Z",
          limit_price: 920,
          reference_price: 919.5,
          client_order_id: "cli-200",
          rejection_reason: null,
          filled_quantity: 0,
          average_fill_price: null,
          metadata: {}
        }
      ]
    });

    apiMock.onJson("GET", "/paper/state?fills_limit=200", initialState);
    apiMock.onJson("POST", "/paper/orders", {
      order: nextState.open_orders[1],
      fills: [],
      state: nextState
    });

    await page.goto("/paper");

    await expect(page.getByRole("heading", { name: "Paper Trading Sandbox" })).toBeVisible();
    await expect(page.getByText("paper-main")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Open Orders" })).toBeVisible();
    await expect(page.getByText("ord-100")).toBeVisible();
    await expect(page.getByText("fill-100")).toBeVisible();

    const orderForm = page
      .locator("form")
      .filter({ has: page.getByRole("heading", { name: "Place Paper Order" }) });

    await orderForm.getByLabel("Symbol").fill("NVDA");
    await orderForm.getByLabel("Order Type").selectOption("limit");
    await orderForm.getByLabel("Quantity").fill("3");
    await orderForm.getByLabel("Limit Price").fill("920");
    await orderForm.getByLabel("Client Order ID (optional)").fill("cli-200");
    await page.getByRole("button", { name: "Submit Order" }).click();

    await expect(page.getByText("ord-200")).toBeVisible();
    await expect(page.getByText("NVDA")).toBeVisible();
    apiMock.assertCalled("POST /paper/orders");
  });

  test("renders the empty operational paper state cleanly", async ({ apiMock, page }) => {
    apiMock.onJson(
      "GET",
      "/paper/state?fills_limit=200",
      paperStateResponse({
        positions: [],
        open_orders: [],
        fills: []
      })
    );

    await page.goto("/paper");

    await expect(page.getByText("No open positions.")).toBeVisible();
    await expect(page.getByText("No open orders.")).toBeVisible();
    await expect(page.getByText("No fills yet.")).toBeVisible();
  });

  test("renders paper-state request failures", async ({ apiMock, page }) => {
    apiMock.onError(
      "GET",
      "/paper/state?fills_limit=200",
      503,
      "paper_unavailable",
      "Paper trading state is temporarily unavailable."
    );

    await page.goto("/paper");

    await expect(page.getByRole("alert")).toContainText("API Error: paper_unavailable");
    await expect(page.getByRole("alert")).toContainText(
      "Paper trading state is temporarily unavailable."
    );
  });
});
