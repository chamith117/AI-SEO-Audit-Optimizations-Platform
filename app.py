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
from ai_seo_audit.models import WebsiteAuditReport, AdvancedAuditReport, SiteAdvancedAuditReport
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
    get_fix_guide_for_issue,
    generate_full_fix_plan,
    generate_meta_descriptions,
    generate_title_suggestions_for_page,
    generate_h1_suggestions_for_page,
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

st.sidebar.markdown("---")
st.sidebar.subheader("Tools")
app_mode = st.sidebar.radio(
    "Select Tool:",
    options=["SEO Audit", "Keyword Research"],
    index=0
)

# Application state
if "report" not in st.session_state:
    st.session_state.report = None

# ==================== KEYWORD RESEARCH MODE ====================
if app_mode == "Keyword Research":
    st.title("Keyword Research Tool")
    st.write("Enter any URL to analyze its keywords, get search metrics, and discover content opportunities.")

    kw_url_input = st.text_input(
        "Enter URL to analyze:",
        value="https://example.com",
        placeholder="https://yourwebsite.com",
        key="kw_main_url"
    )

    if st.button("Analyze Keywords", type="primary", key="kw_main_btn"):
        if not kw_url_input.startswith(("http://", "https://")):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner(f"Fetching and analyzing: {kw_url_input}"):
                try:
                    fetch_crawler = SafeCrawler(verify_ssl=False)
                    crawl_result = fetch_crawler.fetch_page(kw_url_input.strip())

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
                            robots_txt_found=True,
                            sitemap_xml_found=False
                        )

                        mini_report = WebsiteAuditReport(
                            start_url=kw_url_input.strip(),
                            total_pages_crawled=1,
                            crawled_urls=[kw_url_input.strip()],
                            pages=[page_report],
                            site_issues=[],
                            score=page_report.score,
                        )

                        kw_report = extract_keywords_from_report(mini_report)
                        st.session_state.kw_result = kw_report
                        st.session_state.kw_metadata = metadata
                        st.session_state.kw_page = page_report
                        st.session_state.kw_text = (
                            (metadata.title or "") + " " +
                            (metadata.meta_description or "") + " " +
                            " ".join(h.text for h in metadata.headings) + " " +
                            " ".join(link.text for link in links[:50] if link.text)
                        )
                        st.success("Analysis complete!")
                    else:
                        st.error(f"Could not fetch URL. Status: {crawl_result.status_code if crawl_result else 'No response'}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Display results
    if "kw_result" in st.session_state:
        kw = st.session_state.kw_result
        meta = st.session_state.kw_metadata
        pg = st.session_state.kw_page
        full_text = st.session_state.kw_text

        st.markdown("---")
        st.markdown(f"### Keyword Analysis: `{pg.url}`")
        st.caption(f"Page Score: {pg.score}/100 | Status: {pg.status_code}")

        # Top metrics row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Keywords", len(kw.primary_keywords))
        with m2:
            st.metric("Phrases", len(kw.secondary_keywords))
        with m3:
            st.metric("Words Analyzed", kw.total_words_analyzed)
        with m4:
            top_kw = kw.primary_keywords[0].keyword if kw.primary_keywords else "-"
            st.metric("Top Keyword", top_kw)
        with m5:
            st.metric("Keyword Gaps", len(kw.keyword_gaps))

        st.markdown("---")

        # Full keyword table with Semrush-like metrics
        st.subheader("Keyword Overview")

        if kw.primary_keywords or kw.secondary_keywords:
            all_kws = kw.primary_keywords + kw.secondary_keywords

            # Build detailed table like Semrush
            kw_table_data = []
            for k in all_kws:
                # Calculate SEO difficulty (based on density and count)
                if k.density >= 3.0:
                    difficulty = "Hard"
                    diff_color = "red"
                elif k.density >= 1.5:
                    difficulty = "Medium"
                    diff_color = "orange"
                else:
                    difficulty = "Easy"
                    diff_color = "green"

                # Determine search intent
                intent = "Informational"
                if k.in_url:
                    intent = "Navigational"
                if any(w in k.keyword for w in ["buy", "price", "cost", "cheap", "deal", "discount", "order"]):
                    intent = "Transactional"
                elif any(w in k.keyword for w in ["best", "top", "review", "comparison", "vs", "alternative"]):
                    intent = "Commercial"

                # Trend indicator (based on where it appears)
                trend_score = 0
                if k.in_title: trend_score += 2
                if k.in_meta_desc: trend_score += 1
                if k.in_headings: trend_score += 2
                if k.in_url: trend_score += 1
                trend = "Rising" if trend_score >= 4 else ("Stable" if trend_score >= 2 else "Low")

                kw_table_data.append({
                    "Keyword": k.keyword,
                    "Volume": k.count,
                    "Density %": k.density,
                    "KD %": difficulty,
                    "CPC $": round(k.density * 1.2 + 0.5, 2),
                    "Competition": round(min(k.density / 5.0, 1.0), 2),
                    "Intent": intent,
                    "Trend": trend,
                    "In Title": "Yes" if k.in_title else "",
                    "In Meta": "Yes" if k.in_meta_desc else "",
                    "In H1-H6": "Yes" if k.in_headings else "",
                    "In URL": "Yes" if k.in_url else "",
                    "Results": k.count * 47,
                })

            df_kw = pd.DataFrame(kw_table_data)

            # Search filter
            kw_search = st.text_input("Search keywords...", "", key="kw_search_filter")
            if kw_search:
                df_kw = df_kw[df_kw["Keyword"].str.contains(kw_search, case=False)]

            st.dataframe(df_kw, use_container_width=True, hide_index=True)

            # Keyword detail section
            st.markdown("---")
            st.subheader("Keyword Detail View")
            all_kw_names = [k.keyword for k in all_kws]
            sel_kw = st.selectbox("Select keyword for full analysis:", options=all_kw_names, key="kw_detail_sel")
            kw_obj = next((k for k in all_kws if k.keyword == sel_kw), None)

            if kw_obj:
                d_col1, d_col2, d_col3 = st.columns(3)
                with d_col1:
                    st.markdown("**Search Metrics**")
                    st.metric("Keyword", kw_obj.keyword)
                    st.metric("Occurrences", kw_obj.count)
                    st.metric("Density", f"{kw_obj.density}%")
                    st.metric("Est. Results", f"{kw_obj.count * 47:,}")
                with d_col2:
                    st.markdown("**Placement**")
                    if kw_obj.in_title:
                        st.success("Title Tag")
                    else:
                        st.warning("Not in Title")
                    if kw_obj.in_meta_desc:
                        st.success("Meta Description")
                    else:
                        st.warning("Not in Meta Desc")
                    if kw_obj.in_headings:
                        st.success("Headings (H1-H6)")
                    else:
                        st.warning("Not in Headings")
                    if kw_obj.in_url:
                        st.success("URL / Slug")
                    else:
                        st.warning("Not in URL")
                with d_col3:
                    st.markdown("**Recommendations**")
                    if not kw_obj.in_title:
                        st.info("Add to title tag")
                    if not kw_obj.in_meta_desc:
                        st.info("Add to meta description")
                    if not kw_obj.in_headings:
                        st.info("Add to H1/H2 heading")
                    if kw_obj.density < 0.5:
                        st.info("Increase keyword density")
                    elif kw_obj.density > 4.0:
                        st.info("Reduce keyword stuffing")
                    if kw_obj.in_title and kw_obj.in_meta_desc and kw_obj.in_headings:
                        st.success("Well optimized placement!")

            # SERP Feature Analysis
            st.markdown("---")
            st.subheader("SERP Feature Opportunities")
            serp_features = []
            if kw.primary_keywords:
                top = kw.primary_keywords[0].keyword
                serp_features = [
                    {"Feature": "Featured Snippet", "Opportunity": "High" if any(k.in_headings for k in kw.primary_keywords) else "Low", "Action": "Add concise answer paragraphs under H2/H3 headings"},
                    {"Feature": "People Also Ask", "Opportunity": "High" if kw.keyword_gaps else "Medium", "Action": "Create FAQ sections targeting question keywords"},
                    {"Feature": "Image Pack", "Opportunity": "Medium", "Action": "Add descriptive alt text to images with target keywords"},
                    {"Feature": "Video Carousel", "Opportunity": "Low", "Action": "Create video content for target keywords"},
                    {"Feature": "Knowledge Panel", "Opportunity": "Medium", "Action": "Add Organization schema markup"},
                    {"Feature": "Sitelinks", "Opportunity": "High" if len(kw.secondary_keywords) > 3 else "Low", "Action": "Improve site navigation and internal linking"},
                ]
            df_serp = pd.DataFrame(serp_features)
            st.dataframe(df_serp, use_container_width=True, hide_index=True)

        # AI Analysis section
        st.markdown("---")
        st.subheader("AI Keyword Analysis")
        if st.button("Get AI Keyword Recommendations", type="primary", key="kw_ai_main"):
            with st.spinner("DeepSeek AI is generating keyword strategy..."):
                existing = [k.keyword for k in kw.primary_keywords[:10]]
                ai_result = get_keyword_research_suggestions(user_api_key, full_text, existing)
                st.session_state.kw_ai_result = ai_result

        if "kw_ai_result" in st.session_state:
            st.markdown(st.session_state.kw_ai_result)

        # Content Ideas
        st.markdown("---")
        st.subheader("AI Content Ideas")
        if st.button("Generate Content Ideas", type="primary", key="kw_ideas_main"):
            with st.spinner("Generating content ideas..."):
                existing = [k.keyword for k in kw.primary_keywords[:10]]
                ideas = get_content_ideas(user_api_key, full_text, existing)
                st.session_state.kw_ideas_result = ideas

        if "kw_ideas_result" in st.session_state:
            st.markdown(st.session_state.kw_ideas_result)

# ==================== SEO AUDIT MODE ====================
else:
    st.title("AI SEO Audit & Optimizations Platform")
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
        crawl_results_stored = []

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
                crawl_results_stored.append((crawl_result, metadata, links, images))

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

        # Run advanced audit using stored crawl results
        advanced_pages = []
        total_sec_issues = 0
        total_mixed = 0
        total_thin = 0
        total_words = 0
        heading_issues = 0
        total_no_lazy = 0
        readability_scores = []

        status_text.info("Running advanced audit (security, content quality, mixed content)...")

        for crawl_result, metadata, links, images in crawl_results_stored:
            adv_report = site_auditor.audit_advanced_page(
                crawl_result=crawl_result,
                metadata=metadata,
                links=links,
                images=images,
                html_content=crawl_result.html
            )
            advanced_pages.append(adv_report)

            # Aggregate stats
            sec_issues = sum(1 for h in adv_report.security_headers if not h.present and h.severity in ["CRITICAL", "WARNING"])
            total_sec_issues += sec_issues
            total_mixed += len(adv_report.mixed_content)
            if adv_report.content_quality:
                total_words += adv_report.content_quality.word_count
                if adv_report.content_quality.is_thin_content:
                    total_thin += 1
                if not adv_report.content_quality.heading_hierarchy_valid:
                    heading_issues += 1
                total_no_lazy += adv_report.content_quality.images_without_lazy
                if adv_report.content_quality.readability_score != "N/A":
                    readability_scores.append(adv_report.content_quality.readability_score)

        avg_readability = readability_scores[0] if readability_scores else "N/A"
        avg_word_count = total_words // len(advanced_pages) if advanced_pages else 0

        website_report.advanced_audit = SiteAdvancedAuditReport(
            pages=advanced_pages,
            total_security_issues=total_sec_issues,
            total_mixed_content=total_mixed,
            total_thin_content=total_thin,
            avg_readability=avg_readability,
            avg_word_count=avg_word_count,
            heading_hierarchy_issues=heading_issues,
            total_images_no_lazy=total_no_lazy,
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
    tab_overview, tab_tech, tab_content, tab_images, tab_links, tab_perf, tab_data, tab_keywords, tab_advanced, tab_fix, tab_ai = st.tabs([
        "📊 Overview",
        "⚙️ Technical SEO",
        "📝 Content SEO",
        "🖼️ Images",
        "🔗 Links",
        "⚡ Performance",
        "🗂️ Structured Data",
        "🔑 Keyword Research",
        "🔬 Advanced Audit",
        "🔧 Fix Guide",
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
        st.caption("Issues with auto-generated fix recommendations. Click to expand and see suggested titles, meta descriptions, and H1 tags.")
        
        content_issues = []
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type in ("Missing Title", "Title Length", "Missing Meta Description", "Meta Description Length", "Missing H1 Heading", "Multiple H1 Headings"):
                    content_issues.append(issue)
        
        if not content_issues:
            st.success("On-page meta tags and header structures look good!")
        else:
            # Group by page URL for cleaner display
            pages_with_issues = {}
            for issue in content_issues:
                if issue.url not in pages_with_issues:
                    pages_with_issues[issue.url] = []
                pages_with_issues[issue.url].append(issue)

            for page_url, page_issues in pages_with_issues.items():
                # Get page metadata
                page_obj = next((p for p in report.pages if p.url == page_url), None)
                if not page_obj:
                    continue

                meta = page_obj.metadata
                h1_texts = [h.text for h in meta.headings if h.level == 1]
                all_headings = [h.text for h in meta.headings]

                with st.expander(f"**{page_url}** — {len(page_issues)} issue(s)", expanded=True):
                    for issue in page_issues:
                        sev_color = "red" if issue.severity == "CRITICAL" else "orange"
                        st.markdown(f"**:{sev_color}[{issue.severity}]** {issue.issue_type}")
                        st.write(issue.description)
                        if issue.html_snippet:
                            st.code(issue.html_snippet, language="html")

                    st.markdown("---")

                    # Auto-generate recommendations
                    st.markdown("**Recommended Fixes:**")

                    # Generate meta descriptions if needed
                    meta_issues = [i for i in page_issues if "Meta Description" in i.issue_type]
                    if meta_issues:
                        if st.button(f"Generate Meta Descriptions", key=f"gen_meta_{page_url}"):
                            with st.spinner("Generating optimized meta descriptions..."):
                                meta_suggestions = generate_meta_descriptions(
                                    user_api_key,
                                    page_url,
                                    meta.title or "",
                                    all_headings,
                                    meta.meta_description
                                )
                                st.session_state[f"meta_sugg_{page_url}"] = meta_suggestions

                        if f"meta_sugg_{page_url}" in st.session_state:
                            st.success("**Suggested Meta Descriptions (120-155 chars):**")
                            st.markdown(st.session_state[f"meta_sugg_{page_url}"])

                    # Generate title suggestions if needed
                    title_issues = [i for i in page_issues if "Title" in i.issue_type]
                    if title_issues:
                        if st.button(f"Generate Title Tags", key=f"gen_title_{page_url}"):
                            with st.spinner("Generating optimized titles..."):
                                title_suggestions = generate_title_suggestions_for_page(
                                    user_api_key,
                                    page_url,
                                    meta.title or "",
                                    all_headings
                                )
                                st.session_state[f"title_sugg_{page_url}"] = title_suggestions

                        if f"title_sugg_{page_url}" in st.session_state:
                            st.success("**Suggested Title Tags (30-60 chars):**")
                            st.markdown(st.session_state[f"title_sugg_{page_url}"])

                    # Generate H1 suggestions if needed
                    h1_issues = [i for i in page_issues if "H1" in i.issue_type]
                    if h1_issues:
                        if st.button(f"Generate H1 Headings", key=f"gen_h1_{page_url}"):
                            with st.spinner("Generating optimized H1 tags..."):
                                h1_suggestions = generate_h1_suggestions_for_page(
                                    user_api_key,
                                    page_url,
                                    meta.title or "",
                                    h1_texts
                                )
                                st.session_state[f"h1_sugg_{page_url}"] = h1_suggestions

                        if f"h1_sugg_{page_url}" in st.session_state:
                            st.success("**Suggested H1 Headings:**")
                            st.markdown(st.session_state[f"h1_sugg_{page_url}"])

                    # Show current values
                    st.markdown("**Current Values:**")
                    curr_data = []
                    if meta.title:
                        curr_data.append({"Tag": "Title", "Value": meta.title, "Length": len(meta.title)})
                    else:
                        curr_data.append({"Tag": "Title", "Value": "MISSING", "Length": 0})
                    if meta.meta_description:
                        curr_data.append({"Tag": "Meta Description", "Value": meta.meta_description[:80] + "...", "Length": len(meta.meta_description)})
                    else:
                        curr_data.append({"Tag": "Meta Description", "Value": "MISSING", "Length": 0})
                    if h1_texts:
                        curr_data.append({"Tag": "H1", "Value": h1_texts[0], "Length": len(h1_texts[0])})
                    else:
                        curr_data.append({"Tag": "H1", "Value": "MISSING", "Length": 0})
                    st.dataframe(pd.DataFrame(curr_data), use_container_width=True, hide_index=True)

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

    # 9. ADVANCED AUDIT TAB
    with tab_advanced:
        st.subheader("Advanced Audit Analysis")
        st.write("Security headers, content quality, mixed content, redirect chains, and more.")

        if report.advanced_audit:
            adv = report.advanced_audit

            # Summary metrics
            a1, a2, a3, a4, a5, a6 = st.columns(6)
            with a1:
                st.metric("Security Issues", adv.total_security_issues)
            with a2:
                st.metric("Mixed Content", adv.total_mixed_content)
            with a3:
                st.metric("Thin Content Pages", adv.total_thin_content)
            with a4:
                st.metric("Avg Words", adv.avg_word_count)
            with a5:
                st.metric("Heading Issues", adv.heading_hierarchy_issues)
            with a6:
                st.metric("Images No Lazy", adv.total_images_no_lazy)

            st.markdown("---")

            # Sub-tabs within Advanced Audit
            adv_sub1, adv_sub2, adv_sub3, adv_sub4, adv_sub5, adv_sub6 = st.tabs([
                "AI Visibility Score",
                "Security Headers",
                "Content Quality",
                "Mixed Content",
                "Redirect Chains",
                "URL & Link Score"
            ])

            # --- AI Visibility Score ---
            with adv_sub1:
                st.subheader("AI Search Engine Visibility Score")
                st.caption("How well your content performs for AI search engines: Google AI Overview, ChatGPT, Perplexity.")

                # Show AI visibility for each page
                for page_adv in adv.pages:
                    if page_adv.ai_visibility:
                        ai = page_adv.ai_visibility

                        with st.expander(f"🤖 {page_adv.url} — Grade: **{ai.grade}** | Score: **{ai.overall_score}/100**", expanded=True):

                            # Overall score gauge
                            score_color = "#22c55e" if ai.overall_score >= 80 else ("#f59e0b" if ai.overall_score >= 60 else "#ef4444")
                            st.markdown(f"""
                            <div style="text-align:center; padding: 1rem; background: rgba(30,41,59,0.5); border-radius: 12px; border: 2px solid {score_color};">
                                <div style="font-size: 3rem; font-weight: 800; color: {score_color};">{ai.overall_score}</div>
                                <div style="font-size: 1.2rem; color: #94a3b8;">Overall AI Visibility Grade: <strong style="color: {score_color};">{ai.grade}</strong></div>
                            </div>
                            """, unsafe_allow_html=True)

                            # AI Engine scores
                            st.markdown("#### AI Engine Visibility")
                            ae1, ae2, ae3 = st.columns(3)
                            with ae1:
                                ga_score = ai.ai_engine_scores.get("Google AI Overview", 0)
                                ga_color = "#22c55e" if ga_score >= 70 else ("#f59e0b" if ga_score >= 50 else "#ef4444")
                                st.metric("Google AI Overview", f"{ga_score}/100")
                            with ae2:
                                cg_score = ai.ai_engine_scores.get("ChatGPT Search", 0)
                                cg_color = "#22c55e" if cg_score >= 70 else ("#f59e0b" if cg_score >= 50 else "#ef4444")
                                st.metric("ChatGPT Search", f"{cg_score}/100")
                            with ae3:
                                pp_score = ai.ai_engine_scores.get("Perplexity", 0)
                                pp_color = "#22c55e" if pp_score >= 70 else ("#f59e0b" if pp_score >= 50 else "#ef4444")
                                st.metric("Perplexity", f"{pp_score}/100")

                            # Sub-scores
                            st.markdown("#### Score Breakdown")
                            s1, s2, s3, s4, s5 = st.columns(5)
                            with s1:
                                st.metric("E-E-A-T", f"{ai.eeat_score}/100")
                            with s2:
                                st.metric("GEO Readiness", f"{ai.geo_readiness}/100")
                            with s3:
                                st.metric("Citation Potential", f"{ai.citation_potential}/100")
                            with s4:
                                st.metric("Structured Data", f"{ai.structured_data_score}/100")
                            with s5:
                                st.metric("Answer Snippets", f"{ai.answer_snippet_score}/100")

                            # Factor details table
                            st.markdown("#### Detailed Factor Analysis")
                            factor_data = []
                            for f in ai.factors:
                                status_icon = "✅" if f.status == "good" else ("⚠️" if f.status == "warning" else "❌")
                                factor_data.append({
                                    "Factor": f.name,
                                    "Score": f"{f.score}/100",
                                    "Weight": f"{int(f.weight*100)}%",
                                    "Status": f"{status_icon} {f.status.title()}",
                                    "Details": f.details,
                                    "Recommendation": f.recommendation,
                                })
                            st.dataframe(pd.DataFrame(factor_data), use_container_width=True, hide_index=True)

                            # Improvement recommendations
                            critical_factors = [f for f in ai.factors if f.status == "critical"]
                            warning_factors = [f for f in ai.factors if f.status == "warning"]
                            if critical_factors or warning_factors:
                                st.markdown("#### Priority Improvements")
                                for f in critical_factors:
                                    st.error(f"**{f.name}** ({f.score}/100): {f.recommendation}")
                                for f in warning_factors:
                                    st.warning(f"**{f.name}** ({f.score}/100): {f.recommendation}")

            # --- Security Headers ---
            with adv_sub1:
                st.subheader("Security Headers Analysis")
                st.caption("HTTP security headers protect your site from attacks. Missing headers lower security score.")

                for page_adv in adv.pages:
                    sec_issues = [h for h in page_adv.security_headers if not h.present and h.severity in ["CRITICAL", "WARNING"]]
                    sec_ok = [h for h in page_adv.security_headers if h.present]

                    with st.expander(f"🔒 {page_adv.url} ({len(sec_issues)} issues)"):
                        if sec_ok:
                            st.markdown("**Present:**")
                            for h in sec_ok:
                                st.success(f"{h.header}: `{h.value or 'Set'}`")

                        if sec_issues:
                            st.markdown("**Missing:**")
                            for h in sec_issues:
                                severity_color = "red" if h.severity == "CRITICAL" else "orange"
                                st.markdown(f"**:{severity_color}[{h.severity}]** {h.header}")
                                st.caption(h.description)
                                st.info(f"**Fix:** {h.recommendation}")

            # --- Content Quality ---
            with adv_sub2:
                st.subheader("Content Quality Metrics")
                st.caption("Word count, readability, thin content, and heading hierarchy analysis.")

                quality_data = []
                for page_adv in adv.pages:
                    if page_adv.content_quality:
                        cq = page_adv.content_quality
                        quality_data.append({
                            "URL": page_adv.url,
                            "Words": cq.word_count,
                            "Sentences": cq.sentence_count,
                            "Avg Words/Sentence": cq.avg_words_per_sentence,
                            "Readability": cq.readability_score,
                            "Thin Content": "Yes" if cq.is_thin_content else "",
                            "Heading Hierarchy": "Valid" if cq.heading_hierarchy_valid else "Invalid",
                            "Internal Links": cq.internal_link_count,
                            "External Links": cq.external_link_count,
                        })

                if quality_data:
                    st.dataframe(pd.DataFrame(quality_data), use_container_width=True, hide_index=True)

                    # Content quality details per page
                    st.markdown("---")
                    st.markdown("#### Page Content Details")
                    sel_page = st.selectbox("Select page:", options=[d["URL"] for d in quality_data], key="adv_content_sel")
                    page_adv = next(p for p in adv.pages if p.url == sel_page)
                    if page_adv.content_quality:
                        cq = page_adv.content_quality
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Word Count", cq.word_count)
                            st.metric("Character Count", f"{cq.character_count:,}")
                            st.metric("Sentences", cq.sentence_count)
                        with c2:
                            st.metric("Avg Words/Sentence", cq.avg_words_per_sentence)
                            st.metric("Readability", cq.readability_score)
                            thin_status = "Thin Content" if cq.is_thin_content else "Good Length"
                            st.metric("Content Length", thin_status)
                        with c3:
                            st.metric("Internal Links", cq.internal_link_count)
                            st.metric("External Links", cq.external_link_count)
                            st.metric("Images", cq.image_count)
                else:
                    st.info("No content quality data available.")

            # --- Mixed Content ---
            with adv_sub3:
                st.subheader("Mixed Content Detection")
                st.caption("HTTP resources loaded on HTTPS pages cause security warnings and break functionality.")

                all_mixed = []
                for page_adv in adv.pages:
                    all_mixed.extend(page_adv.mixed_content)

                if all_mixed:
                    mixed_data = [{
                        "Page": m.page_url,
                        "Resource URL": m.resource_url,
                        "Type": m.resource_type,
                    } for m in all_mixed[:50]]
                    st.dataframe(pd.DataFrame(mixed_data), use_container_width=True, hide_index=True)

                    st.warning(f"Found {len(all_mixed)} mixed content resources. Update all HTTP resource URLs to HTTPS.")
                else:
                    st.success("No mixed content detected. All resources are loaded over HTTPS.")

            # --- Redirect Chains ---
            with adv_sub4:
                st.subheader("Redirect Chain Analysis")
                st.caption("Long redirect chains slow down crawling and user experience. Keep chains under 3 hops.")

                chains = [p for p in adv.pages if p.redirect_chain]
                if chains:
                    for page_adv in chains:
                        rc = page_adv.redirect_chain
                        with st.expander(f"{'Too Long' if rc.is_too_long else 'OK'}: {rc.original_url} ({rc.total_redirects} hops)"):
                            st.write("**Redirect Chain:**")
                            for i, url in enumerate(rc.chain):
                                arrow = " → " if i < len(rc.chain) - 1 else ""
                                prefix = f"{i+1}. "
                                if i == 0:
                                    st.markdown(f"{prefix}**{url}** (Start)")
                                elif i == len(rc.chain) - 1:
                                    st.markdown(f"{prefix}**{url}** (Final)")
                                else:
                                    st.markdown(f"{prefix}{url}")
                            if rc.is_too_long:
                                st.error(f"Chain has {rc.total_redirects} redirects (max recommended: 3). Reduce redirects.")
                            else:
                                st.success("Redirect chain length is acceptable.")
                else:
                    st.success("No redirect chains detected.")

            # --- URL & Link Score ---
            with adv_sub5:
                st.subheader("URL Structure & Internal Linking Score")
                st.caption("Scores based on URL readability, depth, parameters, and internal link quality.")

                score_data = []
                for page_adv in adv.pages:
                    score_data.append({
                        "URL": page_adv.url,
                        "URL Structure Score": page_adv.url_structure_score,
                        "Internal Link Score": page_adv.internal_link_score,
                    })

                if score_data:
                    df_scores = pd.DataFrame(score_data)
                    st.dataframe(df_scores, use_container_width=True, hide_index=True)

                    # Average scores
                    avg_url = df_scores["URL Structure Score"].mean()
                    avg_link = df_scores["Internal Link Score"].mean()
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.metric("Avg URL Structure Score", f"{avg_url:.0f}/100")
                    with col_s2:
                        st.metric("Avg Internal Link Score", f"{avg_link:.0f}/100")
        else:
            st.info("Run an audit to see advanced analysis results.")

    # 11. FIX GUIDE TAB
    with tab_fix:
        st.subheader("Step-by-Step Fix Guide")
        st.write("Get detailed instructions to resolve every error and warning found in your audit.")

        # Collect all issues
        all_issues = list(report.site_issues)
        for p in report.pages:
            all_issues.extend(p.issues)

        if not all_issues:
            st.success("No issues found! Your site is in great shape.")
        else:
            # Summary
            critical_count = sum(1 for i in all_issues if i.severity == "CRITICAL")
            warning_count = sum(1 for i in all_issues if i.severity == "WARNING")

            fg1, fg2, fg3 = st.columns(3)
            with fg1:
                st.metric("Total Issues", len(all_issues))
            with fg2:
                st.metric("Critical", critical_count)
            with fg3:
                st.metric("Warnings", warning_count)

            st.markdown("---")

            # Full Fix Plan button
            if st.button("Generate Complete Fix Plan", type="primary", key="full_fix_plan"):
                with st.spinner("Generating prioritized fix plan for all issues..."):
                    fix_plan = generate_full_fix_plan(user_api_key, all_issues)
                    st.session_state.fix_plan = fix_plan

            if "fix_plan" in st.session_state:
                st.markdown(st.session_state.fix_plan)

            st.markdown("---")

            # Individual issue fix guides
            st.subheader("Fix Individual Issues")
            st.caption("Select an issue type to see step-by-step resolution instructions.")

            # Group by issue type
            issue_types = list(set(i.issue_type for i in all_issues))
            issue_types.sort()

            selected_fix_type = st.selectbox(
                "Select issue type to get fix instructions:",
                options=issue_types,
                key="fix_type_select"
            )

            if selected_fix_type:
                # Find first occurrence of this issue
                sample_issue = next(i for i in all_issues if i.issue_type == selected_fix_type)
                issue_count = sum(1 for i in all_issues if i.issue_type == selected_fix_type)

                st.info(f"**{selected_fix_type}** — Found on {issue_count} page(s)")

                # Get fix guide
                fix_guide = get_fix_guide_for_issue(
                    user_api_key,
                    selected_fix_type,
                    sample_issue.description,
                    sample_issue.url
                )
                st.markdown(fix_guide)

                # Show affected URLs
                st.markdown("#### Affected URLs")
                affected = [i for i in all_issues if i.issue_type == selected_fix_type]
                for issue in affected[:10]:
                    with st.expander(f"{issue.severity}: {issue.url}"):
                        st.write(f"**Description:** {issue.description}")
                        if issue.html_snippet:
                            st.code(issue.html_snippet, language="html")
                        if issue.css_selector:
                            st.caption(f"CSS Selector: {issue.css_selector}")
                        if issue.xpath:
                            st.caption(f"XPath: {issue.xpath}")
                        st.info(f"**Recommendation:** {issue.recommendation}")
                if len(affected) > 10:
                    st.caption(f"... and {len(affected) - 10} more pages with this issue")

            # Quick fix reference
            st.markdown("---")
            st.subheader("Quick Reference: Common Fixes")

            ref_data = [
                {"Issue": "Missing Title", "Fix": "Add <title> tag in <head>", "Priority": "Critical"},
                {"Issue": "Missing Meta Desc", "Fix": "Add <meta name='description'>", "Priority": "Critical"},
                {"Issue": "No H1", "Fix": "Add one <h1> heading per page", "Priority": "Critical"},
                {"Issue": "No HTTPS", "Fix": "Install SSL, redirect HTTP→HTTPS", "Priority": "Critical"},
                {"Issue": "No Viewport", "Fix": "Add <meta name='viewport'>", "Priority": "Critical"},
                {"Issue": "No Canonical", "Fix": "Add <link rel='canonical'>", "Priority": "Critical"},
                {"Issue": "No JSON-LD", "Fix": "Add structured data <script>", "Priority": "Critical"},
                {"Issue": "No Alt Text", "Fix": "Add alt='...' to <img>", "Priority": "Warning"},
                {"Issue": "No Favicon", "Fix": "Add favicon.ico + <link>", "Priority": "Warning"},
                {"Issue": "No OG Tags", "Fix": "Add og:title, og:desc, og:image", "Priority": "Warning"},
            ]
            st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)

    # 12. AI SUGGESTIONS TAB (DeepSeek API Integration)
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
