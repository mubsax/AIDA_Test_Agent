"""
save_auth.py

Captures a fully authenticated browser session for the Sibme test agent.

Flow:
  1. Navigate to login page
  2. Enter credentials and submit
  3. Wait for /profile-page (post-login redirect)
  4. Navigate to launchpad (/home/launchpad)
  5. Click the 'Sibme Learning' account tile
  6. Wait for /copilot URL to load
  7. Save full session state to auth.json

The Playwright MCP server loads auth.json on every agent run, placing
the agent directly on the Sibme Copilot conversation — the fixed starting
point for all test cases.

Re-run this script whenever the session expires or credentials change.

Usage:
    python scripts/save_auth.py

Environment variables (optional — script prompts if not set):
    EMAIL           Test account email
    PASSWORD        Test account password
    APP_URL         Base URL of the app (default: https://app.sibme.com)
    AUTH_PATH       Where to save auth.json (default: auth.json)
"""

import os
import getpass
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

APP_URL   = os.environ.get("APP_URL", "https://app.sibme.com")
AUTH_PATH = os.environ.get("AUTH_PATH", "auth.json")

# Login page path
LOGIN_PATH = os.environ.get("LOGIN_PATH", "/home/login")

# Where the app redirects after successful login
POST_LOGIN_PATH = os.environ.get("POST_LOGIN_PATH", "/launchpad")

# Launchpad path — same as post-login redirect for Sibme
LAUNCHPAD_PATH = os.environ.get("LAUNCHPAD_PATH", "/launchpad")

# The account tile to click on the launchpad
TARGET_ACCOUNT = os.environ.get("TARGET_ACCOUNT", "Sibme Learning")

# URL pattern after selecting the account
POST_ACCOUNT_URL_PATTERN = os.environ.get("POST_ACCOUNT_URL_PATTERN", "**/copilot**")

# Timeouts in milliseconds
REDIRECT_TIMEOUT = 15_000   # login → profile-page
ACCOUNT_TIMEOUT  = 20_000   # launchpad → /copilot


# ── Credentials ───────────────────────────────────────────────────────────────

def get_credentials():
    email    = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")

    if not email:
        email = input("Test account email: ").strip()
    if not password:
        password = getpass.getpass("Test account password: ")

    return email, password


# ── Step 1: Login ─────────────────────────────────────────────────────────────

def perform_login(page, email: str, password: str):
    login_url = f"{APP_URL}{LOGIN_PATH}"
    print(f"\n  [1/3] Navigating to login page: {login_url}")
    page.goto(login_url)

    # Locators match your actual login form
    page.get_by_role("textbox", name="Email...").fill(email)
    page.get_by_role("textbox", name="Password...").fill(password)
    page.get_by_role("button",  name="SIGN IN").click()

    print(f"  [1/3] Waiting for redirect to {POST_LOGIN_PATH} ...")
    page.wait_for_url(f"**{POST_LOGIN_PATH}**", timeout=REDIRECT_TIMEOUT)
    print(f"  [1/3] OK Login confirmed -- landed on {page.url}")


# ── Step 2: Select account ────────────────────────────────────────────────────

def select_account(page):
    # Login already lands on /launchpad — no extra navigation needed
    print(f"\n  [2/3] Looking for '{TARGET_ACCOUNT}' account tile ...")

    # Fallback chain — tries three locator strategies in order
    try:
        page.get_by_role("heading", name=TARGET_ACCOUNT).click(timeout=10_000)
    except Exception:
        try:
            page.get_by_role("link", name=TARGET_ACCOUNT).click(timeout=10_000)
        except Exception:
            # Last resort — any visible element with exact matching text
            page.get_by_text(TARGET_ACCOUNT, exact=True).first.click(timeout=10_000)

    print(f"  [2/3] Clicked '{TARGET_ACCOUNT}' — waiting for /copilot ...")
    page.wait_for_url(POST_ACCOUNT_URL_PATTERN, timeout=ACCOUNT_TIMEOUT)
    print(f"  [2/3] OK Landed on: {page.url}")


# ── Step 3: Save session ──────────────────────────────────────────────────────

def save_session(context):
    print(f"\n  [3/3] Saving session state to {AUTH_PATH} ...")
    context.storage_state(path=AUTH_PATH)
    print(f"  [3/3] OK Saved:")
    print(f"         - Cookies  (session, remember-me)")
    print(f"         - localStorage (JWT access token, refresh token)")
    print(f"         - sessionStorage")
    print(f"\n         The Playwright MCP server will restore this state on")
    print(f"         every agent run, starting each test on the Copilot page.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  save_auth.py — Sibme session capture")
    print("=" * 55)

    email, password = get_credentials()

    # Headed locally so you can see the flow and intervene if needed
    # CI=true switches to headless automatically
    headless = os.environ.get("CI", "false").lower() == "true"

    browser_name = os.environ.get("PLAYWRIGHT_BROWSER", "chromium").lower()

    with sync_playwright() as p:
        browser_type = {"chromium": p.chromium, "firefox": p.firefox, "webkit": p.webkit}.get(browser_name)
        if browser_type is None:
            print(f"\n  ERROR: Unknown PLAYWRIGHT_BROWSER value: '{browser_name}'. Use chromium, firefox, or webkit.")
            raise SystemExit(1)
        print(f"\n  Using browser: {browser_name}")
        browser = browser_type.launch(headless=headless)
        context = browser.new_context()
        page    = context.new_page()

        # Step 1 — Login
        try:
            perform_login(page, email, password)
        except Exception as e:
            print(f"\n  ERROR: Login failed: {e}")
            print("     Check your credentials, APP_URL, and the locators in perform_login().")
            browser.close()
            raise SystemExit(1)

        # Step 2 — Navigate to launchpad and select account
        try:
            select_account(page)
        except Exception as e:
            print(f"\n  ERROR: Could not select '{TARGET_ACCOUNT}' account: {e}")
            print("     The tile may use a different label or element type.")
            print("     Open the launchpad manually and inspect the tile element.")
            browser.close()
            raise SystemExit(1)

        # Step 3 — Save session
        save_session(context)
        browser.close()

    print(f"\n  DONE. auth.json is ready for the test agent.")
    print(f"     Remember: auth.json is in .gitignore — never commit it.\n")


if __name__ == "__main__":
    main()