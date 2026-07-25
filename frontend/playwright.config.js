import { defineConfig, devices } from "@playwright/test"
import path from "node:path"
import { fileURLToPath } from "node:url"

const directory = path.dirname(fileURLToPath(import.meta.url))
const repository = path.resolve(directory, "..")
const backend = path.join(repository, "backend")
const documentStorage = path.join(repository, ".local", "playwright-document-storage")

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [["line"]],
  outputDir: "test-results",
  use: {
    baseURL: "http://127.0.0.1:4174",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: [
        "APP_ENV=development",
        "AEROASSIST_DB_MODE=memory",
        "DEMO_AUTH_ENABLED=true",
        "SEED_ON_STARTUP=true",
        "SEED_ENDPOINT_ENABLED=true",
        "READINESS_PUBLIC_MODE=detailed",
        "READINESS_AUTHENTICATED_DETAIL_ENABLED=true",
        "READINESS_INTERNAL_ENABLED=true",
        "CORS_ALLOWED_ORIGINS=http://127.0.0.1:4174",
        `DOCUMENT_EXPORT_STORAGE_DIR=${documentStorage}`,
        "python3 scripts/run_browser_acceptance_server.py",
      ].join(" "),
      cwd: backend,
      url: "http://127.0.0.1:18086/api/health",
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4174",
      cwd: directory,
      env: {
        VITE_API_BASE_URL: "http://127.0.0.1:18086",
      },
      url: "http://127.0.0.1:4174",
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
})
