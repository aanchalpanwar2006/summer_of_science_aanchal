from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from field_scanner import scan_page

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_form.html"


@pytest.fixture
async def page():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        pg = await browser.new_page()
        await pg.goto(f"file://{FIXTURE_PATH}")
        yield pg
        await browser.close()


async def test_detects_all_expected_fields(page):
    result = await scan_page(page)
    labels = {f.label: f for f in result.fields}

    assert len(result.fields) == 9
    assert "Full Name" in labels
    assert "Email" in labels
    assert "Bio" in labels
    assert "Country" in labels
    assert "Gender" in labels
    assert "Hobbies" in labels
    assert "Resume" in labels
    assert "Nested Name" in labels


async def test_element_types_and_options(page):
    result = await scan_page(page)
    labels = {f.label: f for f in result.fields}

    assert labels["Full Name"].element_type == "text"
    assert labels["Full Name"].required is True
    assert labels["Email"].element_type == "email"
    assert labels["Bio"].element_type == "textarea"

    country = labels["Country"]
    assert country.element_type == "select"
    assert {o.value for o in country.options} == {"", "us", "in"}

    gender = labels["Gender"]
    assert gender.element_type == "radio"
    assert {o.value for o in gender.options} == {"male", "female"}

    hobbies = labels["Hobbies"]
    assert hobbies.element_type == "checkbox"
    assert {o.value for o in hobbies.options} == {"reading", "sports"}

    resume = labels["Resume"]
    assert resume.element_type == "file"


async def test_standalone_checkbox_has_no_options(page):
    result = await scan_page(page)
    agree = next(f for f in result.fields if "agree" in f.label.lower())
    assert agree.element_type == "checkbox"
    assert agree.options == []


async def test_iframe_field_resolves_to_non_main_frame(page):
    result = await scan_page(page)
    nested = next(f for f in result.fields if f.label == "Nested Name")
    frame = result.frame_by_field_id[nested.field_id]
    assert frame != page.main_frame


async def test_submit_button_detected(page):
    result = await scan_page(page)
    assert result.submit_field_id is not None
    assert result.submit_field_id in result.frame_by_field_id
