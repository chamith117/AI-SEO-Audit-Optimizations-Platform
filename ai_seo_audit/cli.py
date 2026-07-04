"""CLI interface implemented via Typer for single-page auditing and site-wide crawling.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import urllib3
import requests
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ai_seo_audit.config import load_config
from ai_seo_audit.utils import setup_logging, is_valid_url, logger
from ai_seo_audit.crawler import SafeCrawler, SiteCrawler
from ai_seo_audit.parser import SEOHTMLParser
from ai_seo_audit.audit import SEOAuditor
from ai_seo_audit.reports import (
    print_rich_report,
    export_report_to_json,
    export_report_to_html,
    export_report_to_pdf,
    export_report_to_csv
)

app = typer.Typer(
    name="seoaudit",
    help="AI SEO Audit Toolkit - Crawler and auditing tool for website SEO signals.",
    add_completion=False
)
console = Console()

# Suppress insecure SSL warning logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@app.command()
def audit(
    url: str = typer.Argument(
        ...,
        help="The full URL (including scheme) of the page to audit."
    ),
    output_json: Optional[str] = typer.Option(
        None,
        "--output-json",
        "-o",
        help="Path to save single-page audit report as JSON."
    ),
    check_links: bool = typer.Option(
        False,
        "--check-links",
        "-c",
        help="Enable link health checks."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable diagnostic logging."
    )
) -> None:
    """Executes a legacy single-page SEO audit on the target URL."""
    setup_logging(verbose=verbose)
    
    if not is_valid_url(url):
        console.print(f"[bold red]Error:[/bold red] '{url}' is not a valid absolute URL.", style="red")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Crawl:[/bold cyan] Fetching single page HTML from {url}...")
    crawler = SafeCrawler()
    crawl_result = crawler.fetch_page(url)

    if not crawl_result.is_success:
        console.print(f"[bold red]Crawl Failed:[/bold red] {crawl_result.error_message}", style="red")
        raise typer.Exit(code=1)

    console.print("[bold cyan]Parse:[/bold cyan] Analyzing HTML structures...")
    parser = SEOHTMLParser(html_content=crawl_result.html, base_url=crawl_result.final_url)
    metadata = parser.parse_metadata()
    links = parser.get_links()
    images = parser.get_images()

    console.print("[bold cyan]Audit:[/bold cyan] Running quality checks...")
    # Mock site-level values to reuse auditor
    auditor = SEOAuditor(check_links=check_links, check_images=False)
    page_report = auditor.audit_page(
        crawl_result=crawl_result,
        metadata=metadata,
        links=links,
        images=images,
        robots_txt_found=True,
        sitemap_xml_found=False
    )
    
    # Render page details
    console.print(f"Page SEO Score: [bold green]{page_report.score}/100[/bold green]")
    for issue in page_report.issues:
        console.print(f" - [{issue.severity}] {issue.issue_type}: {issue.description}")
        
    if output_json:
        try:
            # Dump page_report as json
            Path(output_json).parent.mkdir(parents=True, exist_ok=True)
            with open(output_json, "w", encoding="utf-8") as f:
                f.write(page_report.model_dump_json(indent=2))
            console.print(f"[bold green]Saved JSON to {output_json}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]JSON Save Failed: {e}[/bold red]")


@app.command()
def crawl(
    url: str = typer.Argument(
        ...,
        help="The start URL (homepage) of the website to crawl."
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to the TOML configuration file."
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        help="Override maximum pages limit."
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--max-depth",
        help="Override crawl depth limit."
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory path for reports (overrides config paths)."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed diagnostic logs."
    )
) -> None:
    """Recursively crawls a website, runs SEO rules, and generates reports."""
    setup_logging(verbose=verbose)

    if not is_valid_url(url):
        console.print(f"[bold red]Error:[/bold red] '{url}' is not a valid absolute URL.", style="red")
        raise typer.Exit(code=1)

    # 1. Load configurations
    cfg = load_config(config_path)
    
    # CLI Overrides
    crawl_max_pages = max_pages if max_pages is not None else cfg.crawl.max_pages
    crawl_max_depth = max_depth if max_depth is not None else cfg.crawl.max_depth

    # 2. Check sitemap.xml on domain
    parsed_start = urlparse(url)
    origin = f"{parsed_start.scheme}://{parsed_start.netloc}"
    sitemap_xml_content = None
    try:
        sitemap_res = requests.get(f"{origin}/sitemap.xml", headers={"User-Agent": cfg.crawl.user_agent}, timeout=5, verify=False)
        if sitemap_res.status_code == 200:
            sitemap_xml_content = sitemap_res.text
            logger.info("Found and loaded sitemap.xml for orphan analysis.")
    except Exception:
        pass

    # Check robots.txt presence
    robots_found = False
    try:
        robots_res = requests.get(f"{origin}/robots.txt", headers={"User-Agent": cfg.crawl.user_agent}, timeout=5, verify=False)
        robots_found = (robots_res.status_code == 200)
    except Exception:
        pass

    # 3. Execute recursive crawling with progress bar
    safe_crawler = SafeCrawler(
        timeout=cfg.crawl.timeout,
        max_size_bytes=cfg.crawl.max_size,
        user_agent=cfg.crawl.user_agent,
        verify_ssl=cfg.crawl.verify_ssl
    )
    site_crawler = SiteCrawler(
        crawler=safe_crawler,
        max_pages=crawl_max_pages,
        max_depth=crawl_max_depth,
        respect_robots=True
    )

    pages_audited = []
    
    console.print(f"[bold cyan]Crawl:[/bold cyan] Initiating website crawl on {url} (limit: {crawl_max_pages} pages, depth: {crawl_max_depth})")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=console
    ) as progress:
        crawl_task = progress.add_task("[cyan]Crawling site pages...", total=crawl_max_pages)
        
        # Generator iteration
        for current_url, count, crawl_result, queue_size in site_crawler.crawl_site(url):
            # Update bar description
            short_url = current_url if len(current_url) <= 35 else f"{current_url[:32]}..."
            progress.update(
                crawl_task, 
                completed=count, 
                description=f"[cyan]Fetched: {short_url} (Queue: {queue_size})"
            )
            
            if not crawl_result or not crawl_result.is_success:
                continue

            # Run page parser and audit immediately on successful fetch
            parser = SEOHTMLParser(html_content=crawl_result.html, base_url=crawl_result.final_url)
            metadata = parser.parse_metadata()
            links = parser.get_links()
            images = parser.get_images()

            auditor = SEOAuditor(
                check_links=cfg.audit.check_links,
                check_images=cfg.audit.check_images,
                max_workers=cfg.audit.max_workers,
                timeout=cfg.crawl.timeout
            )
            page_report = auditor.audit_page(
                crawl_result=crawl_result,
                metadata=metadata,
                links=links,
                images=images,
                robots_txt_found=robots_found,
                sitemap_xml_found=(sitemap_xml_content is not None)
            )
            pages_audited.append(page_report)

    if not pages_audited:
        console.print("[bold red]Error:[/bold red] Visited zero valid HTML pages on the site.", style="red")
        raise typer.Exit(code=1)

    # 4. Generate Website Level Report
    console.print("[bold cyan]Audit:[/bold cyan] Performing site-wide duplicate content and asset validations...")
    site_auditor = SEOAuditor(
        check_links=cfg.audit.check_links,
        check_images=cfg.audit.check_images,
        max_workers=cfg.audit.max_workers,
        timeout=cfg.crawl.timeout
    )
    website_report = site_auditor.audit_website(
        start_url=url,
        pages=pages_audited,
        robots_txt_found=robots_found,
        sitemap_xml_found=(sitemap_xml_content is not None),
        sitemap_xml_content=sitemap_xml_content
    )

    # Print summary to terminal
    print_rich_report(website_report)

    # 5. Export Reports
    # Determine directory
    if output_dir:
        out_base = Path(output_dir)
        json_out = out_base / "seo_report.json"
        html_out = out_base / "seo_report.html"
        pdf_out = out_base / "seo_report.pdf"
        csv_out = out_base / "seo_report.csv"
    else:
        json_out = Path(cfg.output.json_path) if cfg.output.json_path else None
        html_out = Path(cfg.output.html_path) if cfg.output.html_path else None
        pdf_out = Path(cfg.output.pdf_path) if cfg.output.pdf_path else None
        csv_out = Path(cfg.output.csv_path) if cfg.output.csv_path else None

    # Exporters triggers
    if json_out:
        console.print(f" -> Exporting JSON: {json_out}")
        export_report_to_json(website_report, json_out)
    if html_out:
        console.print(f" -> Exporting HTML: {html_out}")
        export_report_to_html(website_report, html_out)
    if pdf_out:
        console.print(f" -> Exporting PDF:  {pdf_out}")
        export_report_to_pdf(website_report, pdf_out)
    if csv_out:
        console.print(f" -> Exporting CSV:  {csv_out}")
        export_report_to_csv(website_report, csv_out)

    console.print("\n[bold green]✓ Audit Completed Successfully![/bold green]")


def main():
    app()


if __name__ == "__main__":
    main()
