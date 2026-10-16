"""Refresh README assets from a running local prototype, not an end-to-end test.

Install tooling: python -m pip install playwright
Then: python -m playwright install chromium
SCREENSHOT_URL=http://127.0.0.1:59054 python scripts/capture_screenshots.py
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    url = os.environ.get('SCREENSHOT_URL', 'http://127.0.0.1:59054/')
    target = ROOT / 'docs/assets/workbench.jpg'
    target.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=os.environ.get('SCREENSHOT_BROWSER_CHANNEL') or None)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900},
                                    device_scale_factor=1, color_scheme='light')
            response = page.goto(url, wait_until='networkidle')
            if response is None or not response.ok:
                raise RuntimeError('Workbench did not return a successful page: ' + url)
            page.get_by_role('heading', name='本公司 × 合作方', exact=True).wait_for()
            page.evaluate('document.fonts.ready')
            page.locator('img:visible').evaluate_all(
                '(images) => Promise.all(images.map(img => img.decode()))')
            page.screenshot(path=str(target), full_page=True, type='jpeg', quality=90,
                            animations='disabled')
        finally:
            browser.close()
    print(target)


if __name__ == '__main__':
    main()
