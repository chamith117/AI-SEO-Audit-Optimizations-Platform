"""Robust HTML downloader and recursive website crawler with robots.txt enforcement.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
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
        error_message: Optional[str] = None
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.headers = headers or {}
        self.final_url = final_url or url
        self.redirect_history = redirect_history or []
        self.error_message = error_message

    @property
    def is_success(self) -> bool:
        """Checks if the request completed with a 2xx status code and no errors."""
        return not self.error_message and 200 <= self.status_code < 300


class SafeCrawler:
    """A safe HTTP crawler that downloads HTML contents under strict limits."""

    DEFAULT_USER_AGENT = "AI-SEO-Audit-Toolkit/1.0 (+https://github.com/google/ai-seo-audit)"

    def __init__(
        self,
        timeout: int = 10,
        max_size_bytes: int = 5 * 1024 * 1024,
        user_agent: Optional[str] = None,
        verify_ssl: bool = True
    ):
        self.timeout = timeout
        self.max_size_bytes = max_size_bytes
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.verify_ssl = verify_ssl

    def fetch_page(self, url: str) -> CrawlResult:
        """Safely retrieves HTML contents of a URL, collecting redirect histories."""
        headers = {"User-Agent": self.user_agent}
        logger.debug(f"Initiating request to: {url}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
                verify=self.verify_ssl
            )
            
            status_code = response.status_code
            final_url = response.url
            response_headers = dict(response.headers)
            
            # Extract redirect history (list of absolute redirect URLs)
            redirect_history = [res.url for res in response.history]
            
            content_type = response_headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                return CrawlResult(
                    url=url,
                    status_code=status_code,
                    headers=response_headers,
                    final_url=final_url,
                    redirect_history=redirect_history,
                    error_message=f"Invalid Content-Type: {content_type}. Only text/html is supported."
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
                            error_message=f"Content length exceeds maximum limit."
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
            return CrawlResult(url=url, error_message="Request timeout")
        except SSLError as ssl_err:
            return CrawlResult(url=url, error_message=f"SSL validation error: {ssl_err}")
        except RequestException as req_err:
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
                headers = {"User-Agent": self.crawler.user_agent}
                res = requests.get(
                    f"{scheme}://{domain}/robots.txt",
                    headers=headers,
                    timeout=5,
                    verify=self.crawler.verify_ssl
                )
                if res.status_code == 200:
                    rp.parse(res.text.splitlines())
                else:
                    rp.parse([])
            except Exception:
                rp.parse([])
            self.robots_parsers[domain] = rp

        return self.robots_parsers[domain].can_fetch(self.crawler.user_agent, url)

    def crawl_site(self, start_url: str):
        """Iteratively crawls the website from a start URL, yielding results for progress tracking.

        Yields:
            Tuple[str, int, Optional[CrawlResult], int]: (current_url, pages_crawled_so_far, result_if_fetched, current_queue_size)
        """
        # Set of seen URLs to prevent duplicate visits
        visited: Set[str] = set()
        
        # Queue storing tuples of (url, current_depth)
        queue: deque = deque([(start_url, 0)])
        
        pages_crawled = 0

        while queue and pages_crawled < self.max_pages:
            url, depth = queue.popleft()
            
            # De-duplicate
            # Loose comparison: strip trailing slash and hash fragments
            parsed = urlparse(url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            if clean_url in visited:
                continue
                
            visited.add(clean_url)

            # Respect robots.txt
            if not self._is_allowed_by_robots(url):
                logger.warning(f"URL disallowed by robots.txt: {url}")
                yield url, pages_crawled, None, len(queue)
                continue

            # Fetch page
            result = self.crawler.fetch_page(url)
            pages_crawled += 1
            
            # Yield result for CLI callback/progress bar
            yield url, pages_crawled, result, len(queue)

            if not result.is_success:
                continue

            # Enqueue internal links if depth has not exceeded limit
            if depth < self.max_depth:
                from ai_seo_audit.parser import SEOHTMLParser
                parser = SEOHTMLParser(html_content=result.html, base_url=result.final_url)
                
                for link in parser.get_links():
                    if link.is_internal:
                        # Ensure we don't enqueue already visited ones
                        link_parsed = urlparse(link.url)
                        link_clean = f"{link_parsed.scheme}://{link_parsed.netloc}{link_parsed.path}".rstrip("/")
                        if link_clean not in visited:
                            queue.append((link.url, depth + 1))
