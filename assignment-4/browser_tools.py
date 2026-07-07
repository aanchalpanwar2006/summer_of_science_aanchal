import json
from pathlib import Path

from langchain_core.tools import tool
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

_pw = None
_browser = None
_page: Page | None = None

USER_PROFILE_PATH = Path(__file__).parent / "user_profile.json"


async def init_browser() -> None:
    global _pw, _browser, _page
    _pw = await async_playwright().start()
    _browser = await _pw.chromium.launch(headless=False)
    _page = await _browser.new_page()


async def close_browser() -> None:
    global _pw, _browser, _page
    if _browser:
        await _browser.close()
    if _pw:
        await _pw.stop()
    _browser = _page = _pw = None


async def get_page() -> Page:
    global _pw, _browser, _page
    if _page is None:
        await init_browser()
    return _page


@tool
async def navigate_to(url: str) -> str:
    """Navigate the browser to a URL and return the page title.
    Use full URLs including https:// (e.g. https://google.com)."""
    page = await get_page()
    try:
        await page.goto(url, timeout=15000)
        title = await page.title()
        return f"Navigated to {url}. Page title: '{title}'"
    except PlaywrightTimeoutError:
        return f"Error: Timed out loading {url} after 15 seconds."
    except PlaywrightError as e:
        return f"Error: Could not navigate to {url} — {e}"


@tool
async def click_element(selector: str) -> str:
    """Click a page element identified by a CSS selector.
    Example selectors: 'button#submit', 'a.nav-link', 'input[name=q]'."""
    page = await get_page()
    try:
        await page.click(selector, timeout=5000)
        return f"Clicked element '{selector}' successfully."
    except PlaywrightTimeoutError:
        return f"Error: Element '{selector}' did not appear within 5 seconds."
    except PlaywrightError as e:
        return f"Error: Could not click '{selector}' — {e}"


@tool
async def type_text(selector: str, text: str) -> str:
    """Fill a text field identified by a CSS selector with the given text.
    Clears any existing content before typing.
    Example: selector='input[name=q]', text='AI news'."""
    page = await get_page()
    try:
        await page.fill(selector, text)
        return f"Typed '{text}' into '{selector}'."
    except PlaywrightTimeoutError:
        return f"Error: Field '{selector}' did not appear within the timeout."
    except PlaywrightError as e:
        return f"Error: Could not type into '{selector}' — {e}"


@tool
def get_user_profile(field: str) -> str:
    """Read a field from the local user profile store.
    Available fields: name, email, phone, resume_path.
    Pass field='all' to return the full profile as JSON."""
    try:
        with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
    except FileNotFoundError:
        return "Error: user_profile.json not found."

    if field == "all":
        return json.dumps(data, indent=2)

    value = data.get(field)
    if value is None:
        return f"Field '{field}' not found. Available fields: {list(data.keys())}"
    return str(value)
