# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: app.spec.ts >> posts visible
- Location: tests/app.spec.ts:32:1

# Error details

```
Error: page.waitForSelector: Target page, context or browser has been closed
Call log:
  - waiting for locator('.post-card') to be visible

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const BASE_URL = 'http://localhost:5173';
  4  | const API_URL = 'http://localhost:8000/graphql';
  5  | 
  6  | function graphql(query) {
  7  |   return fetch(API_URL, {
  8  |     method: 'POST',
  9  |     headers: { 'Content-Type': 'application/json' },
  10 |     body: JSON.stringify({ query }),
  11 |   }).then(r => r.json());
  12 | }
  13 | 
  14 | test('homepage loads', async ({ page }) => {
  15 |   const response = await page.goto(BASE_URL);
  16 |   expect(response.status()).toBe(200);
  17 |   
  18 |   // Wait for React to mount
  19 |   await page.waitForFunction(() => {
  20 |     const root = document.getElementById('root');
  21 |     return root && root.children.length > 0;
  22 |   }, { timeout: 10000 });
  23 | });
  24 | 
  25 | test('h1 visible', async ({ page }) => {
  26 |   await page.goto(BASE_URL);
  27 |   await page.waitForSelector('h1', { timeout: 15000 });
  28 |   const text = await page.locator('h1').textContent();
  29 |   expect(text).toBeTruthy();
  30 | });
  31 | 
  32 | test('posts visible', async ({ page }) => {
  33 |   await page.goto(BASE_URL);
> 34 |   await page.waitForSelector('.post-card', { timeout: 15000 });
     |              ^ Error: page.waitForSelector: Target page, context or browser has been closed
  35 |   const count = await page.locator('.post-card').count();
  36 |   expect(count).toBeGreaterThan(0);
  37 | });
  38 | 
  39 | test('login page loads', async ({ page }) => {
  40 |   await page.goto(BASE_URL + '/login');
  41 |   await page.waitForSelector('.auth-form', { timeout: 15000 });
  42 |   await expect(page.locator('h2')).toBeVisible();
  43 | });
  44 | 
  45 | test('API feed works', async () => {
  46 |   const result = await graphql('{ feed(limit: 3) { id content author { name } } }');
  47 |   expect(result.data?.feed).toBeTruthy();
  48 | });
  49 | 
  50 | test('API post detail', async () => {
  51 |   const result = await graphql('{ post(id: 1) { id content author { name } } }');
  52 |   expect(result.data?.post).toBeTruthy();
  53 | });
  54 | 
  55 | test('API register', async () => {
  56 |   const ts = Date.now();
  57 |   const result = await graphql(`
  58 |     mutation {
  59 |       register(username: "u${ts}", password: "test", name: "Test", gender: "other", age: 25, location: "TW") {
  60 |         success user { id name }
  61 |       }
  62 |     }
  63 |   `);
  64 |   // success or "already exists" is OK
  65 |   expect(result.data?.register?.success === true || result.errors?.[0]?.message?.includes('exists')).toBeTruthy();
  66 | });
  67 | 
  68 | test('API login invalid', async () => {
  69 |   const result = await graphql(`mutation { login(username: "notexist", password: "x") { success } }`);
  70 |   expect(result.errors).toBeTruthy();
  71 | });
```