"""
Login feature — generated test file (protocol run 2026-06-24-002)
Stories: SIB-login
Docs:    (none on file — no login.md in context_server/docs/)
"""
from playwright.sync_api import Page, expect


def test_valid_login_redirects_to_launchpad(page: Page):
    # Story:   SIB-login — Valid credentials redirect to /launchpad
    # Doc:     (none on file)
    # Bugs:    (none)
    page.goto("https://qa.sibme.com/home/login")
    page.get_by_role("textbox", name="Email...").fill("testinglandingpage9@gmail.com")
    page.get_by_role("textbox", name="Password...").fill("Testinglanding@1")
    page.get_by_role("button", name="SIGN IN").click()
    expect(page).to_have_url("https://qa.sibme.com/home/launchpad")


def test_account_selection_redirects_to_copilot(page: Page):
    # Story:   SIB-login — Account tile selection redirects to /copilot
    # Doc:     (none on file)
    # Bugs:    (none)
    page.goto("https://qa.sibme.com/home/login")
    page.get_by_role("textbox", name="Email...").fill("testinglandingpage9@gmail.com")
    page.get_by_role("textbox", name="Password...").fill("Testinglanding@1")
    page.get_by_role("button", name="SIGN IN").click()
    page.wait_for_url("**/launchpad**")
    page.get_by_text("Sibme Test User").click()
    page.wait_for_url("**/copilot**")
    expect(page).to_have_url("https://qa.sibme.com/home/copilot")


def test_profile_page_content_after_login(page: Page):
    # Story:   SIB-login — Profile page shows user name, Workspace and Huddles links
    # Doc:     (none on file)
    # Bugs:    (none)
    page.goto("https://qa.sibme.com/home/login")
    page.get_by_role("textbox", name="Email...").fill("testinglandingpage9@gmail.com")
    page.get_by_role("textbox", name="Password...").fill("Testinglanding@1")
    page.get_by_role("button", name="SIGN IN").click()
    page.wait_for_url("**/launchpad**")
    page.get_by_text("Sibme Test User").click()
    page.wait_for_url("**/copilot**")
    expect(page.get_by_role("heading", name="Hello, Testing")).to_be_visible()
    expect(page.get_by_role("link", name="Workspace")).to_be_visible()
    expect(page.get_by_role("link", name="Huddles")).to_be_visible()


def test_invalid_credentials_show_error_toast(page: Page):
    # Story:   SIB-login — Invalid credentials show error toast
    # Doc:     (none on file)
    # Bugs:    (none)
    # NOTE: The error toast (class: ngx-toastr toast-error) is outside the ARIA
    # accessibility tree and disappears in ~1s. A MutationObserver captures the
    # toast text at DOM level before it disappears.
    page.goto("https://qa.sibme.com/home/login")

    page.evaluate("""() => {
        window._toastText = null;
        new MutationObserver((mutations) => {
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.nodeType === 1 && node.className &&
                        node.className.includes('toast-error')) {
                        window._toastText = node.innerText.trim();
                    }
                });
            });
        }).observe(document.body, { childList: true, subtree: true });
    }""")

    page.get_by_role("textbox", name="Email...").fill("testinglandingpage9@gmail.com")
    page.get_by_role("textbox", name="Password...").fill("WrongPassword123!")
    page.get_by_role("button", name="SIGN IN").click()
    page.wait_for_timeout(2000)

    toast_text = page.evaluate("() => window._toastText")
    assert toast_text == "The user credentials were incorrect.", (
        f"Expected error toast 'The user credentials were incorrect.', got: {toast_text!r}"
    )
