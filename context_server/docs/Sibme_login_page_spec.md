# Business Rules: Sibme Login

## Page Identity

- **URL:** `app.sibme.com/home/login`
- **Purpose:** Primary authentication entry point. Supports email/password login and three SSO providers (Google, Microsoft, Enterprise SSO).

---

## Elements

| Element | Business Rule |
|---|---|
| Page heading | "Login to Sibme" — translates with the selected locale |
| Email field | Accepts a valid email address OR a username. If the user has not set a custom username, their username defaults to their email address. |
| Password field | Masked by default. Has a show/hide toggle (eye icon) on the right side that switches the field between masked and plain text. |
| Sign In button | Disabled when either field is empty. Becomes active when both fields contain any non-empty string. No client-side format validation — intentional, because usernames can be non-email-formatted. |
| Remember me checkbox | Unchecked by default. Behaviour (session duration) TBD — not yet specced. |
| Forgot Password? link | Navigates to the password reset flow. |
| Sign in with Google | Initiates OAuth flow — redirects to `accounts.google.com`. |
| Sign in with Microsoft | Initiates OAuth flow — redirects to `login.microsoftonline.com`. |
| Sign in with SSO | Opens a modal dialog titled "Sign in with SSO" containing an email input field and SIGN IN / Close buttons. |
| Consent text | Static text: "By Signing in I agree to the [Privacy Policy] and [Terms of Use.]" |
| Privacy Policy link | Opens `sibme.com/privacy-policy` in a new tab. |
| Terms of Use link | Opens `sibme.com/terms-of-service` in a new tab. |
| Language selector | Switches page locale. Supported: English (default), Spanish. All visible text — headings, labels, buttons, links, consent text — translates with the selection. |

---

## Post-Login Routing Rules

After successful login, the redirect destination depends on the user's account state:

| Condition | Redirect destination |
|---|---|
| User is active in more than one account | `/home/launchpad` (account selection screen) |
| User is active in exactly one account AND that account has Engage/New view enabled | `/home/copilot` |
| User is active in exactly one account AND that account has Classic view enabled | `/home/profile-page` |

After selecting an account on the launchpad, the same Engage vs Classic routing applies.

---

## Credential Rules

- The email field accepts either a valid email address or a username.
- If a user has not set a custom username, their username is their email address by default.
- A user with a custom username can authenticate using the username in place of their email.
- Wrong password, non-existent email, and non-existent username all return the same toast: **"The user credentials were incorrect."** — this is intentional to prevent user enumeration.
- On any credential failure, the URL remains `/home/login` and no redirect occurs.
- A non-email-formatted string that is not a recognised username will be submitted to the server (the Sign In button does not gate on format) and the server will return the same credentials toast.

---

## SSO Rules

- **Google:** Clicking "Sign in with Google" redirects to `accounts.google.com` (Google OAuth consent domain).
- **Microsoft:** Clicking "Sign in with Microsoft" redirects to `login.microsoftonline.com` (Microsoft identity platform).
- **Enterprise SSO:** Clicking "Sign in with SSO" opens an in-page modal dialog with an email input. The user enters their organisation email to initiate the SAML/enterprise flow.

---

## Session Rules

- **Already authenticated:** If a user with a valid active session navigates to `/home/login`, they are immediately redirected away without seeing the login form. Redirect destination follows the post-login routing rules above (observed: `/home/copilot` for Engage view).
- **Remember me:** Behaviour (session duration, cookie/token lifetime) not yet specced — treat as TBD.