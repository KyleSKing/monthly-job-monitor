"""Crawl4AI content extraction — Tier 1 reader (replaces Jina Reader).

Self-hosted headless-Chromium fetch → clean markdown. No API key, no
per-request cost, no payment wall. Exposes the same .fetch(url) -> Optional[str]
interface as JinaClient so the swap in main.py is a one-liner.

crawl4ai is async; main.py's tier loop is sync. We keep one AsyncWebCrawler
alive on a dedicated event loop and reuse it across all URLs (launching a
browser per URL for 500+ pages would be prohibitively slow).
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Crawl4aiClient:
    """Fetch URL content as clean markdown via crawl4ai (headless Chromium)."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._loop = None
        self._crawler = None
        self._ready = False

    def _ensure(self) -> bool:
        """Lazily create the event loop + crawler. Returns False if unavailable."""
        if self._ready:
            return True
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig

            self._loop = asyncio.new_event_loop()
            browser_conf = BrowserConfig(headless=True)
            self._crawler = AsyncWebCrawler(config=browser_conf)
            self._loop.run_until_complete(self._crawler.__aenter__())
            self._ready = True
            return True
        except Exception as e:
            logger.warning(f"[Crawl4AI] init failed, content extraction disabled: {e}")
            return False

    def fetch(self, url: str) -> Optional[str]:
        """Fetch a URL and return clean markdown content. Silent-ish on failure."""
        if not url or not url.strip():
            return None
        if not self._ensure():
            return None

        try:
            from crawl4ai import CrawlerRunConfig, CacheMode

            run_conf = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=self.timeout * 1000,
            )
            result = self._loop.run_until_complete(
                self._crawler.arun(url=url.strip(), config=run_conf)
            )
            if not result or not getattr(result, "success", False):
                err = getattr(result, "error_message", "unknown") if result else "no result"
                logger.warning(f"[Crawl4AI] fetch failed for {url}: {err}")
                return None
            md = getattr(result, "markdown", None)
            # markdown may be a str or a MarkdownGenerationResult object
            if md is not None and not isinstance(md, str):
                md = getattr(md, "fit_markdown", None) or getattr(md, "raw_markdown", None)
            return md or None
        except Exception as e:
            logger.warning(f"[Crawl4AI] fetch error for {url}: {e}")
            return None

    def close(self):
        """Tear down the crawler + loop. Safe to call multiple times."""
        if self._crawler is not None and self._loop is not None:
            try:
                self._loop.run_until_complete(self._crawler.__aexit__(None, None, None))
            except Exception:
                pass
        if self._loop is not None:
            try:
                self._loop.close()
            except Exception:
                pass
        self._crawler = None
        self._loop = None
        self._ready = False
