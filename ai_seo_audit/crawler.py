"""Robust HTML downloader and recursive website crawler with robots.txt enforcement.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException, Timeout, SSLError

from ai_seo_audit.utils import logger, is_internal_url


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
        error_message: Optional[str] = None
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.headers = headers or {}
        self.final_url = final_url or url
        self.redirect_history = redirect_history or []
        self.redirect_status_codes = redirect_status_codes or []
        self.error_message = error_message

    @property
    def is_success(self) -> bool:
        """Checks if the request completed with a 2xx status code and no errors."""
        return not self.error_message and 200 <= self.status_code < 300

    @property
    def has_redirect(self) -> bool:
        """Check if this page had any redirects."""
        return len(self.redirect_history) > 0

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
    """A safe HTTP crawler that downloads HTML contents under strict limits."""

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
        """Safely retrieves HTML contents of a URL, collecting redirect histories."""
        logger.debug(f"Initiating request to: {url}")

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
                verify=self.verify_ssl
            )
            
            status_code = response.status_code
            final_url = response.url
            response_headers = dict(response.headers)
            
            # Extract redirect history with status codes
            redirect_history = [res.url for res in response.history]
            redirect_status_codes = [res.status_code for res in response.history]
            
            content_type = response_headers.get("Content-Type", "")
            if "text/html" not in content_type.lower() and "application/xhtml" not in content_type.lower():
                # Allow non-HTML but don't parse
                return CrawlResult(
                    url=url,
                    status_code=status_code,
                    headers=response_headers,
                    final_url=final_url,
                    redirect_history=redirect_history,
                    redirect_status_codes=redirect_status_codes,
                    error_message=f"Non-HTML content: {content_type}"
                )

            content_length = response_headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > self.max_size_bytes:
                        return CrawlResult(
                            url=url,
                            status_code=status_code,
                            headers=response_headers,
                            final_url=final_url,
                            redirect_history=redirect_history,
                    redirect_status_codes=redirect_status_codes,
                            error_message="Content length exceeds maximum limit."
                        )
                except ValueError:
                    pass

            body_bytes = bytearray()
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    body_bytes.extend(chunk)
                    if len(body_bytes) > self.max_size_bytes:
                        return CrawlResult(
                            url=url,
                            status_code=status_code,
                            headers=response_headers,
                            final_url=final_url,
                            redirect_history=redirect_history,
                    redirect_status_codes=redirect_status_codes,
                            error_message="Download size exceeded limit."
                        )
            
            encoding = response.encoding or response.apparent_encoding or "utf-8"
            try:
                html = body_bytes.decode(encoding, errors="replace")
            except Exception:
                html = body_bytes.decode("utf-8", errors="replace")

            return CrawlResult(
                url=url,
                html=html,
                status_code=status_code,
                headers=response_headers,
                final_url=final_url,
                redirect_history=redirect_history
            )
            
        except Timeout:
            # Retry once without SSL if timeout
            if url.startswith("https://") and self.verify_ssl:
                try:
                    logger.debug(f"Retrying {url} without SSL verification")
                    response = self.session.get(
                        url, timeout=self.timeout + 10,
                        stream=True, allow_redirects=True, verify=False
                    )
                    body_bytes = bytearray()
                    for chunk in response.iter_content(chunk_size=16384):
                        if chunk:
                            body_bytes.extend(chunk)
                    html = body_bytes.decode("utf-8", errors="replace")
                    return CrawlResult(
                        url=url, html=html,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        final_url=response.url,
                        redirect_history=[r.url for r in response.history],
                        redirect_status_codes=[r.status_code for r in response.history]
                    )
                except Exception:
                    pass
            return CrawlResult(url=url, error_message="Request timeout")
        except SSLError:
            # Retry without SSL verification
            try:
                logger.debug(f"Retrying {url} without SSL verification")
                response = self.session.get(
                    url, timeout=self.timeout + 10,
                    stream=True, allow_redirects=True, verify=False
                )
                body_bytes = bytearray()
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        body_bytes.extend(chunk)
                html = body_bytes.decode("utf-8", errors="replace")
                return CrawlResult(
                    url=url, html=html,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    final_url=response.url,
                    redirect_history=[r.url for r in response.history],
                    redirect_status_codes=[r.status_code for r in response.history]
                )
            except Exception as ssl_err:
                return CrawlResult(url=url, error_message=f"SSL error: {ssl_err}")
        except RequestException as req_err:
            # If HTTPS fails, try HTTP
            if url.startswith("https://"):
                http_url = url.replace("https://", "http://", 1)
                logger.debug(f"Trying HTTP fallback for {url}")
                try:
                    response = self.session.get(
                        http_url, timeout=self.timeout,
                        stream=True, allow_redirects=True, verify=False
                    )
                    body_bytes = bytearray()
                    for chunk in response.iter_content(chunk_size=16384):
                        if chunk:
                            body_bytes.extend(chunk)
                    html = body_bytes.decode("utf-8", errors="replace")
                    return CrawlResult(
                        url=url, html=html,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        final_url=response.url,
                        redirect_history=[r.url for r in response.history],
                        redirect_status_codes=[r.status_code for r in response.history]
                    )
                except Exception:
                    pass
            return CrawlResult(url=url, error_message=f"HTTP request failed: {req_err}")
        except Exception as err:
            return CrawlResult(url=url, error_message=f"Unexpected error: {err}")


class SiteCrawler:
    """Orchestrates recursive, multi-page site crawling, respecting robots.txt."""

    def __init__(
        self,
        crawler: SafeCrawler,
        max_pages: int = 50,
        max_depth: int = 3,
        respect_robots: bool = True
    ):
        self.crawler = crawler
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.respect_robots = respect_robots
        self.robots_parsers: Dict[str, RobotFileParser] = {}

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
                else:
                    rp.parse([])
            except Exception:
                rp.parse([])
            self.robots_parsers[domain] = rp
        return self.robots_parsers[domain].can_fetch(
            self.crawler.session.headers.get("User-Agent", ""), url
        )

    def _discover_sitemap_urls(self, start_url: str) -> List[str]:
        """Fetch sitemap.xml and extract all URLs from it."""
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
                                            if loc_tag is not None and loc_tag.text:
                                                sitemap_urls.append(loc_tag.text.strip())
                                except Exception:
                                    pass
                    else:
                        for url_elem in root.findall(".//s:url", ns):
                            loc_tag = url_elem.find("s:loc", ns)
                            if loc_tag is not None and loc_tag.text:
                                sitemap_urls.append(loc_tag.text.strip())
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

    def crawl_site(self, start_url: str):
        """Crawls the whole website like Screaming Frog.

        Strategy:
        1. Discover URLs from sitemap.xml
        2. Crawl from start URL, discovering more links
        3. BFS through all discovered internal URLs up to max_pages
        """
        visited: Set[str] = set()
        queue: deque = deque()
        pages_crawled = 0

        # STEP 1: Discover all URLs from sitemap.xml
        sitemap_urls = self._discover_sitemap_urls(start_url)
        for url in sitemap_urls:
            parsed = urlparse(url)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/') or '/'}"
            if clean not in visited:
                queue.append((url, 0))
                visited.add(clean)

        # STEP 2: Add start URL
        parsed_start = urlparse(start_url)
        start_clean = f"{parsed_start.scheme}://{parsed_start.netloc}{parsed_start.path.rstrip('/') or '/'}"
        if start_clean not in visited:
            queue.append((start_url, 0))
            visited.add(start_clean)

        # STEP 3: BFS crawl through all discovered URLs
        while queue and pages_crawled < self.max_pages:
            url, depth = queue.popleft()

            parsed = urlparse(url)
            path = parsed.path.rstrip("/") or "/"
            clean_url = f"{parsed.scheme}://{parsed.netloc}{path}"

            if clean_url in visited and pages_crawled > 0:
                pass
            visited.add(clean_url)

            if not self._is_allowed_by_robots(url):
                yield url, pages_crawled, None, len(queue)
                continue

            result = self.crawler.fetch_page(url)
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
