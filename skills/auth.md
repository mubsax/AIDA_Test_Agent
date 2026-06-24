# Skill: Authentication

## When to use this skill
Read this file before any test cycle, or any time a session error (401, redirect
to /login) occurs mid-test.

## Session strategy
Auth is session-based with JWT access tokens and refresh tokens.
A valid session is pre-loaded via `auth.json` — do NOT attempt to log in
manually unless `auth.json` is missing or expired.

## Steps

### Happy path (auth.json exists and is valid)
1. Check that `auth.json` exists and is non-empty.
2. Load it as Playwright storage state — do not navigate to /login.
3. Proceed directly to the feature under test.

### Fresh login (auth.json missing or expired)
1. Run `python scripts/save_auth.py` — this performs the full login flow and
   writes a fresh `auth.json`.
2. After the script completes, verify `auth.json` is non-empty before continuing.

### Manual login fallback (save_auth.py unavailable)
1. Navigate to the app Base URL (read from `.env`).
2. Enter credentials and submit.
3. Detect landing on `/launchpad`.
4. Click the `<TARGET_ACCOUNT>` tile — read the account name from `.env`.
5. Wait for redirect to `/copilot` before proceeding with any test steps.

## Important rules
- Always confirm the active account matches `TARGET_ACCOUNT` from `.env`
  before running any test. Account context affects Library, Copilot, and
  Goals visibility.
- If a mid-test 401 occurs, stop the test, re-run `save_auth.py`, and
  restart the cycle from step 1. Do not attempt to continue with a broken session.
- Never hardcode credentials. Read all auth values from `.env`.