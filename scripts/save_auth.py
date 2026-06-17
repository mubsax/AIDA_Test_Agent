"""
save_auth.py

Run this script once to capture a logged-in browser session and save it to
auth.json. The Playwright MCP server loads auth.json on every agent run,
so the agent never has to handle login manually.

Re-run whenever the session expires or credentials change.

Usage:
    python scripts/save_auth.py

Environment variables (optional — falls back to prompting if not set):
    EMAIL           Test account email
    PASSWORD        Test account password
    APP_URL         Base URL of the app (defaults to https://app.sibme.com)
    AUTH_PATH       Path to save auth.json (defaults to auth.json)
"""

import os
import getpass
from playwright.sync_api import sync_playwright

# ── Configuration ────────────────────────────────────────────────────────────

APP_URL   = os.environ.get("APP_URL", "https://app.sibme.com")
AUTH_PATH = os.environ.get("AUTH_PATH", "auth.json")

# Login page path — adjust to match your app
LOGIN_PATH = "/home/login"

# Where the app redirects after a successful login — used to confirm success
POST_LOGIN_PATH = "/profile-page"

# How long to wait for the post-login redirect (milliseconds)
REDIRECT_TIMEOUT = 15_000


# ── Credentials ──────────────────────────────────────────────────────────────

def get_credentials():
    email    = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")

    if not email:
        email = input("Test account email: ").strip()
    if not password:
        password = getpass.getpass("Test account password: ")

    return email, password


# ── Login flow ────────────────────────────────────────────────────────────────
#
# Adjust the locators below to match your app's login form.
# The agent uses getByRole locators — prefer those over CSS selectors
# so this script stays resilient to style changes.
#
# Common adjustments:
#   - Change name="Email" / name="Password" to match your field labels
#   - Change name="Sign in" to match your submit button label
#   - If your app uses a username instead of email, update accordingly
#   - If your app has MFA, add the MFA step after the initial submit

def perform_login(page, email: str, password: str):
    login_url = f"{APP_URL}{LOGIN_PATH}"
    print(f"  Navigating to {login_url}")
    page.goto(login_url)

    # Fill email / username
    page.get_by_role("textbox", name="Email...").fill(email)

    # Fill password
    page.get_by_role("textbox", name="Password...").fill(password)

    # Submit
    page.get_by_role("button", name="SIGN IN").click()

    # Wait for redirect to confirm login succeeded
    print(f"  Waiting for redirect to {POST_LOGIN_PATH} ...")
    page.wait_for_url(f"**{POST_LOGIN_PATH}**", timeout=REDIRECT_TIMEOUT)
    print(f"  Login confirmed — landed on {page.url}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  save_auth.py — capturing browser session")
    print("=" * 55)

    email, password = get_credentials()

    with sync_playwright() as p:
        # Run headed so you can see what's happening and intervene if needed
        # Switch to headless=True for CI (set TEST_EMAIL + TEST_PASSWORD as secrets)
        headless = os.environ.get("CI", "false").lower() == "true"

        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page    = context.new_page()

        try:
            perform_login(page, email, password)
        except Exception as e:
            print(f"\n  ❌ Login failed: {e}")
            print("     Check your credentials, APP_URL, and the locators in perform_login().")
            browser.close()
            raise SystemExit(1)

        # Save full session state:
        # - Cookies (session cookie, remember-me cookie, etc.)
        # - localStorage (JWT access token, refresh token, user prefs, etc.)
        # - sessionStorage
        context.storage_state(path=AUTH_PATH)
        browser.close()

    print(f"\n  ✅ Session saved to {AUTH_PATH}")
    print("     Add auth.json to .gitignore — it contains sensitive tokens.")
    print("     Re-run this script when the session expires.")


if __name__ == "__main__":
    main()