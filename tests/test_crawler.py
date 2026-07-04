"""Unit tests for the crawler and multipage SiteCrawler modules.
"""

from unittest.mock import MagicMock, patch
import pytest

from ai_seo_audit.crawler import SafeCrawler, SiteCrawler, CrawlResult


def test_fetch_page_success_with_redirects():
    """Tests that redirects are correctly recorded in the crawl results."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/target"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.iter_content.return_value = [b"<html></html>"]
        
        # Mock redirect history responses
        mock_r1 = MagicMock()
        mock_r1.url = "https://example.com/start"
        mock_r2 = MagicMock()
        mock_r2.url = "https://example.com/hop"
        mock_response.history = [mock_r1, mock_r2]

        mock_get.return_value = mock_response

        crawler = SafeCrawler()
        res = crawler.fetch_page("https://example.com/start")
        
        assert res.is_success
        assert res.final_url == "https://example.com/target"
        assert res.redirect_history == ["https://example.com/start", "https://example.com/hop"]


def test_site_crawler_recursive_crawl():
    """Tests recursive site crawler and depth limits."""
    # We want to crawl https://example.com/
    # Page 1 contains link to "/about"
    # Page 2 contains link to "/contact" and "https://external.com"
    html_home = '<html><body><a href="/about">About</a></body></html>'
    html_about = '<html><body><a href="/contact">Contact</a><a href="https://external.com">External</a></body></html>'
    html_contact = '<html><body><h1>Contact Us</h1></body></html>'

    crawler = SafeCrawler()
    site_crawler = SiteCrawler(crawler=crawler, max_pages=10, max_depth=2, respect_robots=False)

    def side_effect_fetch(url):
        if url == "https://example.com/":
            return CrawlResult(url=url, html=html_home, status_code=200, headers={"Content-Type": "text/html"})
        elif url == "https://example.com/about":
            return CrawlResult(url=url, html=html_about, status_code=200, headers={"Content-Type": "text/html"})
        elif url == "https://example.com/contact":
            return CrawlResult(url=url, html=html_contact, status_code=200, headers={"Content-Type": "text/html"})
        return CrawlResult(url=url, error_message="Not found")

    with patch.object(SafeCrawler, "fetch_page", side_effect=side_effect_fetch):
        # Gather all crawler generator steps
        results = list(site_crawler.crawl_site("https://example.com/"))
        
        # Verify URLs crawled (generator yields: url, count, result, qsize)
        crawled_urls = [r[0] for r in results if r[2] is not None]
        
        # Verify it crawled home, about, and contact (internal)
        # External URL (https://external.com) should be ignored
        assert "https://example.com/" in crawled_urls
        assert "https://example.com/about" in crawled_urls
        assert "https://example.com/contact" in crawled_urls
        assert "https://external.com" not in crawled_urls
        assert len(crawled_urls) == 3


def test_site_crawler_respects_robots():
    """Tests that site crawler skips URL disallowed by robots.txt."""
    crawler = SafeCrawler()
    site_crawler = SiteCrawler(crawler=crawler, max_pages=10, respect_robots=True)

    with patch.object(SiteCrawler, "_is_allowed_by_robots", return_value=False):
        # Generator yields: url, count, result, qsize
        results = list(site_crawler.crawl_site("https://example.com/disallowed"))
        assert len(results) == 1
        assert results[0][0] == "https://example.com/disallowed"
        # Since it is blocked, result should be None
        assert results[0][2] is None
