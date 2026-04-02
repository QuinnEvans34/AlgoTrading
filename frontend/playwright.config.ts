import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";

const FRONTEND_HOST = "127.0.0.1";
const FRONTEND_PORT = 4173;
const FRONTEND_URL = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;
const ROOT_DIR = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  testDir: "./tests/smoke",
  timeout: 30_000,
  expect: {
    timeout: 5_000
  },
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: FRONTEND_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"]
      }
    }
  ],
  webServer: {
    command: `npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT}`,
    url: FRONTEND_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    cwd: ROOT_DIR
  }
});
