#!/usr/bin/env python3
"""Render the figures in each visualization's figures/ directory from index.html with a headless browser.

    python3 figures.py

Requires Playwright for Python with Chromium installed (python -m playwright install chromium).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
STEPS = ["boroughs", "no_ac", "hvi", "black", "hispanic", "council"]
TABS = ["apps", "black", "hispanic"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto((ROOT / "index.html").as_uri())
    page.wait_for_selector("#layer-council path")

    canvas = page.locator(".scrolly-canvas")
    for step in STEPS:
        page.locator(f'[data-step="{step}"]').evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
        page.wait_for_function(f"() => document.querySelector('.progress span:nth-child({STEPS.index(step) + 1})').classList.contains('is-on')")
        page.wait_for_timeout(150)
        canvas.screenshot(path=ROOT / "01_heat_vulnerability_map" / "figures" / f"{step}.png")

    page.locator("#zero-in-25").screenshot(path=ROOT / "02_no_working_ac" / "figures" / "ac_status.png")
    page.locator("#days-90f").screenshot(path=ROOT / "03_days_at_or_above_90f" / "figures" / "days_at_or_above_90f.png")

    section = page.locator("#overlap")
    buttons = page.locator("#tabs button")
    for i, tab in enumerate(TABS):
        buttons.nth(i).click()
        page.wait_for_timeout(100)
        section.screenshot(path=ROOT / "04_heat_vulnerability_overlap" / "figures" / f"{tab}.png")
    buttons.nth(1).click()
    page.locator("#biv-map").scroll_into_view_if_needed()
    page.locator("#biv-map path").nth(59).hover()
    page.wait_for_selector("#biv-hover:not([hidden])")
    # The hover card is positioned relative to the viewport, so capture the viewport region around the map rather than the element.
    box = page.locator("#biv-map").bounding_box()
    page.screenshot(path=ROOT / "04_heat_vulnerability_overlap" / "figures" / "hover.png",
                    clip={"x": 0, "y": max(0, box["y"] - 20), "width": 1280, "height": min(900, box["height"] + 40)})
    browser.close()
    assert not errors, errors
    print("figures written:", *sorted(str(f.relative_to(ROOT)) for f in ROOT.glob("*/figures/*.png")), sep="\n  ")
