import os
from typing import Optional

from playwright.async_api import Browser, Page, Playwright, async_playwright

_pw: Optional[Playwright] = None
_browser: Optional[Browser] = None


async def init_browser() -> None:
    global _pw, _browser
    _pw = await async_playwright().start()
    headless = os.environ.get("HEADLESS", "false").lower() == "true"
    _browser = await _pw.chromium.launch(headless=headless)


async def close_browser() -> None:
    global _pw, _browser
    if _browser:
        await _browser.close()
    if _pw:
        await _pw.stop()
    _browser = None
    _pw = None


async def new_page() -> Page:
    if _browser is None:
        raise RuntimeError("Browser not initialized — call init_browser() first.")
    return await _browser.new_page()
