import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

HN_URL = "https://news.ycombinator.com"
OUTPUT_FILE = Path(__file__).parent / "articles.json"


async def fetch_articles(url: str) -> list[dict]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=15000)
        except PlaywrightTimeoutError:
            print(f"[Error] Timed out loading {url} after 15 seconds.")
            await browser.close()
            return []

        elements = await page.query_selector_all(".titleline > a")

        if not elements:
            await browser.close()
            raise RuntimeError("No articles found — selector may have changed.")

        articles = []
        for i, el in enumerate(elements[:5], start=1):
            title = await el.inner_text()
            href = await el.get_attribute("href") or ""
            articles.append({"rank": i, "title": title, "url": href})

        await browser.close()
        return articles


async def save_to_json(data: list[dict], path: Path) -> None:
    def _write():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    await asyncio.to_thread(_write)
    print(f"Saved {len(data)} articles to {path}")


async def main() -> None:
    print("Fetching top 5 articles from Hacker News...")
    articles = await fetch_articles(HN_URL)

    if not articles:
        print("No articles to save. Exiting.")
        return

    for a in articles:
        print(f"  {a['rank']}. {a['title']}")

    await save_to_json(articles, OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
