from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Frame, Page

from models import FieldOption, FormField

# Runs once per frame. Walks the DOM, tags every fillable element with a stable
# data-agent-field-id attribute (so Python can re-locate it later without ever
# reconstructing a CSS selector), groups radio/checkbox siblings sharing a
# `name` into one logical field, and picks a best-guess submit button.
SCAN_JS = """
(prefix) => {
    function computeLabel(el) {
        if (el.id) {
            const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (lbl && lbl.textContent.trim()) return lbl.textContent.trim();
        }
        const ancestorLabel = el.closest('label');
        if (ancestorLabel && ancestorLabel.textContent.trim()) return ancestorLabel.textContent.trim();
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();
        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const target = document.getElementById(labelledBy);
            if (target && target.textContent.trim()) return target.textContent.trim();
        }
        if (el.placeholder && el.placeholder.trim()) return el.placeholder.trim();
        const raw = el.name || el.id || '';
        if (raw) {
            return raw
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/[_-]+/g, ' ')
                .replace(/\\s+/g, ' ')
                .trim()
                .replace(/^./, c => c.toUpperCase());
        }
        return 'Unnamed field';
    }

    function elementType(el) {
        const tag = el.tagName.toLowerCase();
        if (tag === 'textarea') return 'textarea';
        if (tag === 'select') return 'select';
        const type = (el.type || 'text').toLowerCase();
        if (['file', 'checkbox', 'radio', 'email', 'tel', 'date', 'number'].includes(type)) return type;
        if (['text', 'search', 'url', 'password'].includes(type)) return 'text';
        return 'other';
    }

    let counter = 0;
    const nextId = () => `${prefix}-af-${counter++}`;
    const fields = [];

    const candidates = Array.from(document.querySelectorAll('input, textarea, select'));
    const excludedTypes = new Set(['hidden', 'submit', 'button', 'reset', 'image']);
    const relevant = candidates.filter(el => !excludedTypes.has((el.type || '').toLowerCase()));

    const grouped = new Set();

    for (const el of relevant) {
        if (grouped.has(el)) continue;
        const type = elementType(el);

        if (type === 'radio' || (type === 'checkbox' && el.name)) {
            const siblings = relevant.filter(
                other => elementType(other) === type && other.name === el.name && !grouped.has(other)
            );
            if (siblings.length > 1) {
                const fieldId = nextId();
                const options = siblings.map(sib => {
                    grouped.add(sib);
                    sib.setAttribute('data-agent-field-id', fieldId);
                    sib.setAttribute('data-agent-option-value', sib.value || '');
                    return { value: sib.value || '', label: computeLabel(sib) };
                });
                const checked = siblings.find(sib => sib.checked);
                fields.push({
                    field_id: fieldId,
                    label: el.name
                        .replace(/([a-z])([A-Z])/g, '$1 $2')
                        .replace(/[_-]+/g, ' ')
                        .trim()
                        .replace(/^./, c => c.toUpperCase()),
                    element_type: type,
                    required: siblings.some(sib => sib.required),
                    current_value: checked ? checked.value : '',
                    options,
                });
                continue;
            }
        }

        const fieldId = nextId();
        el.setAttribute('data-agent-field-id', fieldId);
        grouped.add(el);

        let options = [];
        let currentValue = el.value || '';
        if (type === 'select') {
            options = Array.from(el.options).map(o => ({ value: o.value, label: o.textContent.trim() }));
        } else if (type === 'checkbox') {
            currentValue = el.checked ? 'true' : 'false';
        } else if (type === 'file') {
            currentValue = '';
        }

        fields.push({
            field_id: fieldId,
            label: computeLabel(el),
            element_type: type,
            required: !!(el.required || el.getAttribute('aria-required') === 'true'),
            current_value: currentValue,
            options,
        });
    }

    let submitId = null;
    const submitCandidates = Array.from(
        document.querySelectorAll('button[type=submit], input[type=submit], button:not([type])')
    );
    const textMatch = /submit|apply|send|register|continue|save/i;
    const best =
        submitCandidates.find(b => textMatch.test(b.textContent || b.value || '')) || submitCandidates[0];
    if (best) {
        submitId = `${prefix}-submit`;
        best.setAttribute('data-agent-field-id', submitId);
    }

    return { fields, submit_id: submitId };
}
"""


@dataclass
class ScanResult:
    fields: list[FormField] = field(default_factory=list)
    frame_by_field_id: dict[str, Frame] = field(default_factory=dict)
    submit_field_id: Optional[str] = None


async def scan_page(page: Page) -> ScanResult:
    result = ScanResult()

    for idx, frame in enumerate(page.frames):
        prefix = f"f{idx}"
        try:
            raw = await frame.evaluate(SCAN_JS, prefix)
        except PlaywrightError:
            continue

        for raw_field in raw.get("fields", []):
            field_id = raw_field["field_id"]
            result.frame_by_field_id[field_id] = frame
            result.fields.append(
                FormField(
                    field_id=field_id,
                    label=raw_field["label"],
                    element_type=raw_field["element_type"],
                    required=raw_field["required"],
                    current_value=raw_field.get("current_value", ""),
                    options=[FieldOption(**o) for o in raw_field.get("options", [])],
                )
            )

        submit_id = raw.get("submit_id")
        if submit_id and result.submit_field_id is None:
            result.frame_by_field_id[submit_id] = frame
            result.submit_field_id = submit_id

    return result
