"""Exporting and rendering of site-level SEO reports in HTML, PDF, CSV, JSON, and Rich console layouts.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text

from ai_seo_audit.models import WebsiteAuditReport, IssueModel

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

console = Console()


def pdf_escape(text: Optional[str]) -> str:
    """Escapes XML special characters for ReportLab paragraphs."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")



def export_report_to_json(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Exports the full website audit report as a structured JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))


def export_report_to_csv(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Exports all discovered SEO issues into a CSV spreadsheet."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect all page issues and global site issues
    all_issues: List[IssueModel] = []
    for issue in report.site_issues:
        all_issues.append(issue)
    for p in report.pages:
        for issue in p.issues:
            all_issues.append(issue)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "URL", 
            "Severity", 
            "Issue Type", 
            "Description", 
            "HTML Snippet", 
            "CSS Selector", 
            "XPath", 
            "Recommendation"
        ])
        for issue in all_issues:
            writer.writerow([
                issue.url,
                issue.severity,
                issue.issue_type,
                issue.description,
                issue.html_snippet or "",
                issue.css_selector or "",
                issue.xpath or "",
                issue.recommendation
            ])


def export_report_to_html(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Generates a comprehensive HTML report with clustered issues and step-by-step fixes."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Collect all issues
    all_issues = list(report.site_issues)
    for p in report.pages:
        for issue in p.issues:
            all_issues.append(issue)

    # Stats
    total_issues = len(all_issues)
    critical_count = sum(1 for i in all_issues if i.severity == "CRITICAL")
    warning_count = sum(1 for i in all_issues if i.severity == "WARNING")
    info_count = total_issues - critical_count - warning_count
    score = report.score

    # Cluster issues by type
    issue_clusters = {}
    for issue in all_issues:
        key = issue.issue_type
        if key not in issue_clusters:
            issue_clusters[key] = {"issues": [], "severity": issue.severity, "recommendation": issue.recommendation}
        issue_clusters[key]["issues"].append(issue)

    # Sort clusters: critical first, then warning, then info
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    sorted_clusters = sorted(issue_clusters.items(), key=lambda x: (severity_order.get(x[1]["severity"], 3), -len(x[1]["issues"])))

    # Build clustered issues HTML
    cluster_html = ""
    for cluster_name, data in sorted_clusters:
        severity = data["severity"]
        issues_list = data["issues"]
        rec = data["recommendation"]
        count = len(issues_list)

        severity_colors = {"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "INFO": "#38bdf8"}
        severity_bg = {"CRITICAL": "rgba(239,68,68,0.08)", "WARNING": "rgba(245,158,11,0.08)", "INFO": "rgba(56,189,248,0.08)"}
        sev_color = severity_colors.get(severity, "#94a3b8")
        sev_bg = severity_bg.get(severity, "rgba(148,163,184,0.08)")

        # Fix steps based on issue type
        fix_steps = _get_fix_steps(cluster_name)

        affected_urls = list(set(i.url for i in issues_list))
        urls_html = ""
        for u in affected_urls[:5]:
            urls_html += f'<li><a href="{u}" target="_blank" style="color: #38bdf8;">{u}</a></li>'
        if len(affected_urls) > 5:
            urls_html += f'<li style="color: #94a3b8;">... and {len(affected_urls) - 5} more pages</li>'

        cluster_html += f"""
        <div style="background: {sev_bg}; border: 1px solid {sev_color}33; border-left: 4px solid {sev_color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: {sev_color};">{_severity_icon(severity)} {cluster_name}</h3>
                <span style="background: {sev_color}22; color: {sev_color}; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">{count} affected page{"s" if count > 1 else ""}</span>
            </div>
            <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1rem;">Severity: <strong style="color: {sev_color};">{severity}</strong></div>

            <div style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <strong style="color: #f1f5f9;">What this means:</strong>
                <p style="color: #94a3b8; margin: 0.5rem 0 0 0;">{_get_issue_description(cluster_name)}</p>
            </div>

            <div style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <strong style="color: #f1f5f9;">How to fix (step-by-step):</strong>
                <ol style="color: #94a3b8; margin: 0.5rem 0 0 0; padding-left: 1.2rem;">
                    {"".join(f'<li style="margin-bottom: 0.5rem;">{step}</li>' for step in fix_steps)}
                </ol>
            </div>

            <div style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <strong style="color: #f1f5f9;">Affected URLs ({len(affected_urls)}):</strong>
                <ul style="margin: 0.5rem 0 0 0; padding-left: 1.2rem;">{urls_html}</ul>
            </div>

            {f'<div style="background: rgba(34,197,94,0.05); border-left: 3px solid #22c55e; padding: 0.8rem 1rem; border-radius: 0 8px 8px 0;"><strong style="color: #22c55e;">Recommendation:</strong> <span style="color: #94a3b8;">{rec}</span></div>' if rec else ''}
        </div>
        """

    # Build page rows
    page_rows = ""
    for p in report.pages:
        p_critical = sum(1 for i in p.issues if i.severity == "CRITICAL")
        p_warning = sum(1 for i in p.issues if i.severity == "WARNING")
        sc = "#22c55e" if p.score >= 80 else ("#f59e0b" if p.score >= 60 else "#ef4444")
        page_rows += f"""
        <tr>
            <td><a href="{p.url}" target="_blank">{p.url}</a></td>
            <td><span class="badge status-{p.status_code}">{p.status_code}</span></td>
            <td><span style="color: #ef4444;">{p_critical} critical</span>, <span style="color: #f59e0b;">{p_warning} warnings</span></td>
            <td><strong style="color: {sc};">{p.score}/100</strong></td>
        </tr>
        """

    # Health checklist
    https_pct = sum(1 for p in report.pages if p.is_https) / max(1, len(report.pages)) * 100
    pages_with_title = sum(1 for p in report.pages if p.metadata.title) / max(1, len(report.pages)) * 100
    pages_with_meta = sum(1 for p in report.pages if p.metadata.meta_description) / max(1, len(report.pages)) * 100
    pages_with_h1 = sum(1 for p in report.pages if p.metadata.headings and any(h.level == 1 for h in p.metadata.headings)) / max(1, len(report.pages)) * 100

    def _health_bar(label, pct):
        color = "#22c55e" if pct > 90 else ("#f59e0b" if pct > 50 else "#ef4444")
        return f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
            <div style="width: 180px; color: #94a3b8;">{label}</div>
            <div style="flex: 1; background: #1e293b; border-radius: 6px; height: 12px; margin: 0 1rem;">
                <div style="width: {pct}%; background: {color}; height: 100%; border-radius: 6px;"></div>
            </div>
            <div style="width: 50px; text-align: right; color: {color}; font-weight: 600;">{pct:.0f}%</div>
        </div>
        """

    health_bars = ""
    health_bars += _health_bar("HTTPS Security", https_pct)
    health_bars += _health_bar("robots.txt", 100 if report.robots_txt_found else 0)
    health_bars += _health_bar("sitemap.xml", 100 if report.sitemap_xml_found else 0)
    health_bars += _health_bar("Title Tags", pages_with_title)
    health_bars += _health_bar("Meta Descriptions", pages_with_meta)
    health_bars += _health_bar("H1 Tags", pages_with_h1)

    # Priority action items
    priority_items = ""
    if critical_count > 0:
        priority_items += f'<div style="background: rgba(239,68,68,0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem;"><strong style="color: #ef4444;">🔴 Fix {critical_count} critical issue{"s" if critical_count > 1 else ""} first</strong> — These directly impact your SEO ranking and should be fixed immediately.</div>'
    if warning_count > 0:
        priority_items += f'<div style="background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem;"><strong style="color: #f59e0b;">🟡 Fix {warning_count} warning{"s" if warning_count > 1 else ""} next</strong> — These improve your SEO when fixed.</div>'
    if not report.robots_txt_found:
        priority_items += '<div style="background: rgba(239,68,68,0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem;"><strong style="color: #ef4444;">🔴 Create robots.txt</strong> — Missing robots.txt prevents search engines from understanding your crawl rules.</div>'
    if not report.sitemap_xml_found:
        priority_items += '<div style="background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem;"><strong style="color: #f59e0b;">🟡 Create sitemap.xml</strong> — Missing sitemap helps search engines discover all your pages.</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Audit Report — {report.start_url}</title>
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --border: rgba(255,255,255,0.1); --text: #f1f5f9; --muted: #94a3b8; --primary: #38bdf8; --critical: #ef4444; --warning: #f59e0b; --pass: #22c55e; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem; }}
        header {{ background: linear-gradient(135deg, #1e293b, #0f172a); padding: 2.5rem; text-align: center; border-bottom: 1px solid var(--border); }}
        header h1 {{ font-size: 2.2rem; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        header p {{ color: var(--muted); }}
        .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .score-circle {{ width: 130px; height: 130px; border-radius: 50%; border: 8px solid #1e293b; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; margin: 0 auto 1rem; }}
        .badge {{ padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }}
        .status-200 {{ background: rgba(34,197,94,0.2); color: var(--pass); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.8rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: rgba(30,41,59,0.9); color: var(--primary); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; }}
        a {{ color: var(--primary); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        h2 {{ border-left: 4px solid var(--primary); padding-left: 12px; margin: 2rem 0 1rem; font-size: 1.5rem; }}
        h3 {{ margin-bottom: 0.5rem; }}
        @media print {{ body {{ background: white; color: #1e293b; }} .card {{ border: 1px solid #e2e8f0; background: white; }} header {{ background: #f8fafc; }} }}
    </style>
</head>
<body>
    <header>
        <h1>SEO Audit Report</h1>
        <p>{report.start_url} | {report.total_pages_crawled} pages crawled | Generated: {report.generated_at}</p>
    </header>
    <div class="container">

        <!-- SCORE -->
        <div style="text-align: center; margin-bottom: 2rem;">
            <div class="score-circle" style="border-color: {get_score_color_hsl(score)}; color: {get_score_color_hsl(score)};">{score}%</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: {get_score_color_hsl(score)};">{get_score_description(score)}</div>
        </div>

        <!-- KEY METRICS -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            <div class="card" style="text-align: center;"><div style="font-size: 1.8rem; font-weight: 700;">{report.total_pages_crawled}</div><div style="color: var(--muted); font-size: 0.8rem; text-transform: uppercase;">Pages</div></div>
            <div class="card" style="text-align: center;"><div style="font-size: 1.8rem; font-weight: 700; color: var(--critical);">{critical_count}</div><div style="color: var(--muted); font-size: 0.8rem; text-transform: uppercase;">Critical</div></div>
            <div class="card" style="text-align: center;"><div style="font-size: 1.8rem; font-weight: 700; color: var(--warning);">{warning_count}</div><div style="color: var(--muted); font-size: 0.8rem; text-transform: uppercase;">Warnings</div></div>
            <div class="card" style="text-align: center;"><div style="font-size: 1.8rem; font-weight: 700; color: var(--primary);">{total_issues}</div><div style="color: var(--muted); font-size: 0.8rem; text-transform: uppercase;">Total Issues</div></div>
        </div>

        <!-- HEALTH BARS -->
        <div class="card">
            <h2 style="margin-top: 0;">Site Health</h2>
            {health_bars}
        </div>

        <!-- PRIORITY ACTIONS -->
        <div class="card">
            <h2 style="margin-top: 0;">Priority Actions</h2>
            {priority_items if priority_items else '<p style="color: var(--muted);">No critical priority actions. Your site is in good shape!</p>'}
        </div>

        <!-- CLUSTERED ISSUES -->
        <h2>Issues by Category ({len(sorted_clusters)} types, {total_issues} total)</h2>
        {cluster_html if cluster_html else '<div class="card"><p style="color: var(--pass);">No issues found! Your site is well optimized.</p></div>'}

        <!-- PAGES TABLE -->
        <h2>All Crawled Pages</h2>
        <div class="card" style="padding: 0; overflow-x: auto;">
            <table>
                <thead><tr><th>URL</th><th>Status</th><th>Issues</th><th>Score</th></tr></thead>
                <tbody>{page_rows}</tbody>
            </table>
        </div>

    </div>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)


def _severity_icon(severity):
    """Return icon for severity."""
    return {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")


def _get_issue_description(issue_type):
    """Return plain-English description for issue type."""
    descriptions = {
        "Missing Title Tag": "Your page doesn't have a title tag. Search engines use this to understand what the page is about and display it in search results.",
        "Missing Meta Description": "Your page doesn't have a meta description. This is the short text shown under your page in search results.",
        "Missing H1 Heading": "Your page doesn't have an H1 heading. This is the main heading that tells search engines the primary topic of the page.",
        "Missing Viewport Tag": "Your page doesn't have a viewport meta tag. This means it may not display correctly on mobile devices.",
        "Missing Lang Attribute": "Your HTML tag doesn't specify a language. This helps search engines serve the right content to the right audience.",
        "Missing Favicon": "Your page doesn't have a favicon. This is the small icon shown in browser tabs.",
        "Missing Canonical Tag": "Your page doesn't have a canonical tag. This tells search engines which URL is the preferred version of this page.",
        "HTTPS Security": "Some pages are not using HTTPS. Google gives preference to secure sites.",
        "Invalid JSON-LD": "Your page has structured data (JSON-LD) that contains errors. Search engines can't read it properly.",
        "Broken Link": "Your page contains links to URLs that don't work (404 errors). This hurts user experience and SEO.",
        "Duplicate Content": "Multiple pages have very similar content. Search engines may not know which one to show in results.",
        "Duplicate Titles": "Multiple pages share the same title tag. Each page should have a unique title.",
        "Duplicate Descriptions": "Multiple pages share the same meta description. Each page should have a unique description.",
        "Orphan Page": "This page exists in your sitemap but isn't linked from any other page on your site.",
        "Image Missing Alt Text": "An image doesn't have alt text. Search engines can't understand what the image shows.",
        "Empty Anchor Text": "A link has no text content. Screen readers and search engines can't understand where it goes.",
        "Thin Content": "This page has very little content. Pages with thin content rank poorly in search results.",
        "Missing robots.txt": "Your site doesn't have a robots.txt file. This tells search engines which pages to crawl.",
        "Missing sitemap.xml": "Your site doesn't have a sitemap.xml. This helps search engines discover all your pages.",
        "Heading Hierarchy Issue": "Your headings skip levels (e.g., H1 to H3 without H2). This confuses search engines.",
        "Images Without Lazy Loading": "Images don't use lazy loading. This slows down page load time.",
        "Mixed Content": "Your HTTPS page loads resources (images, scripts) over HTTP. This creates security warnings.",
        "Security Header Missing": "Your site is missing important security headers that protect users.",
    }
    return descriptions.get(issue_type, f"This is a {issue_type} issue that needs to be addressed for better SEO performance.")


def _get_fix_steps(issue_type):
    """Return step-by-step fix instructions for issue type."""
    steps = {
        "Missing Title Tag": [
            "Open your page's HTML file or CMS editor",
            'Add a title tag in the &lt;head&gt; section: &lt;title&gt;Your Keyword-Rich Title&lt;/title&gt;',
            "Keep it under 60 characters",
            "Include your main keyword near the beginning",
            "Save and republish the page"
        ],
        "Missing Meta Description": [
            "Open your page's HTML or CMS editor",
            'Add in the &lt;head&gt;: &lt;meta name="description" content="Your description here"&gt;',
            "Keep it between 150-160 characters",
            "Include your target keyword naturally",
            "Make it compelling — this is your ad in search results"
        ],
        "Missing H1 Heading": [
            "Open your page content",
            "Add one H1 heading that describes the page topic",
            'Use: &lt;h1&gt;Your Main Topic&lt;/h1&gt;',
            "Include your primary keyword in the H1",
            "Only use ONE H1 per page"
        ],
        "Missing Viewport Tag": [
            "Open your page's HTML file",
            'Add in &lt;head&gt;: &lt;meta name="viewport" content="width=device-width, initial-scale=1.0"&gt;',
            "Save and test on mobile devices",
            "Use Google's Mobile-Friendly Test to verify"
        ],
        "Missing Canonical Tag": [
            "Open your page's HTML file",
            'Add in &lt;head&gt;: &lt;link rel="canonical" href="https://yoursite.com/this-page"&gt;',
            "Use the URL of the preferred version of this page",
            "If using WordPress, most SEO plugins handle this automatically"
        ],
        "Invalid JSON-LD": [
            "Copy the JSON-LD code from your page",
            "Go to https://validator.schema.org/",
            "Paste and validate the code",
            "Fix any JSON syntax errors (missing commas, brackets)",
            "Ensure @context is set to https://schema.org",
            "Re-validate until it passes"
        ],
        "Broken Link": [
            "Find the broken link on your page",
            "Either update it to point to the correct URL",
            "Or remove the link if the destination no longer exists",
            "Consider adding a 301 redirect if the page moved",
            "Check for typos in the URL"
        ],
        "Duplicate Content": [
            "Choose one URL as the canonical (preferred) version",
            "Add a canonical tag on the duplicate pages pointing to the preferred URL",
            "OR add a 301 redirect from duplicates to the canonical",
            "Consider merging very similar pages into one comprehensive page"
        ],
        "Orphan Page": [
            "Add internal links to this page from other relevant pages",
            "Include it in your site's navigation menu",
            "Add it to your sitemap.xml",
            "Link to it from related blog posts or content"
        ],
        "Image Missing Alt Text": [
            "Open your page editor",
            "Find the image tag",
            'Add descriptive alt text: &lt;img src="..." alt="Description of image"&gt;',
            "Describe what the image shows, include keywords naturally",
            "Keep it under 125 characters"
        ],
        "Missing robots.txt": [
            "Create a file named robots.txt in your site root",
            "Add basic content: User-agent: * / Allow: /",
            "Upload to https://yoursite.com/robots.txt",
            "Test at https://www.google.com/robots.txt for examples"
        ],
        "Missing sitemap.xml": [
            "Create an XML sitemap listing all your pages",
            "Use a sitemap generator tool or SEO plugin",
            "Upload to your site root: https://yoursite.com/sitemap.xml",
            "Submit it to Google Search Console",
            "Reference it in your robots.txt: Sitemap: https://yoursite.com/sitemap.xml"
        ],
        "Mixed Content": [
            "Find all HTTP resources on your HTTPS page",
            "Change all internal links from http:// to https://",
            "Update image sources, script sources, and stylesheet links",
            "Use protocol-relative URLs if needed: //yoursite.com/image.png",
            "Test with a mixed content checker tool"
        ],
    }
    return steps.get(issue_type, [
        "Review the issue description to understand what needs to be fixed",
        "Open your page in the CMS or code editor",
        "Apply the recommended fix",
        "Save and test the page",
        "Re-run the audit to confirm the issue is resolved"
    ])


def export_report_to_pdf(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Exports a professional PDF report with Table of Contents, Overall Details, Clustered Errors, and Fix Guides."""
    from ai_seo_audit.fix_guides import get_fix_guide_as_markdown
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=30
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Header3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#090d16'),
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=5,
        spaceAfter=6
    )

    recommendation_style = ParagraphStyle(
        'Recommendation',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#15803d'),
        spaceAfter=6
    )

    toc_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        leftIndent=20,
        spaceAfter=4
    )

    toc_header_style = ParagraphStyle(
        'TOCHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )

    story = []

    # Collect all issues
    all_issues = list(report.site_issues)
    for p in report.pages:
        for issue in p.issues:
            all_issues.append(issue)

    # Cluster issues by type
    issue_clusters = {}
    for issue in all_issues:
        key = issue.issue_type
        if key not in issue_clusters:
            issue_clusters[key] = []
        issue_clusters[key].append(issue)

    # Sort clusters by severity (CRITICAL first)
    def cluster_severity(cluster_key):
        issues = issue_clusters[cluster_key]
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        return (0 if has_critical else 1, -len(issues))
    
    sorted_clusters = sorted(issue_clusters.keys(), key=cluster_severity)

    # Stats
    total_issues = len(all_issues)
    critical_count = sum(1 for i in all_issues if i.severity == "CRITICAL")
    warning_count = sum(1 for i in all_issues if i.severity == "WARNING")
    pages_with_issues = len(set(i.url for i in all_issues))

    # --- COVER PAGE ---
    story.append(Spacer(1, 100))
    story.append(Paragraph("AI WEBSITE SEO AUDIT REPORT", title_style))
    story.append(Paragraph(f"Audited Target: {pdf_escape(report.start_url)}", subtitle_style))
    story.append(Spacer(1, 50))

    # Score Panel
    score = report.score
    score_text = f"<b>SEO Score: {score}/100</b>"
    if score >= 90:
        panel_color = colors.HexColor('#dcfce7')
        text_color = colors.HexColor('#15803d')
    elif score >= 70:
        panel_color = colors.HexColor('#fef9c3')
        text_color = colors.HexColor('#a16207')
    else:
        panel_color = colors.HexColor('#fee2e2')
        text_color = colors.HexColor('#b91c1c')

    score_panel_style = ParagraphStyle(
        'ScorePanel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=text_color,
        alignment=1
    )

    score_table = Table([[Paragraph(score_text, score_panel_style)]], colWidths=[250])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), panel_color),
        ('PADDING', (0,0), (-1,-1), 15),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1.5, text_color),
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 150))
    story.append(Paragraph(f"Generated at: {report.generated_at} (UTC)", subtitle_style))
    story.append(PageBreak())

    # --- TABLE OF CONTENTS ---
    story.append(Paragraph("Table of Contents", h1_style))
    story.append(Spacer(1, 10))

    # TOC entries
    toc_entries = [
        ("1. Overall Site Details", "Summary of site health and key metrics"),
        ("2. Executive Summary", "Pages crawled, issues found, and score breakdown"),
        ("3. Issue Clusters by Type", f"{len(sorted_clusters)} unique issue types found"),
        ("4. Detailed Fix Guides", "Step-by-step instructions for each issue type"),
    ]

    for title, desc in toc_entries:
        story.append(Paragraph(f"<b>{title}</b>", toc_header_style))
        story.append(Paragraph(f"  {desc}", toc_style))
        story.append(Spacer(1, 6))

    # Issue cluster TOC
    story.append(Spacer(1, 10))
    story.append(Paragraph("Issue Types Summary", h2_style))
    
    toc_cluster_data = [
        [Paragraph("<b>Issue Type</b>", body_style), 
         Paragraph("<b>Count</b>", body_style), 
         Paragraph("<b>Severity</b>", body_style)]
    ]
    for cluster_key in sorted_clusters[:20]:  # Show top 20
        issues = issue_clusters[cluster_key]
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        sev = "CRITICAL" if has_critical else "WARNING"
        sev_color = "red" if has_critical else "orange"
        toc_cluster_data.append([
            Paragraph(pdf_escape(cluster_key), body_style),
            Paragraph(str(len(issues)), body_style),
            Paragraph(f"<font color='{sev_color}'>{sev}</font>", body_style),
        ])
    
    toc_cluster_table = Table(toc_cluster_data, colWidths=[250, 60, 80])
    toc_cluster_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(toc_cluster_table)
    story.append(PageBreak())

    # --- OVERALL SITE DETAILS ---
    story.append(Paragraph("1. Overall Site Details", h1_style))
    story.append(Spacer(1, 10))

    # Site info table
    https_pct = sum(1 for p in report.pages if p.is_https) / max(1, len(report.pages)) * 100
    site_info_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Website URL", body_style), Paragraph(pdf_escape(report.start_url), body_style)],
        [Paragraph("SEO Score", body_style), Paragraph(f"<b>{score}/100</b>", body_style)],
        [Paragraph("Pages Crawled", body_style), Paragraph(str(report.total_pages_crawled), body_style)],
        [Paragraph("HTTPS Enabled", body_style), Paragraph(f"Yes ({https_pct:.0f}%)" if https_pct == 100 else f"Partial ({https_pct:.0f}%)", body_style)],
        [Paragraph("robots.txt Found", body_style), Paragraph("Yes" if report.robots_txt_found else "No", body_style)],
        [Paragraph("sitemap.xml Found", body_style), Paragraph("Yes" if report.sitemap_xml_found else "No", body_style)],
    ]
    site_info_table = Table(site_info_data, colWidths=[200, 250])
    site_info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(site_info_table)
    story.append(Spacer(1, 15))

    # Health metrics
    story.append(Paragraph("Site Health Summary", h2_style))
    
    pages_with_title = sum(1 for p in report.pages if p.metadata.title)
    title_pct = pages_with_title / max(1, len(report.pages)) * 100
    pages_with_meta = sum(1 for p in report.pages if p.metadata.meta_description)
    meta_pct = pages_with_meta / max(1, len(report.pages)) * 100
    pages_with_h1 = sum(1 for p in report.pages if any(h.level == 1 for h in p.metadata.headings))
    h1_pct = pages_with_h1 / max(1, len(report.pages)) * 100
    pages_with_canonical = sum(1 for p in report.pages if p.metadata.canonical_url)
    canonical_pct = pages_with_canonical / max(1, len(report.pages)) * 100

    health_data = [
        [Paragraph("<b>Health Check</b>", body_style), 
         Paragraph("<b>Status</b>", body_style),
         Paragraph("<b>Percentage</b>", body_style)],
        [Paragraph("HTTPS Security", body_style),
         Paragraph("✅ Pass" if https_pct == 100 else "⚠️ Partial", body_style),
         Paragraph(f"{https_pct:.1f}%", body_style)],
        [Paragraph("Title Tags", body_style),
         Paragraph("✅ Good" if title_pct > 80 else "⚠️ Needs Work", body_style),
         Paragraph(f"{title_pct:.1f}%", body_style)],
        [Paragraph("Meta Descriptions", body_style),
         Paragraph("✅ Good" if meta_pct > 80 else "⚠️ Needs Work", body_style),
         Paragraph(f"{meta_pct:.1f}%", body_style)],
        [Paragraph("H1 Headings", body_style),
         Paragraph("✅ Good" if h1_pct > 80 else "⚠️ Needs Work", body_style),
         Paragraph(f"{h1_pct:.1f}%", body_style)],
        [Paragraph("Canonical Tags", body_style),
         Paragraph("✅ Good" if canonical_pct > 80 else "⚠️ Needs Work", body_style),
         Paragraph(f"{canonical_pct:.1f}%", body_style)],
    ]
    health_table = Table(health_data, colWidths=[180, 120, 100])
    health_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(health_table)
    story.append(Spacer(1, 15))

    # Issue distribution
    story.append(Paragraph("Issue Distribution", h2_style))
    issue_dist_data = [
        [Paragraph("<b>Severity</b>", body_style), 
         Paragraph("<b>Count</b>", body_style),
         Paragraph("<b>Percentage</b>", body_style)],
        [Paragraph("🔴 Critical", body_style),
         Paragraph(str(critical_count), body_style),
         Paragraph(f"{critical_count/max(1,total_issues)*100:.1f}%", body_style)],
        [Paragraph("🟡 Warning", body_style),
         Paragraph(str(warning_count), body_style),
         Paragraph(f"{warning_count/max(1,total_issues)*100:.1f}%", body_style)],
        [Paragraph("📊 Total", body_style),
         Paragraph(str(total_issues), body_style),
         Paragraph("100%", body_style)],
    ]
    issue_dist_table = Table(issue_dist_data, colWidths=[150, 100, 100])
    issue_dist_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(issue_dist_table)
    story.append(PageBreak())

    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("2. Executive Summary", h1_style))
    story.append(Paragraph(
        f"This report presents a comprehensive SEO audit of <b>{pdf_escape(report.start_url)}</b>. "
        f"The analysis covers <b>{report.total_pages_crawled}</b> pages and identified "
        f"<b>{total_issues}</b> issues across <b>{pages_with_issues}</b> pages.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Key findings
    story.append(Paragraph("Key Findings", h2_style))
    findings = []
    if critical_count > 0:
        findings.append(f"<b>{critical_count} Critical Issues</b> requiring immediate attention")
    if warning_count > 0:
        findings.append(f"<b>{warning_count} Warnings</b> that should be addressed")
    if len(report.duplicate_pages) > 0:
        findings.append(f"<b>{len(report.duplicate_pages)} Duplicate Content Sets</b> found")
    if len(report.orphan_pages) > 0:
        findings.append(f"<b>{len(report.orphan_pages)} Orphan Pages</b> not linked from other pages")
    if len(report.redirect_chains) > 0:
        findings.append(f"<b>{len(report.redirect_chains)} Redirect Chains</b> detected")
    
    for finding in findings:
        story.append(Paragraph(f"  •  {finding}", body_style))
    story.append(PageBreak())

    # --- ISSUE CLUSTERS BY TYPE ---
    story.append(Paragraph("3. Issue Clusters by Type", h1_style))
    story.append(Paragraph(
        f"Issues have been grouped into <b>{len(sorted_clusters)}</b> unique categories for easier management.",
        body_style
    ))
    story.append(Spacer(1, 10))

    for cluster_key in sorted_clusters:
        issues = issue_clusters[cluster_key]
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        
        # Cluster header
        sev_icon = "🔴" if has_critical else "🟡"
        story.append(Paragraph(f"{sev_icon} {cluster_key} ({len(issues)} pages)", h2_style))
        
        # Sample issue description
        sample = issues[0]
        story.append(Paragraph(f"<b>Description:</b> {pdf_escape(sample.description)}", body_style))
        story.append(Paragraph(f"<b>Recommendation:</b> {pdf_escape(sample.recommendation)}", recommendation_style))
        story.append(Spacer(1, 5))
        
        # Affected URLs (show first 10)
        url_data = [
            [Paragraph("<b>Affected URLs</b>", body_style)]
        ]
        for issue in issues[:10]:
            url_data.append([Paragraph(pdf_escape(issue.url), body_style)])
        if len(issues) > 10:
            url_data.append([Paragraph(f"... and {len(issues) - 10} more", body_style)])
        
        url_table = Table(url_data, colWidths=[450])
        url_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fef2f2') if has_critical else colors.HexColor('#fef9c3')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        story.append(url_table)
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())

    # --- DETAILED FIX GUIDES ---
    story.append(Paragraph("4. Detailed Fix Guides", h1_style))
    story.append(Paragraph(
        "Step-by-step instructions to resolve each issue type. Follow these guides to improve your SEO score.",
        body_style
    ))
    story.append(Spacer(1, 10))

    for cluster_key in sorted_clusters:
        issues = issue_clusters[cluster_key]
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        
        # Get fix guide
        try:
            guide = get_fix_guide_as_markdown(cluster_key)
        except:
            guide = None
        
        if guide and "No fix guide available" not in guide:
            sev_icon = "🔴" if has_critical else "🟡"
            story.append(Paragraph(f"{sev_icon} Fix Guide: {cluster_key}", h2_style))
            
            # Parse guide into sections - escape all HTML tags
            guide_lines = guide.split('\n')
            for line in guide_lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('## '):
                    story.append(Paragraph(pdf_escape(line[3:]), h3_style))
                elif line.startswith('### '):
                    story.append(Paragraph(pdf_escape(line[4:]), h3_style))
                elif line.startswith('**'):
                    # Bold text - escape and use plain text
                    clean = line.replace('**', '').replace('*', '')
                    story.append(Paragraph(f"<b>{pdf_escape(clean)}</b>", body_style))
                elif line.startswith('- '):
                    story.append(Paragraph(f"  •  {pdf_escape(line[2:])}", body_style))
                elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    story.append(Paragraph(f"  {pdf_escape(line)}", body_style))
                elif line.startswith('```'):
                    # Skip code block markers
                    continue
                elif '<' in line and '>' in line:
                    # Code snippet - escape HTML
                    story.append(Paragraph(pdf_escape(line), code_style))
                else:
                    story.append(Paragraph(pdf_escape(line), body_style))
            
            story.append(Spacer(1, 15))
    
    doc.build(story)


def build_html_issue_card(issue: IssueModel) -> str:
    """Builds a HTML issue card element."""
    severity_class = f"badge-severity-{issue.severity.lower()}"
    html = f"""
    <div class="issue-card">
        <div class="issue-header">
            <h4 class="issue-title">{issue.issue_type}</h4>
            <span class="badge {severity_class}">{issue.severity}</span>
        </div>
        <div class="issue-meta"><strong>Location URL:</strong> <a href="{issue.url}" target="_blank">{issue.url}</a></div>
    """
    if issue.css_selector:
        html += f'<div class="issue-meta"><strong>CSS Selector:</strong> <code>{issue.css_selector}</code></div>'
    if issue.xpath:
        html += f'<div class="issue-meta"><strong>XPath:</strong> <code>{issue.xpath}</code></div>'
    
    if issue.html_snippet:
        snippet_escaped = issue.html_snippet.replace("<", "&lt;").replace(">", "&gt;")
        html += f'<div class="code-block">{snippet_escaped}</div>'

    html += f"""
        <p style="margin: 0.5rem 0;">{issue.description}</p>
        <div class="recommendation-box">
            <strong>Recommendation:</strong> {issue.recommendation}
        </div>
    </div>
    """
    return html


def print_rich_report(report: WebsiteAuditReport) -> None:
    """Outputs a summarized version of the site-wide report to the terminal."""
    # Print Dashboard Header
    title_text = Text()
    title_text.append("AI SEO Website Crawler & Auditor ", style="bold cyan")
    title_text.append(f"v2.0.0\n", style="dim")
    title_text.append(f"Root Target: ", style="bold white")
    title_text.append(f"{report.start_url}\n", style="underline blue")
    title_text.append(f"Total Crawled: {report.total_pages_crawled} pages", style="italic dim")

    console.print(Panel(title_text, border_style="cyan"))

    # Score assessment
    score = report.score
    if score >= 90:
        score_color = "bold green"
    elif score >= 70:
        score_color = "bold yellow"
    else:
        score_color = "bold red"

    score_text = Text()
    score_text.append("Website-Level Score: ", style="bold white")
    score_text.append(f"{score}/100\n", style=score_color)
    
    filled = int(score / 5)
    score_text.append("[" + "=" * filled + "-" * (20 - filled) + "]", style=score_color)
    console.print(Panel(score_text, title="Score Assessment", border_style="cyan"))

    # Table of Pages
    pages_table = RichTable(title="Pages Crawl Summary", show_header=True, header_style="bold blue")
    pages_table.add_column("Page URL", style="bold white", width=55)
    pages_table.add_column("HTTP Status", justify="center", width=12)
    pages_table.add_column("Issues count", justify="right", width=15)
    pages_table.add_column("Page Score", justify="right", width=12)

    for p in report.pages[:15]: # Show up to 15 pages in terminal
        pages_table.add_row(
            p.url,
            str(p.status_code),
            str(len(p.issues)),
            f"{p.score}/100"
        )
    if len(report.pages) > 15:
        pages_table.add_row("... and other pages", "", "", "")
    console.print(pages_table)
    console.print()

    # Table of site-wide metrics/issues
    total_issues = len(report.site_issues) + sum(len(p.issues) for p in report.pages)
    console.print(f"[bold magenta]Global Findings Summary:[/bold magenta]")
    console.print(f" - Duplicate Content Groups: [bold yellow]{len(report.duplicate_pages)}[/bold yellow]")
    console.print(f" - Duplicate Titles Identified: [bold yellow]{len(report.duplicate_titles)}[/bold yellow]")
    console.print(f" - Duplicate Descriptions Identified: [bold yellow]{len(report.duplicate_descriptions)}[/bold yellow]")
    console.print(f" - Orphan Pages in Sitemap: [bold yellow]{len(report.orphan_pages)}[/bold yellow]")
    console.print(f" - Total issues logged: [bold cyan]{total_issues}[/bold cyan]")
    console.print()


def get_score_color_hsl(score: int) -> str:
    """Returns color string (HSL format) corresponding to the SEO score."""
    if score >= 90: return "#22c55e" # Green
    if score >= 70: return "#f59e0b" # Yellow
    return "#ef4444" # Red


def get_score_description(score: int) -> str:
    """Returns classification string for the score."""
    if score >= 90: return "Excellent Health"
    if score >= 70: return "Satisfactory Health"
    return "Needs Immediate Remediation"


def export_report_to_xml_sitemap(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Generates a valid XML sitemap from the crawled pages."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build priority based on score and depth
    def _get_priority(url: str, score: int) -> str:
        if url.rstrip("/") == report.start_url.rstrip("/"):
            return "1.0"
        if score >= 80:
            return "0.8"
        if score >= 60:
            return "0.6"
        return "0.4"

    # Build changefreq based on page type
    def _get_changefreq(url: str) -> str:
        url_lower = url.lower()
        if any(w in url_lower for w in ["blog", "news", "post", "article"]):
            return "weekly"
        if any(w in url_lower for w in ["product", "shop", "store", "price"]):
            return "daily"
        if any(w in url_lower for w in ["about", "contact", "team", "company"]):
            return "monthly"
        return "weekly"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for page in report.pages:
        priority = _get_priority(page.url, page.score)
        changefreq = _get_changefreq(page.url)

        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{_xml_escape(page.url)}</loc>")
        xml_lines.append(f"    <lastmod>{now}</lastmod>")
        xml_lines.append(f"    <changefreq>{changefreq}</changefreq>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append("  </url>")

    xml_lines.append("</urlset>")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))


def _xml_escape(text: str) -> str:
    """Escapes XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
