import { test as base, expect } from "@playwright/test";

import { ApiMock } from "./apiMock";

export const test = base.extend<{ apiMock: ApiMock }>({
  apiMock: async ({ page }, use) => {
    const apiMock = new ApiMock(page);
    await apiMock.install();
    await use(apiMock);
    apiMock.assertNoUnexpectedRequests();
  }
});

export { expect };
