import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8000/graphql';

function graphql(query) {
  return fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  }).then(r => r.json());
}

test('homepage loads', async ({ page }) => {
  const response = await page.goto(BASE_URL);
  expect(response.status()).toBe(200);
  
  // Wait for React to mount
  await page.waitForFunction(() => {
    const root = document.getElementById('root');
    return root && root.children.length > 0;
  }, { timeout: 10000 });
});

test('h1 visible', async ({ page }) => {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1', { timeout: 15000 });
  const text = await page.locator('h1').textContent();
  expect(text).toBeTruthy();
});

test('posts visible', async ({ page }) => {
  await page.goto(BASE_URL);
  await page.waitForSelector('.post-card', { timeout: 15000 });
  const count = await page.locator('.post-card').count();
  expect(count).toBeGreaterThan(0);
});

test('login page loads', async ({ page }) => {
  await page.goto(BASE_URL + '/login');
  await page.waitForSelector('.auth-form', { timeout: 15000 });
  await expect(page.locator('h2')).toBeVisible();
});

test('API feed works', async () => {
  const result = await graphql('{ feed(limit: 3) { id content author { name } } }');
  expect(result.data?.feed).toBeTruthy();
});

test('API post detail', async () => {
  const result = await graphql('{ post(id: 1) { id content author { name } } }');
  expect(result.data?.post).toBeTruthy();
});

test('API register', async () => {
  const ts = Date.now();
  const result = await graphql(`
    mutation {
      register(username: "u${ts}", password: "test", name: "Test", gender: "other", age: 25, location: "TW") {
        success user { id name }
      }
    }
  `);
  // success or "already exists" is OK
  expect(result.data?.register?.success === true || result.errors?.[0]?.message?.includes('exists')).toBeTruthy();
});

test('API login invalid', async () => {
  const result = await graphql(`mutation { login(username: "notexist", password: "x") { success } }`);
  expect(result.errors).toBeTruthy();
});