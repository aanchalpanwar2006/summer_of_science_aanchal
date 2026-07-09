from typing import Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Frame

from models import FormField


async def fill_and_submit(
    fields: list[FormField],
    frame_by_field_id: dict[str, Frame],
    submit_field_id: Optional[str],
) -> None:
    for field in fields:
        frame = frame_by_field_id.get(field.field_id)
        if frame is None or not field.proposed_value:
            continue

        locator = frame.locator(f'[data-agent-field-id="{field.field_id}"]')
        try:
            if field.element_type == "file":
                await locator.first.set_input_files(field.proposed_value)

            elif field.element_type == "select":
                await locator.first.select_option(field.proposed_value)

            elif field.element_type == "checkbox" and field.options:
                selected = {v.strip() for v in field.proposed_value.split(",") if v.strip()}
                for opt in field.options:
                    opt_locator = frame.locator(
                        f'[data-agent-field-id="{field.field_id}"]'
                        f'[data-agent-option-value="{opt.value}"]'
                    )
                    is_checked = await opt_locator.first.is_checked()
                    should_check = opt.value in selected
                    if should_check != is_checked:
                        await opt_locator.first.click()

            elif field.element_type == "checkbox":
                should_check = field.proposed_value.strip().lower() in ("true", "yes", "1", "on")
                is_checked = await locator.first.is_checked()
                if should_check != is_checked:
                    await locator.first.click()

            elif field.element_type == "radio":
                opt_locator = frame.locator(
                    f'[data-agent-field-id="{field.field_id}"]'
                    f'[data-agent-option-value="{field.proposed_value}"]'
                )
                await opt_locator.first.click()

            else:
                await locator.first.fill(field.proposed_value)

        except PlaywrightError:
            continue

    if submit_field_id:
        frame = frame_by_field_id.get(submit_field_id)
        if frame:
            await frame.locator(f'[data-agent-field-id="{submit_field_id}"]').first.click()
