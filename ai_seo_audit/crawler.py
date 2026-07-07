"""Robust HTML downloader and recursive website crawler with robots.txt enforcement, response time tracking, and concurrent crawling.
"""

import time
import re
from collections import deque
from typing import Dict, List, Optional, Set, Tuple, Generator
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException, Timeout, SSLError

from ai_seo_audit.utils import logger, is_internal_url

# Soft 404 detection patterns
SOFT_404_PATTERNS = [
    r"page\s+not\s+found",
    r"404\s+error",
    r"does\s+not\s+exist",
    r"doesn.t\s+exist",
    r"cannot\s+be\s+found",
    r"no\s+longer\s+available",
    r"this\s+page\s+has\s+been\s+moved",
    r"the\s+page\s+you\s+were\s+looking\s+for",
    r"oops.*page\s+not\s+found",
    r"error\s+404",
    r"not\s+found",
    r"we\s+couldn.t\s+find",
    r"something\s+went\s+wrong",
    r"this\s+url\s+does\s+not\s+exist",
]
SOFT_404_RE = re.compile("|".join(SOFT_404_PATTERNS), re.IGNORECASE)


class CrawlResult:
    """Represents the results of a crawling attempt for a single page."""

    def __init__(
        self,
        url: str,
        html: str = "",
        status_code: int = 0,
        headers: Optional[Dict[str, str]] = None,
        final_url: str = "",
        redirect_history: Optional[List[str]] = None,
        redirect_status_codes: Optional[List[int]] = None,
        error_message: Optional[str] = None,
        time_to_first_byte: Optional[float] = None,
        total_response_time: Optional[float] = None,
        html_size_bytes: int = 0,
        compressed_size: Optional[int] = None,
        crawl_depth: int = 0,
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.headers = headers or {}
        self.final_url = final_url or url
        self.redirect_history = redirect_history or []
        self.redirect_status_codes = redirect_status_codes or []
        self.error_message = error_message
        self.time_to_first_byte = time_to_first_byte
        self.total_response_time = total_response_time
        self.html_size_bytes = html_size_bytes
        self.compressed_size = compressed_size
        self.crawl_depth = crawl_depth

    @property
    def is_success(self) -> bool:
        """Checks if the request completed with a 2xx status code and no errors."""
        return not self.error_message and 200 <= self.status_code < 300

    @property
    def has_redirect(self) -> bool:
        """Check if this page had any redirects."""
        return len(self.redirect_history) > 0

    @property
    def has_redirect_loop(self) -> bool:
        """Check if redirect chain contains a loop."""
        all_urls = self.redirect_history + [self.final_url]
        return len(all_urls) != len(set(all_urls))

    @property
    def is_soft_404(self) -> bool:
        """Detect if page returns 200 but contains error content."""
        if self.status_code != 200 or not self.html:
            return False
        text_sample = self.html[:5000]
        return bool(SOFT_404_RE.search(text_sample))

    @property
    def redirect_chain_display(self) -> str:
        """Return a human-readable redirect chain like Screaming Frog."""
        if not self.redirect_history:
            return ""
        parts = []
        for i, url in enumerate(self.redirect_history):
            code = self.redirect_status_codes[i] if i < len(self.redirect_status_codes) else "?"
            parts.append(f"[{code}] {url}")
        code = self.status_code
        parts.append(f"[{code}] {self.final_url}")
        return " → ".join(parts)

    @property
    def x_robots_tag(self) -> Optional[str]:
        """Extract X-Robots-Tag from response headers."""
        return self.headers.get("X-Robots-Tag") or self.headers.get("x-robots-tag")

    @property
    def content_encoding(self) -> Optional[str]:
        """Extract Content-Encoding header."""
        return self.headers.get("Content-Encoding") or self.headers.get("content-encoding")

    @property
    def compression_ratio(self) -> Optional[float]:
        """Calculate compression ratio if compressed_size is known."""
        if self.compressed_size and self.html_size_bytes > 0:
            return round((1 - self.compressed_size / self.html_size_bytes) * 100, 1)
        return None


# Browser-like headers to avoid bot detection
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class SafeCrawler:
    """A safe HTTP crawler that downloads HTML contents under strict limits with response time tracking."""

    def __init__(
        self,
        timeout: int = 15,
        max_size_bytes: int = 10 * 1024 * 1024,
        user_agent: Optional[str] = None,
        verify_ssl: bool = False
    ):
        self.timeout = timeout
        self.max_size_bytes = max_size_bytes
        self.verify_ssl = verify_ssl

        # Build a session with retry logic
        self.session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set browser-like headers
        self.session.headers.update(DEFAULT_HEADERS)
        if user_agent:
            self.session.headers["User-Agent"] = user_agent

    def fetch_page(self, url: str) -> CrawlResult:
        """Safely retrieves HTML contents of a URL, collecting redirect histories and timing metrics."""
        logger.debug(f"Initiating request to: {url}")
        start_time = time.time()
        ttfb = None

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
                verify=self.verify_ssl
            )

            # Measure TTFB from first content
            ttfb = (time.time() - start_time) * 1000  # ms

            status_code = response.status_code
            final_url = response.url
            response_headers = dict(response.headers)

            # Extract redirect history with status codes
            redirect_history = [res.url for res in response.history]
            redirect_status_codes = [res.status_code for res in response.history]

            content_type = response_headers.get("Content-Type", "")
            if "text/html" not in content_type.lower() and "application/xhtml" not in content_type.lower():
                total_time = (time.time() - start_time) * 1000
                return CrawlResult(
                    url=url,
                    status_code=status_code,
                    headers=response_headers,
                    final_url=final_url,
                    redirect_history=redirect_history,
                    redirect_status_codes=redirect_status_codes,
                    error_message=f"Non-HTML content: {content_type}",
                    time_to_first_byte=ttfb,
                    total_response_time=total_time,
                )

            content_length = response_headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > self.max_size_bytes:
                        total_time = (time.time() - start_time) * 1000
                        return CrawlResult(
                            url=url,
                            status_code=status_code,
                            headers=response_headers,
                            final_url=final_url,
                            redirect_history=redirect_history,
                            redirect_status_codes=redirect_status_codes,
                            error_message="Content length exceeds maximum limit.",
                            time_to_first_byte=ttfb,
                            total_response_time=total_time,
                        )
                except ValueError:
                    pass

            body_bytes = bytearray()
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    body_bytes.extend(chunk)
                    if len(body_bytes) > self.max_size_bytes:
                        total_time = (time.time() - start_time) * 1000
                        return CrawlResult(
                            url=url,
                            status_code=status_code,
                            headers=response_headers,
                            final_url=final_url,
                            redirect_history=redirect_history,
                            redirect_status_codes=redirect_status_codes,
                            error_message="Download size exceeded limit.",
                            time_to_first_byte=ttfb,
                            total_response_time=total_time,
                        )

            encoding = response.encoding or response.apparent_encoding or "utf-8"
            try:
                html = body_bytes.decode(encoding, errors="replace")
            except Exception:
                html = body_bytes.decode("utf-8", errors="replace")

            total_time = (time.time() - start_time) * 1000
            compressed_size = len(body_bytes)

            return CrawlResult(
                url=url,
                html=html,
                status_code=status_code,
                headers=response_headers,
                final_url=final_url,
                redirect_history=redirect_history,
                redirect_status_codes=redirect_status_codes,
                time_to_first_byte=ttfb,
                total_response_time=total_time,
                html_size_bytes=len(html.encode("utf-8", errors="replace")),
                compressed_size=compressed_size,
            )

        except Timeout:
            if url.startswith("https://") and self.verify_ssl:
                try:
                    logger.debug(f"Retrying {url} without SSL verification")
                    start2 = time.time()
                    response = self.session.get(
                        url, timeout=self.timeout + 10,
                        stream=True, allow_redirects=True, verify=False
                    )
                    ttfb2 = (time.time() - start2) * 1000
                    body_bytes = bytearray()
                    for chunk in response.iter_content(chunk_size=16384):
                        if chunk:
                            body_bytes.extend(chunk)
                    html = body_bytes.decode("utf-8", errors="replace")
                    total2 = (time.time() - start2) * 1000
                    return CrawlResult(
                        url=url, html=html,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        final_url=response.url,
                        redirect_history=[r.url for r in response.history],
                        redirect_status_codes=[r.status_code for r in response.history],
                        time_to_first_byte=ttfb2,
                        total_response_time=total2,
                        html_size_bytes=len(html.encode("utf-8", errors="replace")),
                        compressed_size=len(body_bytes),
                    )
                except Exception:
                    pass
            total_time = (time.time() - start_time) * 1000
            return CrawlResult(url=url, error_message="Request timeout", total_response_time=total_time)
        except SSLError:
            try:
                logger.debug(f"Retrying {url} without SSL verification")
                start2 = time.time()
                response = self.session.get(
                    url, timeout=self.timeout + 10,
                    stream=True, allow_redirects=True, verify=False
                )
                ttfb2 = (time.time() - start2) * 1000
                body_bytes = bytearray()
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        body_bytes.extend(chunk)
                html = body_bytes.decode("utf-8", errors="replace")
                total2 = (time.time() - start2) * 1000
                return CrawlResult(
                    url=url, html=html,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    final_url=response.url,
                    redirect_history=[r.url for r in response.history],
                    redirect_status_codes=[r.status_code for r in response.history],
                    time_to_first_byte=ttfb2,
                    total_response_time=total2,
                    html_size_bytes=len(html.encode("utf-8", errors="replace")),
                    compressed_size=len(body_bytes),
                )
            except Exception as ssl_err:
                total_time = (time.time() - start_time) * 1000
                return CrawlResult(url=url, error_message=f"SSL error: {ssl_err}", total_response_time=total_time)
        except RequestException as req_err:
            if url.startswith("https://"):
                http_url = url.replace("https://", "http://", 1)
                logger.debug(f"Trying HTTP fallback for {url}")
                try:
                    start2 = time.time()
                    response = self.session.get(
                        http_url, timeout=self.timeout,
                        stream=True, allow_redirects=True, verify=False
                    )
                    ttfb2 = (time.time() - start2) * 1000
                    body_bytes = bytearray()
                    for chunk in response.iter_content(chunk_size=16384):
                        if chunk:
                            body_bytes.extend(chunk)
                    html = body_bytes.decode("utf-8", errors="replace")
                    total2 = (time.time() - start2) * 1000
                    return CrawlResult(
                        url=url, html=html,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        final_url=response.url,
                        redirect_history=[r.url for r in response.history],
                        redirect_status_codes=[r.status_code for r in response.history],
                        time_to_first_byte=ttfb2,
                        total_response_time=total2,
                        html_size_bytes=len(html.encode("utf-8", errors="replace")),
                        compressed_size=len(body_bytes),
                    )
                except Exception:
                    pass
            total_time = (time.time() - start_time) * 1000
            return CrawlResult(url=url, error_message=f"HTTP request failed: {req_err}", total_response_time=total_time)
        except Exception as err:
            total_time = (time.time() - start_time) * 1000
            return CrawlResult(url=url, error_message=f"Unexpected error: {err}", total_response_time=total_time)


class SiteCrawler:
    """Orchestrates recursive, multi-page site crawling with robots.txt enforcement and concurrent crawling support."""

    def __init__(
        self,
        crawler: SafeCrawler,
        max_pages: int = 50,
        max_depth: int = 3,
        respect_robots: bool = True,
        max_workers: int = 1,
        crawl_delay: float = 0.0,
    ):
        self.crawler = crawler
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.respect_robots = respect_robots
        self.max_workers = max_workers
        self.crawl_delay = crawl_delay
        self.robots_parsers: Dict[str, RobotFileParser] = {}
        self._robots_cache: Dict[str, str] = {}

    def _is_allowed_by_robots(self, url: str) -> bool:
        """Determines if a URL can be crawled according to robots.txt rules."""
        if not self.respect_robots:
            return True
        parsed = urlparse(url)
        domain = parsed.netloc
        scheme = parsed.scheme
        if not domain:
            return True
        if domain not in self.robots_parsers:
            rp = RobotFileParser()
            rp.set_url(f"{scheme}://{domain}/robots.txt")
            try:
                res = self.crawler.session.get(
                    f"{scheme}://{domain}/robots.txt", timeout=5,
                    verify=self.crawler.verify_ssl
                )
                if res.status_code == 200:
                    rp.parse(res.text.splitlines())
                    self._robots_cache[domain] = res.text
                else:
                    rp.parse([])
            except Exception:
                rp.parse([])
            self.robots_parsers[domain] = rp
        return self.robots_parsers[domain].can_fetch(
            self.crawler.session.headers.get("User-Agent", ""), url
        )

    def _get_robots_txt_content(self, domain: str) -> Optional[str]:
        """Get cached robots.txt content for a domain."""
        return self._robots_cache.get(domain)

    def _discover_sitemap_urls(self, start_url: str) -> List[Tuple[str, Optional[str]]]:
        """Fetch sitemap.xml and extract all URLs with optional lastmod dates."""
        parsed = urlparse(start_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        sitemap_urls = []

        sitemap_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]
        for path in sitemap_paths:
            try:
                res = self.crawler.session.get(
                    f"{base}{path}", timeout=10, verify=self.crawler.verify_ssl
                )
                if res.status_code == 200 and "xml" in res.headers.get("Content-Type", "").lower():
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(res.text)
                    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                    sitemaps = root.findall(".//s:sitemap", ns)
                    if sitemaps:
                        for sm in sitemaps:
                            loc = sm.find("s:loc", ns)
                            lastmod = sm.find("s:lastmod", ns)
                            if loc is not None and loc.text:
                                try:
                                    sub_res = self.crawler.session.get(
                                        loc.text.strip(), timeout=10,
                                        verify=self.crawler.verify_ssl
                                    )
                                    if sub_res.status_code == 200:
                                        sub_root = ET.fromstring(sub_res.text)
                                        for url_elem in sub_root.findall(".//s:url", ns):
                                            loc_tag = url_elem.find("s:loc", ns)
                                            lm_tag = url_elem.find("s:lastmod", ns)
                                            if loc_tag is not None and loc_tag.text:
                                                lastmod_val = lm_tag.text.strip() if lm_tag is not None and lm_tag.text else None
                                                sitemap_urls.append((loc_tag.text.strip(), lastmod_val))
                                except Exception:
                                    pass
                    else:
                        for url_elem in root.findall(".//s:url", ns):
                            loc_tag = url_elem.find("s:loc", ns)
                            lm_tag = url_elem.find("s:lastmod", ns)
                            if loc_tag is not None and loc_tag.text:
                                lastmod_val = lm_tag.text.strip() if lm_tag is not None and lm_tag.text else None
                                sitemap_urls.append((loc_tag.text.strip(), lastmod_val))
                    if sitemap_urls:
                        break
            except Exception:
                continue
        return sitemap_urls

    def _extract_links_from_html(self, html: str, base_url: str) -> List[str]:
        """Extract ALL internal links from HTML: <a>, <link>, <area>, meta refresh."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        links = set()

        for tag in soup.find_all("a"):
            href = tag.get("href")
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                abs_url = urljoin(base_url, href.strip())
                if is_internal_url(abs_url, base_url):
                    links.add(abs_url)

        for tag in soup.find_all("link"):
            href = tag.get("href")
            rel = tag.get("rel", [])
            if href and any(r in rel for r in ["alternate", "canonical", "next", "prev"]):
                abs_url = urljoin(base_url, href.strip())
                if is_internal_url(abs_url, base_url):
                    links.add(abs_url)

        for tag in soup.find_all("area"):
            href = tag.get("href")
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                abs_url = urljoin(base_url, href.strip())
                if is_internal_url(abs_url, base_url):
                    links.add(abs_url)

        for tag in soup.find_all("meta", attrs={"http-equiv": "refresh"}):
            content = tag.get("content", "")
            if "url=" in content.lower():
                url_part = content.split("url=", 1)[-1].strip()
                abs_url = urljoin(base_url, url_part)
                if is_internal_url(abs_url, base_url):
                    links.add(abs_url)

        return list(links)

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        # Remove trailing slash, normalize path
        path = parsed.path.rstrip("/") or "/"
        # Remove index files
        for idx in ["index.html", "index.htm", "index.php", "default.html"]:
            if path.lower().endswith(idx):
                path = path[: -len(idx)]
                break
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def crawl_site(self, start_url: str) -> Generator[Tuple[str, int, Optional[CrawlResult], int], None, None]:
        """Crawls the whole website like Screaming Frog.

        Yields:
            Tuple of (current_url, pages_crawled_count, crawl_result, queue_size)
        """
        visited: Set[str] = set()
        queue: deque = deque()
        pages_crawled = 0

        # STEP 1: Discover all URLs from sitemap.xml
        sitemap_urls = self._discover_sitemap_urls(start_url)
        for url, lastmod in sitemap_urls:
            parsed = urlparse(url)
            clean = self._normalize_url(url)
            if clean not in visited:
                queue.append((url, 0))
                visited.add(clean)

        # STEP 2: Add start URL
        parsed_start = urlparse(start_url)
        start_clean = self._normalize_url(start_url)
        if start_clean not in visited:
            queue.append((start_url, 0))
            visited.add(start_clean)

        # STEP 3: BFS crawl through all discovered URLs
        while queue and pages_crawled < self.max_pages:
            url, depth = queue.popleft()

            clean_url = self._normalize_url(url)

            if clean_url in visited and pages_crawled > 0:
                pass
            visited.add(clean_url)

            if not self._is_allowed_by_robots(url):
                # Still yield to show the URL was processed
                yield url, pages_crawled, CrawlResult(
                    url=url,
                    status_code=0,
                    error_message="Blocked by robots.txt",
                    crawl_depth=depth,
                ), len(queue)
                continue

            # Apply crawl delay
            if self.crawl_delay > 0 and pages_crawled > 0:
                time.sleep(self.crawl_delay)

            result = self.crawler.fetch_page(url)
            result.crawl_depth = depth
            pages_crawled += 1
            yield url, pages_crawled, result, len(queue)

            if not result.is_success:
                continue

            # Extract links from this page
            if depth < self.max_depth:
                discovered = self._extract_links_from_html(result.html, result.final_url)
                for link_url in discovered:
                    link_parsed = urlparse(link_url)
                    link_path = link_parsed.path.rstrip("/") or "/"
                    link_clean = f"{link_parsed.scheme}://{link_parsed.netloc}{link_path}"
                    if link_clean not in visited:
                        visited.add(link_clean)
                        queue.append((link_url, depth + 1))
