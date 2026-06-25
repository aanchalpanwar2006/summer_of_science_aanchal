import asyncio
import json
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

FORM_URL = "https://demoqa.com/automation-practice-form"
FORM_DATA_FILE = Path(__file__).parent / "form_data.json"
SCREENSHOT_FILE = Path(__file__).parent / "form_screenshot.png"


async def load_form_data(path: Path) -> dict:
    def _read():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return await asyncio.to_thread(_read)


async def fill_form(page, data: dict) -> None:
    async def safe_fill(selector: str, value: str, label: str) -> None:
        try:
            await page.fill(selector, value)
        except PlaywrightError as e:
            print(f"[Warning] Could not fill '{label}': {e}")

    async def safe_click(selector: str, label: str) -> None:
        try:
            await page.click(selector)
        except PlaywrightError as e:
            print(f"[Warning] Could not click '{label}': {e}")

    await safe_fill("#firstName", data.get("firstName", ""), "First Name")
    await safe_fill("#lastName", data.get("lastName", ""), "Last Name")
    await safe_fill("#userEmail", data.get("email", ""), "Email")

    gender = data.get("gender", "")
    if gender:
        try:
            await page.click(f"label:has-text('{gender}')")
        except PlaywrightError as e:
            print(f"[Warning] Could not select gender '{gender}': {e}")

    await safe_fill("#userNumber", data.get("mobile", ""), "Mobile")

    dob = data.get("dateOfBirth", "")
    if dob:
        try:
            await page.click("#dateOfBirthInput")
            await page.fill("#dateOfBirthInput", dob)
            await page.keyboard.press("Enter")
        except PlaywrightError as e:
            print(f"[Warning] Could not set date of birth: {e}")

    for subject in data.get("subjects", []):
        try:
            await page.fill("#subjectsInput", subject)
            await page.wait_for_selector(".subjects-auto-complete__option", timeout=3000)
            await page.click(".subjects-auto-complete__option:first-child")
        except PlaywrightError as e:
            print(f"[Warning] Could not add subject '{subject}': {e}")

    hobby_map = {"Sports": 1, "Reading": 2, "Music": 3}
    for hobby in data.get("hobbies", []):
        idx = hobby_map.get(hobby)
        if idx:
            await safe_click(f"#hobbies-checkbox-{idx}", f"Hobby: {hobby}")

    picture_path = data.get("picturePath", "")
    if picture_path and Path(picture_path).exists():
        try:
            await page.set_input_files("#uploadPicture", picture_path)
        except PlaywrightError as e:
            print(f"[Warning] Could not upload picture: {e}")

    await safe_fill("#currentAddress", data.get("currentAddress", ""), "Current Address")

    state = data.get("state", "")
    if state:
        try:
            await page.click("#state")
            await page.click(f"#react-select-3-option-0")
        except PlaywrightError as e:
            print(f"[Warning] Could not select state '{state}': {e}")

    city = data.get("city", "")
    if city:
        try:
            await page.click("#city")
            await page.click(f"#react-select-4-option-0")
        except PlaywrightError as e:
            print(f"[Warning] Could not select city '{city}': {e}")


async def main() -> None:
    data = await load_form_data(FORM_DATA_FILE)
    print(f"Loaded form data for: {data.get('firstName')} {data.get('lastName')}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            await page.goto(FORM_URL, timeout=20000)
        except PlaywrightTimeoutError:
            print(f"[Error] Timed out loading {FORM_URL}. Aborting.")
            await browser.close()
            return

        await page.evaluate("window.scrollTo(0, 0)")

        print("Filling form fields...")
        await fill_form(page, data)

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

        print(f"Taking screenshot -> {SCREENSHOT_FILE}")
        await page.screenshot(path=str(SCREENSHOT_FILE), full_page=True)

        try:
            await page.click("#submit")
            print("Form submitted successfully.")
        except PlaywrightError as e:
            print(f"[Warning] Could not click submit: {e}")

        await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
