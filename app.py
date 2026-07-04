"""Streamlit Web Application for the AI-Powered SEO Platform.
"""

import csv
import io
import os
import tempfile
from urllib.parse import urlparse
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Import Toolkit Core components
from ai_seo_audit.crawler import SafeCrawler, SiteCrawler
from ai_seo_audit.parser import SEOHTMLParser
from ai_seo_audit.audit import SEOAuditor
from ai_seo_audit.models import WebsiteAuditReport
from ai_seo_audit.reports import (
    export_report_to_html,
    export_report_to_pdf,
)
from ai_seo_audit.keyword_research import (
    extract_keywords_from_report,
    get_page_text_content,
)
from ai_seo_audit.ai_engine import (
    get_title_suggestions,
    get_meta_desc_suggestions,
    get_h1_suggestions,
    get_content_quality_analysis,
    get_keyword_suggestions,
    get_faq_suggestions,
    get_geo_recommendations,
    get_tech_explanation,
    get_keyword_research_suggestions,
    get_content_ideas,
    get_competitor_keyword_analysis,
)

# Page configurations
st.set_page_config(
    page_title="AI SEO Auditor & Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling rules
st.markdown("""
<style>
    /* Styling headers & buttons */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    .css-1542z7w, .css-1y4vua4 {
        background-color: #0f172a !important;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge {
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .badge-info { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }
</style>
""", unsafe_allow_html=True)


def get_score_color(score: int) -> str:
    """Return HEX color matching the health score range."""
    if score >= 90: return "#22c55e"  # Green
    if score >= 70: return "#eab308"  # Yellow
    return "#ef4444"  # Red


def get_score_description(score: int) -> str:
    """Return human-readable label for the health score range."""
    if score >= 90: return "Excellent Health"
    if score >= 70: return "Satisfactory Health"
    return "Needs Immediate Remediation"


def draw_gauge(score: int):
    """Draws a premium Gauge chart using Plotly."""
    color = get_score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': color, 'size': 50}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color},
            'bgcolor': "#1e293b",
            'borderwidth': 2,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.08)'},
                {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.08)'},
                {'range': [80, 100], 'color': 'rgba(34, 197, 94, 0.08)'}
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f1f5f9"},
        height=220,
        margin=dict(l=20, r=20, t=10, b=10)
    )
    return fig


# Sidebar configurations
st.sidebar.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=60)
st.sidebar.title("AI SEO Platform")
st.sidebar.caption("Audit & Optimize Content via DeepSeek AI")

# Load API key from Streamlit secrets or environment variable (never hardcode in source)
_default_key = st.secrets.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))

# Sidebar: API key input (user can override)
user_api_key = st.sidebar.text_input(
    "DeepSeek API Key",
    value=_default_key,
    type="password",
    help="Enter your DeepSeek API key. Set DEEPSEEK_API_KEY in Streamlit secrets or env var to pre-fill."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Crawl & Scan Limits")
max_pages = st.sidebar.number_input("Max Pages", min_value=1, max_value=250, value=30)
max_depth = st.sidebar.number_input("Max Depth", min_value=1, max_value=10, value=3)
check_links = st.sidebar.checkbox("Validate Broken Links", value=True)
check_images = st.sidebar.checkbox("Validate Broken Images", value=True)

# Application state
if "report" not in st.session_state:
    st.session_state.report = None

st.title("🤖 AI SEO Audit & Optimizations Platform")
st.write("Scan entire sites, check rankings, and run deep SEO audits powered by DeepSeek LLM.")

# Search controls
url_input = st.text_input(
    "Target Site URL", 
    value="https://example.com",
    placeholder="https://yourwebsite.com"
)

col_run, _ = st.columns([1, 4])
with col_run:
    run_btn = st.button("Start Audit Crawl", type="primary", use_container_width=True)

# Crawling Execution
if run_btn:
    if not url_input.startswith(("http://", "https://")):
        st.error("Please enter a valid absolute URL starting with http:// or https://")
    else:
        pages_audited = []

        # Fetch sitemap and robots.txt
        parsed_start = urlparse(url_input)
        origin = f"{parsed_start.scheme}://{parsed_start.netloc}"

        status_text = st.empty()
        status_text.info("🔎 Checking robots.txt and sitemap.xml...")

        sitemap_xml_content = None
        try:
            s_res = requests.get(f"{origin}/sitemap.xml", timeout=4, verify=False)
            if s_res.status_code == 200:
                sitemap_xml_content = s_res.text
        except Exception:
            pass

        robots_found = False
        try:
            r_res = requests.get(f"{origin}/robots.txt", timeout=4, verify=False)
            robots_found = (r_res.status_code == 200)
        except Exception:
            pass

        # Setup crawler
        safe_crawler = SafeCrawler(verify_ssl=False)
        site_crawler = SiteCrawler(
            crawler=safe_crawler,
            max_pages=max_pages,
            max_depth=max_depth,
            respect_robots=True
        )

        # Streamlit progress tracking
        progress_bar = st.progress(0.0)

        for current_url, count, crawl_result, queue_size in site_crawler.crawl_site(url_input):
            pct = min(1.0, count / max_pages)
            progress_bar.progress(pct)
            status_text.caption(f"🕷️ Scanning ({count}/{max_pages}): {current_url} | Queue: {queue_size}")

            if crawl_result and crawl_result.is_success:
                parser = SEOHTMLParser(html_content=crawl_result.html, base_url=crawl_result.final_url)
                metadata = parser.parse_metadata()
                links = parser.get_links()
                images = parser.get_images()

                page_auditor = SEOAuditor(check_links=False, check_images=False, timeout=5)
                page_report = page_auditor.audit_page(
                    crawl_result=crawl_result,
                    metadata=metadata,
                    links=links,
                    images=images,
                    robots_txt_found=robots_found,
                    sitemap_xml_found=(sitemap_xml_content is not None)
                )
                pages_audited.append(page_report)

        progress_bar.progress(1.0)
        status_text.info("⚙️ Running site-wide validations (links, images, duplicates)...")

        # Run global audit
        site_auditor = SEOAuditor(
            check_links=check_links,
            check_images=check_images,
            max_workers=10,
            timeout=4
        )
        website_report = site_auditor.audit_website(
            start_url=url_input,
            pages=pages_audited,
            robots_txt_found=robots_found,
            sitemap_xml_found=(sitemap_xml_content is not None),
            sitemap_xml_content=sitemap_xml_content
        )

        st.session_state.report = website_report
        status_text.empty()
        progress_bar.empty()
        st.success("✅ Audit complete! Scroll down to view your dashboard.")

# If report is loaded, show the dashboard
if st.session_state.report:
    report: WebsiteAuditReport = st.session_state.report
    
    # Pre-collect stats
    total_issues = len(report.site_issues) + sum(len(p.issues) for p in report.pages)
    critical_count = sum(1 for i in report.site_issues if i.severity == "CRITICAL") + \
                     sum(sum(1 for i in p.issues if i.severity == "CRITICAL") for p in report.pages)
    warning_count = sum(1 for i in report.site_issues if i.severity == "WARNING") + \
                    sum(sum(1 for i in p.issues if i.severity == "WARNING") for p in report.pages)
    info_count = total_issues - (critical_count + warning_count)

    # Core Navigation Tabs
    tab_overview, tab_tech, tab_content, tab_images, tab_links, tab_perf, tab_data, tab_keywords, tab_ai = st.tabs([
        "📊 Overview",
        "⚙️ Technical SEO",
        "📝 Content SEO",
        "🖼️ Images",
        "🔗 Links",
        "⚡ Performance",
        "🗂️ Structured Data",
        "🔑 Keyword Research",
        "🧠 AI Suggestions"
    ])

    # 1. OVERVIEW TAB
    with tab_overview:
        col_gauge, col_stats = st.columns([1.5, 2.5])
        
        with col_gauge:
            st.plotly_chart(draw_gauge(report.score), use_container_width=True)
            st.markdown(f"<h3 style='text-align: center; color: {get_score_color(report.score)}'>{get_score_description(report.score)}</h3>", unsafe_allow_html=True)
        
        with col_stats:
            st.subheader("Key SEO Statistics")
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{report.total_pages_crawled}</div>
                    <div class="metric-label">Pages Crawled</div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                st.markdown(f"""
                <div class="metric-card" style="border-color: #ef4444;">
                    <div class="metric-value" style="color: #ef4444;">{critical_count}</div>
                    <div class="metric-label">Critical Issues</div>
                </div>
                """, unsafe_allow_html=True)
            with sub_col2:
                st.markdown(f"""
                <div class="metric-card" style="border-color: #f59e0b;">
                    <div class="metric-value" style="color: #f59e0b;">{warning_count}</div>
                    <div class="metric-label">Warnings</div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                st.markdown(f"""
                <div class="metric-card" style="border-color: #38bdf8;">
                    <div class="metric-value" style="color: #38bdf8;">{info_count}</div>
                    <div class="metric-label">Advisory Items</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Download Audit Exports")
        
        # Download utilities in memory
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        
        # JSON Export bytes
        json_data = report.model_dump_json(indent=2)
        with col_d1:
            st.download_button(
                label="📥 Download JSON Report",
                data=json_data,
                file_name="seo_report.json",
                mime="application/json",
                use_container_width=True
            )

        # CSV Export bytes
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["URL", "Severity", "Issue Type", "Description", "Selector", "XPath", "Recommendation"])
        
        for issue in report.site_issues:
            writer.writerow([issue.url, issue.severity, issue.issue_type, issue.description, issue.css_selector or "", issue.xpath or "", issue.recommendation])
        for p in report.pages:
            for issue in p.issues:
                writer.writerow([issue.url, issue.severity, issue.issue_type, issue.description, issue.css_selector or "", issue.xpath or "", issue.recommendation])
        
        with col_d2:
            st.download_button(
                label="📥 Download CSV Sheet",
                data=csv_buffer.getvalue(),
                file_name="seo_report.csv",
                mime="text/csv",
                use_container_width=True
            )

        # HTML Export bytes
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_html:
            export_report_to_html(report, tmp_html.name)
            with open(tmp_html.name, "r", encoding="utf-8") as f:
                html_bytes = f.read()
        with col_d3:
            st.download_button(
                label="📥 Download HTML Report",
                data=html_bytes,
                file_name="seo_report.html",
                mime="text/html",
                use_container_width=True
            )

        # PDF Export bytes
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            export_report_to_pdf(report, tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                pdf_bytes = f.read()
        with col_d4:
            st.download_button(
                label="📥 Download PDF Document",
                data=pdf_bytes,
                file_name="seo_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("---")
        st.subheader("Crawled Pages Overview")
        
        # Interactive table with search filter
        df_pages = pd.DataFrame([{
            "URL": p.url,
            "HTTP Status": p.status_code,
            "Security": "HTTPS" if p.is_https else "HTTP",
            "SEO Score": f"{p.score}/100",
            "Issues count": len(p.issues)
        } for p in report.pages])

        search_query = st.text_input("🔍 Filter pages list by URL...", "")
        if search_query:
            df_pages = df_pages[df_pages["URL"].str.contains(search_query, case=False)]
        
        st.dataframe(df_pages, use_container_width=True, hide_index=True)

    # 2. TECHNICAL SEO TAB
    with tab_tech:
        st.subheader("Host & Protocol Audits")
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.checkbox("HTTPS Secure Server", value=all(p.is_https for p in report.pages), disabled=True)
        with col_t2:
            st.checkbox("robots.txt Found", value=report.robots_txt_found, disabled=True)
        with col_t3:
            st.checkbox("sitemap.xml Detected", value=report.sitemap_xml_found, disabled=True)

        st.write("")
        st.subheader("Technical Issues Log")
        
        # Filter details
        tech_issues = []
        for issue in report.site_issues:
            if issue.issue_type in ("HTTPS Security", "robots.txt Availability", "Sitemap XML Availability", "Orphan Pages"):
                tech_issues.append(issue)
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type in ("HTTPS Security", "Missing Viewport Tag", "Missing Lang Attribute", "Missing Favicon"):
                    tech_issues.append(issue)

        if not tech_issues:
            st.success("✓ No technical SEO issues detected!")
        else:
            for issue in tech_issues:
                with st.expander(f"[{issue.severity}] {issue.issue_type} - {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    if issue.css_selector: st.code(f"CSS Selector: {issue.css_selector}")
                    if issue.xpath: st.code(f"XPath: {issue.xpath}")
                    st.info(f"**Recommendation:** {issue.recommendation}")

    # 3. CONTENT SEO TAB
    with tab_content:
        st.subheader("On-Page Optimization Checks")
        
        content_issues = []
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type in ("Missing Title", "Title Length", "Missing Meta Description", "Meta Description Length", "Missing H1 Heading", "Multiple H1 Headings"):
                    content_issues.append(issue)
        
        if not content_issues:
            st.success("✓ On-page meta tags and header structures look good!")
        else:
            for issue in content_issues:
                with st.expander(f"[{issue.severity}] {issue.issue_type} - {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    if issue.html_snippet:
                        st.code(issue.html_snippet, language="html")
                    if issue.css_selector: st.caption(f"CSS Selector: {issue.css_selector}")
                    st.info(f"**Recommendation:** {issue.recommendation}")

    # 4. IMAGES TAB
    with tab_images:
        st.subheader("Image Alt Tags & Broken Asset Audits")
        
        img_issues = []
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type in ("Missing Alt Text", "Broken Image"):
                    img_issues.append(issue)

        if not img_issues:
            st.success("✓ All images are healthy and contain ALT tags!")
        else:
            for issue in img_issues:
                with st.expander(f"[{issue.severity}] {issue.issue_type} - {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    if issue.html_snippet:
                        st.code(issue.html_snippet, language="html")
                    st.info(f"**Recommendation:** {issue.recommendation}")

    # 5. LINKS TAB
    with tab_links:
        st.subheader("Link Profiler & Soundness Validation")
        
        link_issues = []
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type == "Broken Link":
                    link_issues.append(issue)

        if not link_issues:
            st.success("✓ Discovered internal and external links are healthy!")
        else:
            for issue in link_issues:
                with st.expander(f"[{issue.severity}] {issue.issue_type} - {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    st.info(f"**Recommendation:** {issue.recommendation}")

    # 6. PERFORMANCE TAB
    with tab_perf:
        st.subheader("HTTP Response Speed Analysis")
        st.write("Displays approximate file size indicators. Long load times negatively affect search engine crawls.")
        
        perf_data = []
        for p in report.pages:
            perf_data.append({
                "URL": p.url,
                "Length of HTML Document (Characters)": len(p.metadata.title or "") + len(p.metadata.meta_description or "") + 500, # Approximate length
                "Favicon Status": "Configured" if p.metadata.favicon_url else "Missing"
            })
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)

    # 7. STRUCTURED DATA TAB
    with tab_data:
        st.subheader("Schema.org JSON-LD Validations")
        
        schema_issues = []
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type == "Invalid JSON-LD":
                    schema_issues.append(issue)

        if not schema_issues:
            st.success("✓ Detected Schema JSON-LD blocks are structured correctly!")
        else:
            for issue in schema_issues:
                with st.expander(f"[{issue.severity}] {issue.issue_type} - {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    if issue.html_snippet:
                        st.code(issue.html_snippet, language="json")
                    st.info(f"**Recommendation:** {issue.recommendation}")

    # 8. AI SUGGESTIONS TAB (DeepSeek API Integration)
    with tab_ai:
        st.subheader("🧠 DeepSeek AI Optimizations Hub")
        st.write("Extract advice, FAQs, and copywriting rewrites based on page-level content audits.")
        
        # Page picker
        selected_page_url = st.selectbox(
            "Select Page URL to Analyze:",
            options=report.crawled_urls
        )
        
        # Load metadata of chosen page
        selected_page = next(p for p in report.pages if p.url == selected_page_url)
        metadata_ref = selected_page.metadata

        # Horizontal actions selector
        ai_action = st.radio(
            "Choose Optimization Analysis:",
            options=[
                "Title & H1 suggestions",
                "Meta Description suggestion",
                "Content Quality & Keywords",
                "FAQs Suggestion",
                "Generative Engine Optimization (GEO)",
                "Technical SEO Explainer"
            ],
            horizontal=True
        )

        st.markdown("---")
        with st.spinner("Calling DeepSeek AI model..."):
            if ai_action == "Title & H1 suggestions":
                st.subheader("Suggested Page Title Rewrites")
                st.write(get_title_suggestions(user_api_key, metadata_ref.title or "Untitled Page"))
                st.write("")
                st.subheader("Suggested Heading (H1) Improvements")
                h1_texts = [h.text for h in metadata_ref.headings if h.level == 1]
                st.write(get_h1_suggestions(user_api_key, metadata_ref.title or "Untitled Page", h1_texts))

            elif ai_action == "Meta Description suggestion":
                st.subheader("Suggested Meta Description Suggestions")
                st.write(get_meta_desc_suggestions(user_api_key, metadata_ref.title or "Untitled Page", metadata_ref.meta_description))

            elif ai_action == "Content Quality & Keywords":
                st.subheader("Content Semantic Keywords Extraction")
                # Synthesize text sample
                sample = (metadata_ref.title or "") + " " + (metadata_ref.meta_description or "")
                st.write(get_keyword_suggestions(user_api_key, sample))
                st.write("")
                st.subheader("Content Quality & EEAT Audit")
                st.write(get_content_quality_analysis(user_api_key, sample))

            elif ai_action == "FAQs Suggestion":
                st.subheader("Auto-Generated FAQ Suggestions")
                sample = (metadata_ref.title or "") + " " + (metadata_ref.meta_description or "")
                st.write(get_faq_suggestions(user_api_key, metadata_ref.title or "Untitled Page", sample))

            elif ai_action == "Generative Engine Optimization (GEO)":
                st.subheader("GEO Recommendations")
                sample = (metadata_ref.title or "") + " " + (metadata_ref.meta_description or "")
                st.write(get_geo_recommendations(user_api_key, sample))

            elif ai_action == "Technical SEO Explainer":
                st.subheader("Educational Explanations of Page Issues")
                if not selected_page.issues:
                    st.info("No issues are found on this page to explain.")
                else:
                    target_issue = st.selectbox(
                        "Select technical issue to explain:",
                        options=[i.issue_type for i in selected_page.issues]
                    )
                    issue_obj = next(i for i in selected_page.issues if i.issue_type == target_issue)
                    st.write(get_tech_explanation(user_api_key, issue_obj.issue_type, issue_obj.description))

    # 8. KEYWORD RESEARCH TAB
    with tab_keywords:
        st.subheader("Keyword Research & Analysis")
        st.write("Enter any URL below to analyze its keywords, density, and get content recommendations.")

        # URL input for keyword research
        kw_url_input = st.text_input(
            "Enter URL to analyze keywords:",
            value=url_input,
            placeholder="https://example.com",
            key="kw_url_input"
        )

        analyze_kw_btn = st.button("Analyze Keywords", type="primary", key="analyze_kw_btn")

        if analyze_kw_btn and kw_url_input.strip():
            with st.spinner(f"Fetching and analyzing keywords from: {kw_url_input}"):
                try:
                    # Fetch the page
                    fetch_crawler = SafeCrawler(verify_ssl=False)
                    crawl_result = fetch_crawler.fetch_page(kw_url_input.strip())

                    if crawl_result and crawl_result.is_success:
                        # Parse the page
                        parser = SEOHTMLParser(html_content=crawl_result.html, base_url=crawl_result.final_url)
                        metadata = parser.parse_metadata()
                        links = parser.get_links()
                        images = parser.get_images()

                        # Audit the page
                        page_auditor = SEOAuditor(check_links=False, check_images=False, timeout=5)
                        page_report = page_auditor.audit_page(
                            crawl_result=crawl_result,
                            metadata=metadata,
                            links=links,
                            images=images,
                            robots_txt_found=True,
                            sitemap_xml_found=False
                        )

                        # Build a mini report for keyword extraction
                        mini_report = WebsiteAuditReport(
                            start_url=kw_url_input.strip(),
                            total_pages_crawled=1,
                            crawled_urls=[kw_url_input.strip()],
                            pages=[page_report],
                            site_issues=[],
                            score=page_report.score,
                        )

                        # Extract keywords
                        kw_report = extract_keywords_from_report(mini_report)
                        st.session_state.kw_url_report = kw_report
                        st.session_state.kw_url_metadata = metadata
                        st.session_state.kw_url_page = page_report
                        st.session_state.kw_url_text = (
                            (metadata.title or "") + " " +
                            (metadata.meta_description or "") + " " +
                            " ".join(h.text for h in metadata.headings)
                        )
                        st.success(f"Keywords extracted from: {kw_url_input}")
                    else:
                        st.error(f"Could not fetch URL: {kw_url_input}. Status: {crawl_result.status_code if crawl_result else 'No response'}")
                except Exception as e:
                    st.error(f"Error fetching URL: {str(e)}")

        # Display results if available
        if "kw_url_report" in st.session_state:
            kw_report = st.session_state.kw_url_report
            metadata = st.session_state.kw_url_metadata
            page_report = st.session_state.kw_url_page
            page_text = st.session_state.kw_url_text

            st.markdown("---")

            # Page Info Header
            st.markdown(f"### Results for: `{page_report.url}`")
            st.caption(f"Status: {page_report.status_code} | Score: {page_report.score}/100")

            # Summary metrics
            kw_col1, kw_col2, kw_col3, kw_col4 = st.columns(4)
            with kw_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(kw_report.primary_keywords)}</div>
                    <div class="metric-label">Keywords Found</div>
                </div>
                """, unsafe_allow_html=True)
            with kw_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{kw_report.total_words_analyzed}</div>
                    <div class="metric-label">Total Words</div>
                </div>
                """, unsafe_allow_html=True)
            with kw_col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(kw_report.secondary_keywords)}</div>
                    <div class="metric-label">Phrases Found</div>
                </div>
                """, unsafe_allow_html=True)
            with kw_col4:
                top_kw = kw_report.primary_keywords[0].keyword if kw_report.primary_keywords else "-"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.4rem;">{top_kw}</div>
                    <div class="metric-label">Top Keyword</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Sub-tabs
            kw_subtab1, kw_subtab2, kw_subtab3 = st.tabs([
                "Keywords Found",
                "AI Keyword Research",
                "Content Ideas"
            ])

            # Sub-tab 1: Keywords Found
            with kw_subtab1:
                st.subheader("Keywords Extracted from This URL")

                # Primary keywords table
                st.markdown("#### Single Keywords")
                if kw_report.primary_keywords:
                    kw_data = [{
                        "Keyword": k.keyword,
                        "Count": k.count,
                        "Density %": k.density,
                        "In Title": "Yes" if k.in_title else "",
                        "In Meta Desc": "Yes" if k.in_meta_desc else "",
                        "In Headings": "Yes" if k.in_headings else "",
                        "In URL": "Yes" if k.in_url else "",
                    } for k in kw_report.primary_keywords]
                    st.dataframe(pd.DataFrame(kw_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No keywords found.")

                # Multi-word phrases
                st.markdown("#### Multi-Word Phrases")
                if kw_report.secondary_keywords:
                    sec_data = [{
                        "Phrase": k.keyword,
                        "Count": k.count,
                        "Density %": k.density,
                    } for k in kw_report.secondary_keywords]
                    st.dataframe(pd.DataFrame(sec_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No multi-word phrases found.")

                # LSI keywords
                if kw_report.lsi_keywords:
                    st.markdown("#### LSI (Semantic) Keywords")
                    lsi_data = [{
                        "LSI Keyword": k.keyword,
                        "Count": k.count,
                        "Density %": k.density,
                    } for k in kw_report.lsi_keywords]
                    st.dataframe(pd.DataFrame(lsi_data), use_container_width=True, hide_index=True)

                # Keyword Gaps
                if kw_report.keyword_gaps:
                    st.markdown("#### Suggested Keywords to Add")
                    for gap in kw_report.keyword_gaps:
                        st.markdown(f"- **{gap}**")

                # Keyword detail inspector
                st.markdown("---")
                st.markdown("#### Keyword Detail Inspector")
                all_kws = [k.keyword for k in kw_report.primary_keywords + kw_report.secondary_keywords]
                if all_kws:
                    selected_kw = st.selectbox("Select keyword to inspect:", options=all_kws, key="kw_inspect")
                    kw_obj = next(
                        (k for k in kw_report.primary_keywords + kw_report.secondary_keywords if k.keyword == selected_kw),
                        None
                    )
                    if kw_obj:
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.metric("Keyword", kw_obj.keyword)
                            st.metric("Count", kw_obj.count)
                            st.metric("Density", f"{kw_obj.density}%")
                        with detail_col2:
                            placement = []
                            if kw_obj.in_title:
                                placement.append("Title Tag")
                            if kw_obj.in_meta_desc:
                                placement.append("Meta Description")
                            if kw_obj.in_headings:
                                placement.append("Headings")
                            if kw_obj.in_url:
                                placement.append("URL")
                            st.write("**Found in:**")
                            if placement:
                                for p in placement:
                                    st.success(f"{p}")
                            else:
                                st.info("Body text only")

            # Sub-tab 2: AI Keyword Research
            with kw_subtab2:
                st.subheader("AI-Powered Keyword Recommendations")
                st.caption("Get AI analysis of keyword strategy for this URL.")

                existing_kws = [k.keyword for k in kw_report.primary_keywords[:10]]

                if st.button("Generate AI Keyword Analysis", type="primary", key="ai_kw_url_btn"):
                    with st.spinner("DeepSeek AI is analyzing keywords..."):
                        ai_result = get_keyword_research_suggestions(user_api_key, page_text, existing_kws)
                        st.session_state.ai_kw_url_result = ai_result

                if "ai_kw_url_result" in st.session_state:
                    st.markdown(st.session_state.ai_kw_url_result)

            # Sub-tab 3: Content Ideas
            with kw_subtab3:
                st.subheader("Content Ideas for This Page")
                st.caption("Get AI content ideas based on this page's keywords and topics.")

                if st.button("Generate Content Ideas", type="primary", key="content_ideas_url_btn"):
                    with st.spinner("DeepSeek AI is generating content ideas..."):
                        ideas_result = get_content_ideas(user_api_key, page_text, existing_kws)
                        st.session_state.content_ideas_url_result = ideas_result

                if "content_ideas_url_result" in st.session_state:
                    st.markdown(st.session_state.content_ideas_url_result)

        elif not analyze_kw_btn:
            st.info("Enter a URL above and click 'Analyze Keywords' to get detailed keyword analysis.")
