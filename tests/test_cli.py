"""Unit tests for the CLI execution entry point and crawl commands.
"""

from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
import pytest

from ai_seo_audit.cli import app

runner = CliRunner()


def test_cli_audit_invalid_url():
    """Tests legacy single-page audit with invalid URL."""
    result = runner.invoke(app, ["audit", "invalid-url"])
    assert result.exit_code == 1
    assert "is not a valid absolute URL" in result.stdout


def test_cli_crawl_invalid_url():
    """Tests crawl command with invalid URL."""
    result = runner.invoke(app, ["crawl", "invalid-url"])
    assert result.exit_code == 1
    assert "is not a valid absolute URL" in result.stdout


def test_cli_crawl_command_success(tmp_path):
    """Tests crawl command execution under mocked responses, writing reports."""
    output_dir = tmp_path / "exports"
    
    # Mock SiteCrawler.crawl_site to return generator values
    # yields: current_url, count, crawl_result, queue_size
    mock_crawl_result = MagicMock()
    mock_crawl_result.is_success = True
    mock_crawl_result.html = """
    <html>
      <head>
        <title>Home Page</title>
        <meta name="description" content="A description long enough for standard checks.">
        <link rel="canonical" href="https://example.com/">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body lang="en">
        <h1>Heading</h1>
        <img src="img.jpg" alt="alt text">
      </body>
    </html>
    """
    mock_crawl_result.status_code = 200
    mock_crawl_result.final_url = "https://example.com/"

    with patch("ai_seo_audit.crawler.SiteCrawler.crawl_site") as mock_crawl:
        mock_crawl.return_value = [("https://example.com/", 1, mock_crawl_result, 0)]
        
        # Mock requests.get inside CLI to avoid hitting sitemap.xml / robots.txt on internet
        with patch("requests.get") as mock_get:
            mock_res_empty = MagicMock()
            mock_res_empty.status_code = 404
            mock_get.return_value = mock_res_empty

            result = runner.invoke(app, [
                "crawl", "https://example.com",
                "--output-dir", str(output_dir),
                "--max-pages", "1"
            ])

            assert result.exit_code == 0
            assert "Website-Level Score" in result.stdout
            assert "Pages Crawl Summary" in result.stdout
            assert "✓ Audit Completed Successfully!" in result.stdout

            # Verify exported reports in output directory
            assert (output_dir / "seo_report.json").exists()
            assert (output_dir / "seo_report.html").exists()
            assert (output_dir / "seo_report.csv").exists()
            assert (output_dir / "seo_report.pdf").exists()
