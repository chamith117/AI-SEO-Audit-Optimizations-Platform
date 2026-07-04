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
    """Generates a premium, responsive HTML dashboard report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Accumulate stats
    total_issues = len(report.site_issues) + sum(len(p.issues) for p in report.pages)
    critical_count = sum(1 for issue in report.site_issues if issue.severity == "CRITICAL") + \
                     sum(sum(1 for i in p.issues if i.severity == "CRITICAL") for p in report.pages)
    warning_count = sum(1 for issue in report.site_issues if issue.severity == "WARNING") + \
                    sum(sum(1 for i in p.issues if i.severity == "WARNING") for p in report.pages)
    
    # Compile page rows
    page_rows_html = ""
    for p in report.pages:
        issues_summary = f"{len(p.issues)} issues ({sum(1 for i in p.issues if i.severity == 'CRITICAL')} critical)"
        page_rows_html += f"""
        <tr>
            <td><a href="{p.url}" target="_blank">{p.url}</a></td>
            <td><span class="badge status-{p.status_code}">{p.status_code}</span></td>
            <td>{issues_summary}</td>
            <td><strong style="color: {get_score_color_hsl(p.score)}">{p.score}/100</strong></td>
        </tr>
        """

    # Compile issue cards
    issue_cards_html = ""
    # Global site issues first
    for issue in report.site_issues:
        issue_cards_html += build_html_issue_card(issue)
    # Page-specific issues
    for p in report.pages:
        for issue in p.issues:
            issue_cards_html += build_html_issue_card(issue)

    # Overall score variables
    score = report.score
    score_color = get_score_color_hsl(score)

    # Build keyword section if keyword research data exists
    keyword_section_html = ""
    if report.keyword_research:
        kw = report.keyword_research
        kw_rows = ""
        for k in kw.primary_keywords[:15]:
            kw_rows += f"""
            <tr>
                <td><strong>{k.keyword}</strong></td>
                <td>{k.count}</td>
                <td>{k.density}%</td>
                <td>{'Yes' if k.in_title else '-'}</td>
                <td>{'Yes' if k.in_meta_desc else '-'}</td>
                <td>{'Yes' if k.in_headings else '-'}</td>
                <td>{len(k.pages)}</td>
            </tr>
            """

        lsi_rows = ""
        for k in kw.lsi_keywords[:10]:
            lsi_rows += f"<tr><td>{k.keyword}</td><td>{k.count}</td><td>{k.density}%</td></tr>"

        gap_items = ""
        for g in kw.keyword_gaps:
            gap_items += f"<li><strong>{g}</strong></li>"

        keyword_section_html = f"""
        <h2>Keyword Research</h2>
        <div class="card" style="padding: 1rem 1.5rem; margin-bottom: 2rem;">
            <p style="color: var(--text-muted);">Total words analyzed: <strong>{kw.total_words_analyzed}</strong> | Unique words: <strong>{kw.unique_words_found}</strong></p>
        </div>
        <h3 style="color: var(--primary);">Primary Keywords</h3>
        <div class="card" style="padding: 0; overflow-x: auto; margin-bottom: 2rem;">
            <table>
                <thead>
                    <tr>
                        <th>Keyword</th>
                        <th>Count</th>
                        <th>Density</th>
                        <th>In Title</th>
                        <th>In Meta</th>
                        <th>In Headings</th>
                        <th>Pages</th>
                    </tr>
                </thead>
                <tbody>
                    {kw_rows}
                </tbody>
            </table>
        </div>
        <h3 style="color: var(--primary);">LSI Keywords</h3>
        <div class="card" style="padding: 0; overflow-x: auto; margin-bottom: 2rem;">
            <table>
                <thead>
                    <tr>
                        <th>LSI Keyword</th>
                        <th>Count</th>
                        <th>Density</th>
                    </tr>
                </thead>
                <tbody>
                    {lsi_rows}
                </tbody>
            </table>
        </div>
        <h3 style="color: var(--primary);">Keyword Gaps</h3>
        <div class="card" style="margin-bottom: 2rem;">
            <ul style="list-style-type: disc; padding-left: 1.5rem; color: var(--text-muted);">
                {gap_items}
            </ul>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI SEO Audit Report - {report.start_url}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-color: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --critical: #ef4444;
            --warning: #f59e0b;
            --pass: #22c55e;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 2.5rem 2rem;
            border-bottom: 1px solid var(--border-color);
            text-align: center;
        }}
        header h1 {{
            margin: 0 0 0.5rem 0;
            font-size: 2.5rem;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        header p {{
            margin: 0;
            color: var(--text-muted);
            font-size: 1.1rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}
        .grid-dashboard {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        @media(max-width: 768px) {{
            .grid-dashboard {{ grid-template-columns: 1fr; }}
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(12px);
        }}
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 10px solid #1e293b;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            font-weight: 800;
            margin: 1rem auto;
            box-shadow: 0 0 30px rgba(56, 189, 248, 0.1);
        }}
        .score-desc {{
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }}
        .stat-box {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid var(--border-color);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }}
        .stat-label {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        h2 {{
            border-left: 4px solid var(--primary);
            padding-left: 10px;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
        }}
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: rgba(30, 41, 59, 0.9);
            color: var(--primary);
            font-weight: 600;
        }}
        tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        a {{
            color: var(--primary);
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        .status-200 {{ background-color: rgba(34, 197, 94, 0.2); color: var(--pass); }}
        .badge-severity-critical {{ background-color: rgba(239, 68, 68, 0.2); color: var(--critical); border: 1px solid var(--critical); }}
        .badge-severity-warning {{ background-color: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); }}
        .badge-severity-info {{ background-color: rgba(56, 189, 248, 0.2); color: var(--primary); border: 1px solid var(--primary); }}
        .issue-card {{
            border: 1px solid var(--border-color);
            background: rgba(30, 41, 59, 0.4);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .issue-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
        }}
        .code-block {{
            background: #090d16;
            padding: 1rem;
            border-radius: 6px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            border: 1px solid var(--border-color);
            margin: 0.8rem 0;
        }}
        .issue-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}
        .recommendation-box {{
            background: rgba(34, 197, 94, 0.05);
            border-left: 3px solid var(--pass);
            padding: 0.8rem 1rem;
            margin-top: 1rem;
            border-radius: 0 6px 6px 0;
        }}
        .download-btn {{
            display: inline-block;
            background: var(--primary);
            color: #0f172a;
            font-weight: 700;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            margin-top: 1.5rem;
            transition: all 0.2s ease;
        }}
        .download-btn:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
    </style>
</head>
<body>

    <header>
        <h1>AI Website SEO Audit Dashboard</h1>
        <p>Target: {report.start_url} | Generated: {report.generated_at}</p>
    </header>

    <div class="container">
        
        <div class="grid-dashboard">
            <div class="card">
                <h3 style="text-align: center; margin-top: 0;" class="stat-label">Overall Health Score</h3>
                <div class="score-circle" style="border-color: {score_color}; color: {score_color}">
                    {score}%
                </div>
                <div class="score-desc">{get_score_description(score)}</div>
                <div style="text-align: center;">
                    <a href="javascript:window.print()" class="download-btn">Print Report</a>
                </div>
            </div>

            <div class="card stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{report.total_pages_crawled}</div>
                    <div class="stat-label">Pages Crawled</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: var(--critical)">{critical_count}</div>
                    <div class="stat-label">Critical Issues</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: var(--warning)">{warning_count}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: var(--primary)">{total_issues}</div>
                    <div class="stat-label">Total Findings</div>
                </div>
            </div>
        </div>

        <h2>Crawled Pages Summary</h2>
        <div class="card" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Page URL</th>
                        <th>HTTP Status</th>
                        <th>Issue Count</th>
                        <th>SEO Score</th>
                    </tr>
                </thead>
                <tbody>
                    {page_rows_html}
                </tbody>
            </table>
        </div>

        <h2>Detailed Issues Log</h2>
        <div>
            {issue_cards_html}
        </div>

        {keyword_section_html}

    </div>

</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)


def export_report_to_pdf(report: WebsiteAuditReport, output_path: Union[str, Path]) -> None:
    """Exports a professional, beautifully styled PDF document using ReportLab."""
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
        alignment=1, # Center
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

    story = []

    # --- COVER PAGE ---
    story.append(Spacer(1, 100))
    story.append(Paragraph("AI WEBSITE SEO AUDIT REPORT", title_style))
    story.append(Paragraph(f"Audited Target: {pdf_escape(report.start_url)}", subtitle_style))
    story.append(Spacer(1, 50))

    # Score Panel representation in PDF
    score = report.score
    score_text = f"<b>SEO Score: {score}/100</b>"
    if score >= 90:
        panel_color = colors.HexColor('#dcfce7') # soft green
        text_color = colors.HexColor('#15803d')
    elif score >= 70:
        panel_color = colors.HexColor('#fef9c3') # soft yellow
        text_color = colors.HexColor('#a16207')
    else:
        panel_color = colors.HexColor('#fee2e2') # soft red
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

    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(
        f"This report presents a thorough crawler-based SEO and meta-tag verification audit conducted on "
        f"<b>{pdf_escape(report.start_url)}</b>. The evaluation covers document structures, canonicalization, secure HTTPS routing, "
        f"favicons, Open Graph properties, Twitter Card validation, and structured Schema.org JSON-LD definitions.",
        body_style
    ))
    story.append(Spacer(1, 15))

    # Stats Table
    critical_count = sum(1 for i in report.site_issues if i.severity == "CRITICAL") + \
                     sum(sum(1 for i in p.issues if i.severity == "CRITICAL") for p in report.pages)
    warning_count = sum(1 for i in report.site_issues if i.severity == "WARNING") + \
                    sum(sum(1 for i in p.issues if i.severity == "WARNING") for p in report.pages)

    stats_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Pages Crawled", body_style), Paragraph(str(report.total_pages_crawled), body_style)],
        [Paragraph("Critical Issues", body_style), Paragraph(f"<font color='red'>{critical_count}</font>", body_style)],
        [Paragraph("Warnings", body_style), Paragraph(f"<font color='orange'>{warning_count}</font>", body_style)],
        [Paragraph("Duplicate content sets", body_style), Paragraph(str(len(report.duplicate_pages)), body_style)],
        [Paragraph("Orphan pages found", body_style), Paragraph(str(len(report.orphan_pages)), body_style)]
    ]
    stats_table = Table(stats_data, colWidths=[200, 150])
    stats_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(stats_table)
    story.append(PageBreak())

    # --- KEYWORD RESEARCH SECTION ---
    if report.keyword_research:
        kw = report.keyword_research
        story.append(Paragraph("Keyword Research Analysis", h1_style))
        story.append(Paragraph(
            f"Total words analyzed: <b>{kw.total_words_analyzed}</b> | "
            f"Unique words found: <b>{kw.unique_words_found}</b>",
            body_style
        ))
        story.append(Spacer(1, 10))

        # Primary Keywords Table
        if kw.primary_keywords:
            story.append(Paragraph("Primary Keywords", h2_style))
            kw_header = [
                Paragraph("<b>Keyword</b>", body_style),
                Paragraph("<b>Count</b>", body_style),
                Paragraph("<b>Density</b>", body_style),
                Paragraph("<b>Title</b>", body_style),
                Paragraph("<b>Meta</b>", body_style),
                Paragraph("<b>Headings</b>", body_style),
            ]
            kw_data = [kw_header]
            for k in kw.primary_keywords[:12]:
                kw_data.append([
                    Paragraph(pdf_escape(k.keyword), body_style),
                    Paragraph(str(k.count), body_style),
                    Paragraph(f"{k.density}%", body_style),
                    Paragraph("Yes" if k.in_title else "-", body_style),
                    Paragraph("Yes" if k.in_meta_desc else "-", body_style),
                    Paragraph("Yes" if k.in_headings else "-", body_style),
                ])
            kw_table = Table(kw_data, colWidths=[130, 50, 55, 45, 40, 60])
            kw_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(kw_table)
            story.append(Spacer(1, 12))

        # LSI Keywords
        if kw.lsi_keywords:
            story.append(Paragraph("LSI (Semantic) Keywords", h2_style))
            lsi_header = [
                Paragraph("<b>LSI Keyword</b>", body_style),
                Paragraph("<b>Count</b>", body_style),
                Paragraph("<b>Density</b>", body_style),
            ]
            lsi_data = [lsi_header]
            for k in kw.lsi_keywords[:10]:
                lsi_data.append([
                    Paragraph(pdf_escape(k.keyword), body_style),
                    Paragraph(str(k.count), body_style),
                    Paragraph(f"{k.density}%", body_style),
                ])
            lsi_table = Table(lsi_data, colWidths=[200, 60, 60])
            lsi_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(lsi_table)
            story.append(Spacer(1, 12))

        # Keyword Gaps
        if kw.keyword_gaps:
            story.append(Paragraph("Keyword Gaps (Missing from Site)", h2_style))
            for gap in kw.keyword_gaps:
                story.append(Paragraph(f"  -  <b>{pdf_escape(gap)}</b>", body_style))
            story.append(Spacer(1, 10))

        story.append(PageBreak())

    # --- DETAILED PAGES REPORT ---
    story.append(Paragraph("Detailed Issues Log", h1_style))
    
    # Global site issues
    if report.site_issues:
        story.append(Paragraph("Site-wide Global Issues", h2_style))
        for issue in report.site_issues:
            append_pdf_issue_flowable(story, issue, body_style, code_style, recommendation_style)
            story.append(Spacer(1, 10))

    # Page level issues
    for p in report.pages:
        if not p.issues:
            continue
        story.append(Paragraph(f"URL: {p.url} (Score: {p.score}/100)", h2_style))
        for issue in p.issues:
            append_pdf_issue_flowable(story, issue, body_style, code_style, recommendation_style)
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 10))

    doc.build(story)


def append_pdf_issue_flowable(
    story: list, 
    issue: IssueModel, 
    body_style: ParagraphStyle, 
    code_style: ParagraphStyle, 
    rec_style: ParagraphStyle
) -> None:
    """Helper to build a wrapped flowable item for an issue in ReportLab."""
    sev_color = "red" if issue.severity == "CRITICAL" else "orange"
    header_text = f"<b>[{issue.severity}]</b> {pdf_escape(issue.issue_type)}"
    
    content = []
    content.append(Paragraph(f"<font color='{sev_color}'>{header_text}</font>", body_style))
    content.append(Paragraph(pdf_escape(issue.description), body_style))
    
    if issue.css_selector:
        content.append(Paragraph(f"<b>Selector:</b> {pdf_escape(issue.css_selector)}", body_style))
    if issue.xpath:
        content.append(Paragraph(f"<b>XPath:</b> {pdf_escape(issue.xpath)}", body_style))
    if issue.html_snippet:
        snippet = pdf_escape(issue.html_snippet)
        content.append(Paragraph(snippet, code_style))
        
    content.append(Paragraph(f"<b>Recommendation:</b> {pdf_escape(issue.recommendation)}", rec_style))
    
    story.append(KeepTogether(content))


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
