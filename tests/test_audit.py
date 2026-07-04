"""Unit tests for the audit engine module.
"""

from unittest.mock import patch, MagicMock, ANY
import pytest

from ai_seo_audit.audit import SEOAuditor
from ai_seo_audit.crawler import CrawlResult
from ai_seo_audit.models import (
    PageMetadataModel,
    HeadingModel,
    ImageModel,
    LinkModel,
    JSONLDModel,
    PageAuditReport
)


def test_page_audit_warnings_and_deductions():
    """Tests page audit reports containing viewport, lang, social, and schema warnings."""
    crawl_res = CrawlResult(url="https://example.com", status_code=200, final_url="https://example.com")
    
    metadata = PageMetadataModel(
        title="Test Page",  # Under length (WARN)
        meta_description="Too short",  # Under length (WARN)
        meta_robots="index",
        canonical_url="https://example.com",
        viewport=None,  # Missing viewport (CRITICAL)
        lang=None,  # Missing lang (WARNING)
        headings=[],  # Missing H1 (CRITICAL)
        open_graph={},  # Missing OG (WARNING)
        twitter_cards={},  # Missing Twitter (WARNING)
        json_ld=[JSONLDModel(valid=False, error="Syntax error", html_snippet="<script>")] # Invalid Schema (CRITICAL)
    )
    links = []
    images = [ImageModel(src="https://example.com/img.png", alt="", is_missing_alt=True)]  # Missing ALT (WARN)

    auditor = SEOAuditor()
    report = auditor.audit_page(
        crawl_result=crawl_res,
        metadata=metadata,
        links=links,
        images=images,
        robots_txt_found=True,
        sitemap_xml_found=True
    )

    # Assert that issues were collected
    issue_types = {issue.issue_type for issue in report.issues}
    assert "Title Length" in issue_types
    assert "Meta Description Length" in issue_types
    assert "Missing Viewport Tag" in issue_types
    assert "Missing Lang Attribute" in issue_types
    assert "Missing H1 Heading" in issue_types
    assert "Missing Open Graph Tags" in issue_types
    assert "Invalid JSON-LD" in issue_types
    assert "Missing Alt Text" in issue_types

    # Verified score is severely penalized
    assert report.score < 60


def test_site_audit_duplicates_and_orphans():
    """Tests site-wide audit checks: duplicate content, duplicate title, and orphan detection."""
    # Mock crawled page reports
    page1 = PageAuditReport(
        url="https://example.com/page1",
        status_code=200,
        is_https=True,
        metadata=PageMetadataModel(
            title="Shared Duplicate Title",
            meta_description="Unique desc 1",
            headings=[HeadingModel(level=1, text="Title")]
        ),
        links=[],
        images=[],
        issues=[],
        score=95
    )

    page2 = PageAuditReport(
        url="https://example.com/page2",
        status_code=200,
        is_https=True,
        metadata=PageMetadataModel(
            title="Shared Duplicate Title",  # Duplicate title
            meta_description="Unique desc 2",
            headings=[HeadingModel(level=1, text="Title")]
        ),
        links=[],
        images=[],
        issues=[],
        score=95
    )

    auditor = SEOAuditor(check_links=False, check_images=False)
    
    # Mock sitemap listing an orphan page
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <url><loc>https://example.com/page1</loc></url>
       <url><loc>https://example.com/page2</loc></url>
       <url><loc>https://example.com/orphan-unlinked-page</loc></url>
    </urlset>
    """

    site_report = auditor.audit_website(
        start_url="https://example.com/page1",
        pages=[page1, page2],
        robots_txt_found=True,
        sitemap_xml_found=True,
        sitemap_xml_content=sitemap_xml
    )

    # Assert duplicate title detected
    assert "Shared Duplicate Title" in site_report.duplicate_titles
    assert len(site_report.duplicate_titles["Shared Duplicate Title"]) == 2

    # Assert sitemap orphan page detected
    assert "https://example.com/orphan-unlinked-page" in site_report.orphan_pages
    assert len(site_report.orphan_pages) == 1

    # Assert duplicate title and orphan page issue warnings are added
    issue_types = {issue.issue_type for issue in site_report.site_issues}
    assert "Duplicate Page Title" in issue_types
    assert "Orphan Pages" in issue_types

    # Score should be penalized for duplicates and orphans
    assert site_report.score < 95


def test_site_audit_broken_assets_checks():
    """Tests parallel broken image and link auditing during site auditing."""
    page = PageAuditReport(
        url="https://example.com/page",
        status_code=200,
        is_https=True,
        metadata=PageMetadataModel(),
        links=[LinkModel(url="https://example.com/broken-link", text="Broken Link", is_internal=True)],
        images=[ImageModel(src="https://example.com/broken-img.jpg", alt="Bad Image", is_missing_alt=False)],
        issues=[],
        score=100
    )

    auditor = SEOAuditor(check_links=True, check_images=True)

    with patch("requests.head") as mock_head, patch("requests.get") as mock_get:
        # Mock connection failures for assets
        mock_head.side_effect = Exception("Connection Failed")
        mock_get.side_effect = Exception("Connection Failed")

        site_report = auditor.audit_website(
            start_url="https://example.com/page",
            pages=[page],
            robots_txt_found=True,
            sitemap_xml_found=False
        )

        p = site_report.pages[0]
        # Links and images must be updated to broken
        assert p.links[0].is_broken
        assert p.images[0].is_broken
        
        # Broken assets should add critical issues to the page report
        issue_types = {i.issue_type for i in p.issues}
        assert "Broken Link" in issue_types
        assert "Broken Image" in issue_types
        
        # Deducts points from page score
        assert p.score < 100
