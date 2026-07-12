"""Playwright-based JavaScript renderer for SPA/CSR pages.

Renders JavaScript-heavy pages using a headless Chromium browser,
returning the fully rendered HTML for parsing.
"""

import time
from typing import Optional
from contextlib import contextmanager

from ai_seo_audit.utils import logger

# Lazy imports — playwright is optional
_playwright = None
_browser = None


def is_playwright_available() -> bool:
    """Check if Playwright is installed."""
    try:
        import playwright.sync_api
        return True
    except ImportError:
        return False


def _ensure_playwright():
    """Lazy-initialize Playwright browser."""
    global _playwright, _browser
    if _playwright is not None and _browser is not None:
        return _playwright, _browser

    try:
        from playwright.sync_api import sync_playwright
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--no-first-run",
            ]
        )
        logger.info("Playwright Chromium browser launched successfully.")
        return _playwright, _browser
    except Exception as e:
        logger.error(f"Failed to launch Playwright browser: {e}")
        raise


def shutdown_playwright():
    """Cleanly shut down Playwright browser."""
    global _playwright, _browser
    try:
        if _browser:
            _browser.close()
        if _playwright:
            _playwright.stop()
    except Exception:
        pass
    _browser = None
    _playwright = None


class JSRenderer:
    """Renders JavaScript-heavy pages using Playwright headless Chromium.

    Usage:
        renderer = JSRenderer(timeout=30)
        rendered_html = renderer.render("https://example.com")
    """

    def __init__(
        self,
        timeout: int = 30,
        wait_until: str = "networkidle",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: Optional[str] = None,
    ):
        self.timeout = timeout * 1000  # Playwright uses ms
        self.wait_until = wait_until
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.user_agent = user_agent
        self._context = None

    def _get_context(self):
        """Get or create a browser context."""
        if self._context is None:
            _, browser = _ensure_playwright()
            context_opts = {
                "viewport": {"width": self.viewport_width, "height": self.viewport_height},
                "java_script_enabled": True,
                "ignore_https_errors": True,
            }
            if self.user_agent:
                context_opts["user_agent"] = self.user_agent
            self._context = browser.new_context(**context_opts)
        return self._context

    def render(self, url: str) -> Optional[str]:
        """Render a page with JavaScript and return the fully rendered HTML.

        Args:
            url: The URL to render.

        Returns:
            The rendered HTML string, or None if rendering failed.
        """
        start = time.time()
        context = None
        page = None
        try:
            context = self._get_context()
            page = context.new_page()

            # Block unnecessary resources for speed
            page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())
            page.route("**/google-analytics.com/**", lambda route: route.abort())
            page.route("**/googletagmanager.com/**", lambda route: route.abort())
            page.route("**/facebook.net/**", lambda route: route.abort())
            page.route("**/doubleclick.net/**", lambda route: route.abort())

            response = page.goto(
                url,
                wait_until=self.wait_until,
                timeout=self.timeout,
            )

            if response is None:
                logger.warning(f"JS render got no response for {url}")
                return None

            status = response.status
            if status >= 400:
                logger.warning(f"JS render got HTTP {status} for {url}")

            # Wait for dynamic content to settle
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass

            # Extra wait for SPA hydration
            try:
                page.wait_for_timeout(1000)
            except Exception:
                pass

            rendered_html = page.content()
            elapsed = (time.time() - start) * 1000
            logger.debug(f"JS rendered {url} in {elapsed:.0f}ms ({len(rendered_html)} bytes)")
            return rendered_html

        except Exception as e:
            logger.error(f"JS render failed for {url}: {e}")
            return None
        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass

    def render_batch(self, urls: list[str], delay: float = 0.5) -> dict[str, Optional[str]]:
        """Render multiple pages sequentially.

        Args:
            urls: List of URLs to render.
            delay: Delay between requests in seconds.

        Returns:
            Dict mapping URL to rendered HTML (or None on failure).
        """
        results = {}
        for i, url in enumerate(urls):
            results[url] = self.render(url)
            if delay > 0 and i < len(urls) - 1:
                time.sleep(delay)
        return results

    def close(self):
        """Close the browser context."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
