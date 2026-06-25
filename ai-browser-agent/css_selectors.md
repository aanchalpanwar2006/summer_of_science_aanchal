# CSS Selectors — Chrome DevTools Reference

Site used: **https://accounts.google.com** (Google Sign-In page)

---

## How to find these yourself (for the screenshot)

1. Open Chrome → navigate to https://accounts.google.com
2. Press `F12` (or `Cmd+Option+I`) to open DevTools
3. Click the **Elements** tab, then press `Ctrl+F` (`Cmd+F` on Mac) to open the element search bar
4. Paste any selector below and press Enter — DevTools highlights matching elements
5. Take a screenshot with `Cmd+Shift+4` (Mac) or Snipping Tool (Windows)

---

## Form Inputs (3)

| # | Selector | What it targets |
|---|----------|-----------------|
| 1 | `input[type="email"]` | Email address field on the sign-in form |
| 2 | `input[type="password"]` | Password entry field |
| 3 | `input[name="identifier"]` | The unified identifier input (email/phone/username) |

---

## Buttons (2)

| # | Selector | What it targets |
|---|----------|-----------------|
| 1 | `button[type="submit"]` | Primary "Next" / "Sign in" button |
| 2 | `div[role="button"]` | Google's custom accessible button (e.g. "Forgot email?") |

---

## Dropdown (1)

| # | Selector | What it targets |
|---|----------|-----------------|
| 1 | `select#lang` | Language selector in the page footer |

---

## Notes

- Google's DOM uses both native `<button>` elements and `<div role="button">` — both are valid targets for automation.
- `input[name="identifier"]` is the most reliable selector for the first field since the `type` attribute changes to `"password"` on the next step.
- Always prefer attribute selectors (`[type=...]`, `[name=...]`) over generated class names (`.VfPpkd-...`) which change with builds.
