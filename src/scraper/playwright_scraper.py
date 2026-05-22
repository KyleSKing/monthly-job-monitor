from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from ._exceptions import ScraperError

class PlaywrightScraper:
    def __init__(self, headless: bool = True, timeout: int = 30_000):
        self.headless = headless
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, args=["--no-sandbox"])
                page = browser.new_page()
                page.set_default_timeout(self.timeout)
                page.goto(url, wait_until="networkidle")
                content = page.content()
                browser.close()
                return content
        except PlaywrightTimeout as exc:
            raise ScraperError(f"Playwright timeout for {url}") from exc
        except Exception as exc:
            raise ScraperError(f"Playwright error for {url}: {exc}") from exc