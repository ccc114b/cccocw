import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60000,
  use: {
    headless: true,
    viewport: { width: 375, height: 667 },
    baseURL: 'http://localhost:5173',
  },
  webServer: {
    command: 'npm run dev -- --host',
    port: 5173,
    reuseExistingServer: true,
    timeout: 30000,
  },
});