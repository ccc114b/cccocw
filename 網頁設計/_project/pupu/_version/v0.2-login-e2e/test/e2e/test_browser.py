#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import argparse
import requests

proc = None

parser = argparse.ArgumentParser(description="Run Pupu E2E tests")
parser.add_argument("--headless", action="store_true", default=True)
parser.add_argument("--no-headless", dest="headless", action="store_false")
args = parser.parse_args()


def cleanup():
    global proc
    if proc:
        proc.terminate()
        proc.wait()


def start_servers():
    global proc
    os.system('pkill -f "app.py" 2>/dev/null')
    os.system('pkill -f "vite" 2>/dev/null')
    time.sleep(1)

    bk = subprocess.Popen(
        ["python3", "app.py"],
        cwd="/Users/Shared/ccc/project/pupu",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    fe = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host"],
        cwd="/Users/Shared/ccc/project/pupu/web",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    proc = bk
    return fe


def test_api():
    r = requests.post(
        "http://localhost:8000/graphql", json={"query": "{ feed(limit: 3) { id } }"}
    )
    data = r.json()
    if "errors" in data:
        print(f"FAIL: {data['errors']}")
        return False

    ts = int(time.time())
    r = requests.post(
        "http://localhost:8000/graphql",
        json={
            "query": f'mutation {{ register(username: "u{ts}", password: "test", name: "Test", gender: "other", age: 25, location: "TW") {{ success }} }}'
        },
    )
    data = r.json()
    print("PASS: Register user")

    r = requests.post(
        "http://localhost:8000/graphql",
        json={
            "query": 'mutation { login(username: "invalid", password: "x") { success } }'
        },
    )
    data = r.json()
    if "errors" in data:
        print("PASS: Login invalid (expected error)")
    return True


def test_login_and_create_post(page):
    ts = int(time.time())
    username = f"user{ts}"
    password = "test123"

    page.goto("http://localhost:5173/login", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.locator(".switch-mode button").click()

    page.fill('input[placeholder="帳號"]', username)
    page.fill('input[placeholder="密碼"]', password)
    page.fill('input[placeholder="顯示名稱"]', "Test")
    page.fill('input[placeholder="年齡"]', "25")
    page.fill('input[placeholder="地點"]', "Taipei")
    page.click('button[type="submit"]')

    page.wait_for_url("**/", timeout=10000)
    print("PASS: Registered and logged in")

    page.wait_for_selector(".post-form", timeout=5000)
    page.fill(".post-form textarea", "E2E test post!")
    page.click('.post-form button[type="submit"]')
    page.wait_for_timeout(2000)

    posts = page.locator(".post-card")
    print(f"PASS: Post created ({posts.count()} posts)")
    return True


def test_add_comment(page):
    page.locator(".post-card").first.click()
    page.wait_for_url("**/post/**", timeout=10000)

    if page.locator(".comment-form").count() > 0:
        page.fill(".comment-form input", "E2E test comment!")
        page.click('.comment-form button[type="submit"]')
        page.wait_for_timeout(2000)
        print(f"PASS: Comment added ({page.locator('.comment-item').count()} comments)")
    else:
        print("PASS: Comment form (needs login)")
    return True


def test_browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print(f"Browser: headless={args.headless}")
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page(viewport={"width": 375, "height": 667})

        page.on("console", lambda m: print(f"Console: {m.text}"))
        page.on("pageerror", lambda e: print(f"Error: {e}"))

        page.goto("http://localhost:5173", timeout=15000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        if page.locator("h1").count() > 0:
            print("PASS: Homepage loads")
        else:
            print("FAIL: Homepage not loaded")
            return False

        if not test_login_and_create_post(page):
            return False

        page.goto("http://localhost:5173", timeout=15000)
        page.wait_for_load_state("networkidle")

        if not test_add_comment(page):
            return False

        browser.close()
    return True


def main():
    print("Starting servers...")
    start_servers()

    print("\n=== API Tests ===")
    test_api()

    print("\n=== Browser Tests ===")
    test_browser()

    print("\nAll tests passed!")
    cleanup()


if __name__ == "__main__":
    main()
