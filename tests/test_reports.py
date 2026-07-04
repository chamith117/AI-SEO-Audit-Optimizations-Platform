"""Unit tests for the reports and exporters module.
"""

import csv
import json
from pathlib import Path
import pytest

from ai_seo_audit.models import (
    WebsiteAuditReport,
    PageAuditReport,
    PageMetadataModel,
    IssueModel
)
from ai_seo_audit.reports import (
    export_report_to_json,
    export_report_to_csv,
    export_report_to_html,
    export_report_to_pdf
)


@pytest.fixture
def sample_website_report() -> WebsiteAuditReport:
    """Fixture containing a sample WebsiteAuditReport with issues."""
    page_report = PageAuditReport(
        url="https://example.com/page1",
        status_code=200,
        is_https=True,
        metadata=PageMetadataModel(title="Sample Page Title"),
        links=[],
        images=[],
        issues=[
            IssueModel(
                url="https://example.com/page1",
                severity="CRITICAL",
                issue_type="Missing Viewport Tag",
                description="Viewport is missing.",
                recommendation="Add viewport tag."
            )
        ],
        score=80
    )
    
    return WebsiteAuditReport(
        start_url="https://example.com",
        total_pages_crawled=1,
        crawled_urls=["https://example.com/page1"],
        pages=[page_report],
        site_issues=[
            IssueModel(
                url="https://example.com",
                severity="WARNING",
                issue_type="Orphan Pages",
                description="Sitemap listed orphans.",
                recommendation="Fix orphans."
            )
        ],
        score=75
    )


def test_export_all_formats(tmp_path, sample_website_report):
    """Verifies that JSON, HTML, CSV, and PDF reports export successfully without crashes."""
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"
    csv_path = tmp_path / "report.csv"
    pdf_path = tmp_path / "report.pdf"

    # 1. Test JSON
    export_report_to_json(sample_website_report, json_path)
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["start_url"] == "https://example.com"
    assert data["score"] == 75

    # 2. Test CSV
    export_report_to_csv(sample_website_report, csv_path)
    assert csv_path.exists()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Header + 2 issues (1 site issue + 1 page issue)
    assert len(rows) == 3
    assert rows[0][0] == "URL"
    assert rows[1][2] == "Orphan Pages"  # First issue row (site issue)
    assert rows[2][2] == "Missing Viewport Tag"  # Second issue row (page issue)

    # 3. Test HTML
    export_report_to_html(sample_website_report, html_path)
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "AI Website SEO Audit Dashboard" in html_text
    assert "https://example.com/page1" in html_text

    # 4. Test PDF (ReportLab Builder)
    export_report_to_pdf(sample_website_report, pdf_path)
    assert pdf_path.exists()
    # Check that it generated some bytes
    assert pdf_path.stat().st_size > 1000
