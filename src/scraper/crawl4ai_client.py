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
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class Crawl4aiClient:
    """Fetch URL content as clean markdown via crawl4ai (headless Chromium)."""

    def __init__(self, timeout: int = 15, max_concurrent: int = 8):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
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
            return self._markdown_of(result)
        except Exception as e:
            logger.warning(f"[Crawl4AI] fetch error for {url}: {e}")
            return None

    def fetch_many(self, urls: List[str]) -> Dict[str, str]:
        """Fetch many URLs concurrently. Returns {url: markdown} for successes.

        Uses crawl4ai's arun_many with the default MemoryAdaptiveDispatcher so
        concurrency backs off if the (memory-limited) CI runner gets tight.
        """
        clean = [u.strip() for u in urls if u and u.strip()]
        if not clean:
            return {}
        if not self._ensure():
            return {}

        try:
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

            run_conf = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=self.timeout * 1000,
                stream=False,
            )
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=80.0,
                max_session_permit=self.max_concurrent,
            )
            results = self._loop.run_until_complete(
                self._crawler.arun_many(
                    urls=clean, config=run_conf, dispatcher=dispatcher
                )
            )
            out: Dict[str, str] = {}
            ok = 0
            for r in results or []:
                if getattr(r, "success", False):
                    md = self._markdown_of(r)
                    if md:
                        out[getattr(r, "url", "")] = md
                        ok += 1
            logger.info(f"[Crawl4AI] fetch_many: {ok}/{len(clean)} URLs extracted")
            return out
        except Exception as e:
            logger.warning(f"[Crawl4AI] fetch_many error: {e}")
            return {}

    @staticmethod
    def _markdown_of(result) -> Optional[str]:
        """Pull markdown text off a CrawlResult (str or MarkdownGenerationResult)."""
        md = getattr(result, "markdown", None)
        if md is not None and not isinstance(md, str):
            md = getattr(md, "fit_markdown", None) or getattr(md, "raw_markdown", None)
        return md or None

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
