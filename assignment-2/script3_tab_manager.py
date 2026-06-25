import asyncio

from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

URLS = [
    "https://news.ycombinator.com",
    "https://www.bbc.com",
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://www.python.org",
]


async def open_tab(context: BrowserContext, url: str) -> tuple[Page, str]:
    page = await context.new_page()

    try:
        await page.goto(url, timeout=15000)
    except PlaywrightTimeoutError:
        print(f"[Warning] Timed out loading {url}")
        return page, "TIMEOUT"

    try:
        title = await page.title()
    except PlaywrightError as e:
        print(f"[Warning] Could not get title for {url}: {e}")
        return page, "ERROR"

    return page, title


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        print(f"Opening {len(URLS)} tabs in parallel...")
        results: list[tuple[Page, str]] = await asyncio.gather(
            *[open_tab(context, url) for url in URLS]
        )

        pages = [r[0] for r in results]
        titles = [r[1] for r in results]

        print("\n--- Tab Results ---")
        print(f"{'Tab':<5} {'Title':<45} {'URL'}")
        print("-" * 85)
        for i, (url, title) in enumerate(zip(URLS, titles)):
            marker = " (kept)" if i == 0 else ""
            print(f"{i + 1:<5} {title[:44]:<45} {url}{marker}")

        print(f"\nClosing {len(pages) - 1} tabs, keeping tab 1 open...")
        for page in pages[1:]:
            try:
                await page.close()
            except PlaywrightError as e:
                print(f"[Warning] Could not close tab: {e}")

        print(f"Remaining open tab: {titles[0]}")
        await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
