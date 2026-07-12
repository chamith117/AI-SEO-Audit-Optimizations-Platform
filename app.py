"""Streamlit Web Application for the AI-Powered SEO Platform.
"""

import csv
import io
import os
import tempfile
import time
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
    export_report_to_xml_sitemap,
)
from ai_seo_audit.keyword_research import (
    extract_keywords_from_report,
    get_page_text_content,
)
from ai_seo_audit.fix_guides import get_fix_guide, get_fix_guide_as_markdown, get_all_fix_guides, FIX_GUIDES
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
    generate_breadcrumb_schema,
    generate_organization_schema,
    generate_faq_schema,
    generate_article_schema,
    generate_webpage_schema,
    generate_local_business_schema,
    generate_product_schema,
    generate_website_search_schema,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_keyword_magic,
    generate_keyword_clusters,
    get_keyword_questions,
    test_api_connection,
    generate_ai_breadcrumbs,
    generate_ai_faqs,
    generate_ai_schema_for_page,
    validate_schema_for_google,
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
st.sidebar.caption("Audit & Optimize Content via OpenRouter AI")

# Load API key from Streamlit secrets or environment variable
_default_key = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
if not _default_key:
    _default_key = st.secrets.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))

# Sidebar: API key input
user_api_key = st.sidebar.text_input(
    "OpenRouter API Key",
    value=_default_key,
    type="password",
    help="Get your key at openrouter.ai/keys"
)

# Model selector
AI_MODELS = [
    ("deepseek/deepseek-chat", "DeepSeek Chat (Fast, Cheap)"),
    ("deepseek/deepseek-r1", "DeepSeek R1 (Reasoning)"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
    ("openai/gpt-4o", "GPT-4o"),
    ("openai/gpt-4o-mini", "GPT-4o Mini (Fast, Cheap)"),
    ("google/gemini-2.0-flash-001", "Gemini 2.0 Flash"),
    ("meta-llama/llama-3.1-8b-instruct:free", "Llama 3.1 8B (Free)"),
]

selected_model = st.sidebar.selectbox(
    "AI Model:",
    options=[m[0] for m in AI_MODELS],
    format_func=lambda x: next((m[1] for m in AI_MODELS if m[0] == x), x),
    index=0,
    key="ai_model_select"
)

# API connection test
if user_api_key:
    if "api_status" not in st.session_state:
        with st.spinner("Testing API connection..."):
            success, msg = test_api_connection(user_api_key, selected_model)
            st.session_state.api_status = (success, msg)
    success, msg = st.session_state.api_status
    if success:
        st.sidebar.success(f"✅ {msg}")
    else:
        st.sidebar.error(f"❌ {msg}")
else:
    st.sidebar.info("Enter your OpenRouter API key above")

st.sidebar.markdown("---")
st.sidebar.subheader("Crawl & Scan Limits")
max_pages = st.sidebar.number_input("Max Pages", min_value=1, max_value=5000, value=30)
max_depth = st.sidebar.number_input("Max Depth", min_value=1, max_value=10, value=3)
check_links = st.sidebar.checkbox("Validate Broken Links", value=True)
check_images = st.sidebar.checkbox("Validate Broken Images", value=True)
js_render = st.sidebar.checkbox(
    "JS Render (Playwright)",
    value=False,
    help="Use headless Chromium to render JavaScript pages. Required for React/Vue/Angular SPAs. Requires: pip install playwright && playwright install chromium"
)

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
    st.write("Research keywords like Semrush: enter a seed keyword or URL to discover opportunities, clusters, and questions.")

    # Mode selector
    kw_mode = st.radio(
        "Research Mode:",
        options=["Seed Keyword (Magic Tool)", "URL Analysis"],
        horizontal=True,
        key="kw_mode"
    )

    if kw_mode == "Seed Keyword (Magic Tool)":
        st.subheader("Keyword Magic Tool")
        st.caption("Enter a seed keyword to discover thousands of related keywords with volume, difficulty, CPC, and intent data.")

        kw_col1, kw_col2 = st.columns([3, 1])
        with kw_col1:
            seed_keyword = st.text_input(
                "Enter seed keyword:",
                value="",
                placeholder="e.g. seo audit tool",
                key="seed_keyword_input"
            )
        with kw_col2:
            match_filter = st.selectbox(
                "Match Type:",
                options=["All", "Broad", "Phrase", "Exact", "Related", "Questions"],
                key="match_type_filter"
            )

        if st.button("Search Keywords", type="primary", key="kw_magic_btn") and seed_keyword:
            match_type = match_filter.lower() if match_filter != "All" else "all"
            with st.spinner(f"Generating keyword ideas for '{seed_keyword}'..."):
                kw_data = generate_keyword_magic(user_api_key, seed_keyword, match_type, model=selected_model)
                st.session_state.kw_magic_data = kw_data
                st.session_state.kw_magic_seed = seed_keyword

        if "kw_magic_data" in st.session_state:
            kw_data = st.session_state.kw_magic_data
            seed = st.session_state.kw_magic_seed

            # Top metrics
            all_kws = kw_data.get("keywords", [])
            total_vol = sum(k.get("volume", 0) for k in all_kws)
            avg_kd = sum(k.get("kd", 0) for k in all_kws) // len(all_kws) if all_kws else 0

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            with m1:
                st.metric("Total Keywords", len(all_kws))
            with m2:
                st.metric("Total Volume", f"{total_vol:,}")
            with m3:
                st.metric("Avg. KD", f"{avg_kd}%")
            with m4:
                questions = [k for k in all_kws if k.get("match_type") == "question"]
                st.metric("Questions", len(questions))
            with m5:
                broad = [k for k in all_kws if k.get("match_type") == "broad"]
                st.metric("Broad", len(broad))
            with m6:
                exact = [k for k in all_kws if k.get("match_type") == "exact"]
                st.metric("Exact", len(exact))

            st.markdown("---")

            # Match type tabs
            tab_all, tab_broad, tab_phrase, tab_exact, tab_related, tab_questions = st.tabs(
                ["All Keywords", "Broad Match", "Phrase Match", "Exact Match", "Related", "Questions"]
            )

            def render_kw_table(keywords_list, show_match=True, tab_key="all"):
                if not keywords_list:
                    st.info("No keywords found for this filter.")
                    return
                table_data = []
                for k in keywords_list:
                    kd = k.get("kd", 0)
                    if kd <= 29:
                        kd_label = f"🟢 {kd}"
                    elif kd <= 49:
                        kd_label = f"🟡 {kd}"
                    elif kd <= 69:
                        kd_label = f"🟠 {kd}"
                    else:
                        kd_label = f"🔴 {kd}"

                    vol = k.get("volume", 0)
                    if vol >= 10000:
                        vol_label = f"🔥 {vol:,}"
                    elif vol >= 1000:
                        vol_label = f"{vol:,}"
                    else:
                        vol_label = str(vol)

                    row = {
                        "Keyword": k.get("keyword", ""),
                        "Volume": vol_label,
                        "KD%": kd_label,
                        "CPC": f"${k.get('cpc', 0):.2f}",
                        "Competition": k.get("competition", 0),
                        "Intent": k.get("intent", ""),
                        "Trend": {"Rising": "📈", "Stable": "➡️", "Declining": "📉"}.get(k.get("trend", ""), ""),
                        "SERP Features": ", ".join(k.get("serp_features", [])),
                        "Click Potential": k.get("click_potential", ""),
                    }
                    if show_match:
                        row["Match"] = k.get("match_type", "").title()
                    table_data.append(row)

                df = pd.DataFrame(table_data)

                # Search filter
                search = st.text_input("Search keywords...", "", key=f"kw_search_{tab_key}")
                if search:
                    df = df[df["Keyword"].str.contains(search, case=False)]

                st.dataframe(df, use_container_width=True, hide_index=True)

                # Export
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "📥 Export to CSV",
                    data=csv_data,
                    file_name=f"keywords_{seed.replace(' ', '_')}_{tab_key}.csv",
                    mime="text/csv",
                    key=f"export_{tab_key}"
                )

            with tab_all:
                render_kw_table(all_kws, show_match=True, tab_key="all")
            with tab_broad:
                render_kw_table([k for k in all_kws if k.get("match_type") == "broad"], tab_key="broad")
            with tab_phrase:
                render_kw_table([k for k in all_kws if k.get("match_type") == "phrase"], tab_key="phrase")
            with tab_exact:
                render_kw_table([k for k in all_kws if k.get("match_type") == "exact"], tab_key="exact")
            with tab_related:
                render_kw_table([k for k in all_kws if k.get("match_type") == "related"], tab_key="related")
            with tab_questions:
                render_kw_table([k for k in all_kws if k.get("match_type") == "question"], tab_key="questions")

            # Keyword Clustering
            st.markdown("---")
            st.subheader("Keyword Clusters")
            st.caption("Group related keywords into topical clusters for content planning.")

            if st.button("Generate Clusters", type="primary", key="kw_cluster_btn"):
                with st.spinner("Clustering keywords by topic..."):
                    kw_list = [k.get("keyword", "") for k in all_kws]
                    clusters = generate_keyword_clusters(user_api_key, kw_list, seed, model=selected_model)
                    st.session_state.kw_clusters = clusters

            if "kw_clusters" in st.session_state:
                clusters = st.session_state.kw_clusters.get("clusters", [])
                if clusters:
                    for cluster in clusters:
                        with st.expander(f"📁 {cluster.get('name', 'Cluster')} ({len(cluster.get('keywords', []))} keywords)"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.metric("Avg Volume", f"{cluster.get('avg_volume', 0):,}")
                            with c2:
                                st.metric("Avg KD", f"{cluster.get('avg_kd', 0)}%")
                            with c3:
                                st.metric("Intent", cluster.get("recommended_intent", ""))
                            st.write("**Keywords:**")
                            for kw in cluster.get("keywords", []):
                                st.write(f"- {kw}")

            # Content Ideas from Keywords
            st.markdown("---")
            st.subheader("AI Content Ideas")
            if st.button("Generate Content Ideas", type="primary", key="kw_ideas_btn_magic"):
                with st.spinner("Generating content ideas from keywords..."):
                    existing = [k.get("keyword", "") for k in all_kws[:10]]
                    ideas = get_content_ideas(user_api_key, f"Seed keyword: {seed}", existing)
                    st.session_state.kw_ideas_magic_result = ideas
            if "kw_ideas_magic_result" in st.session_state:
                st.markdown(st.session_state.kw_ideas_magic_result)

    else:
        # URL Analysis mode (existing code)
        st.subheader("URL Analysis Mode")
        st.caption("Enter a URL to extract keywords from the page content.")
        kw_url_input = st.text_input(
            "Enter URL to analyze:",
            value="https://example.com",
            placeholder="https://yourwebsite.com",
            key="kw_url_input"
        )

        if st.button("Analyze Keywords", type="primary", key="kw_url_btn"):
            if not kw_url_input.startswith(("http://", "https://")):
                st.error("Please enter a valid URL starting with http:// or https://")
            else:
                with st.spinner(f"Fetching and analyzing: {kw_url_input}"):
                    try:
                        fetch_crawler = SafeCrawler(verify_ssl=False, js_render=js_render)
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

        # Display URL analysis results
        if "kw_result" in st.session_state:
            kw = st.session_state.kw_result
            meta = st.session_state.kw_metadata
            pg = st.session_state.kw_page
            full_text = st.session_state.kw_text

            st.markdown("---")
            st.markdown(f"### Keyword Analysis: `{pg.url}`")
            st.caption(f"Page Score: {pg.score}/100 | Status: {pg.status_code}")

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

            st.subheader("Keyword Overview")
            if kw.primary_keywords or kw.secondary_keywords:
                all_kws = kw.primary_keywords + kw.secondary_keywords
                kw_table_data = []
                for k in all_kws:
                    if k.density >= 3.0:
                        difficulty = "Hard"
                    elif k.density >= 1.5:
                        difficulty = "Medium"
                    else:
                        difficulty = "Easy"

                    intent = "Informational"
                    if k.in_url:
                        intent = "Navigational"
                    if any(w in k.keyword for w in ["buy", "price", "cost", "cheap", "deal", "discount", "order"]):
                        intent = "Transactional"
                    elif any(w in k.keyword for w in ["best", "top", "review", "comparison", "vs", "alternative"]):
                        intent = "Commercial"

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
                kw_search = st.text_input("Search keywords...", "", key="kw_search_filter")
                if kw_search:
                    df_kw = df_kw[df_kw["Keyword"].str.contains(kw_search, case=False)]
                st.dataframe(df_kw, use_container_width=True, hide_index=True)

                # Export
                csv_data = df_kw.to_csv(index=False)
                st.download_button("📥 Export to CSV", data=csv_data, file_name="url_keywords.csv", mime="text/csv")

            # Keyword detail view
            st.markdown("---")
            st.subheader("Keyword Detail View")
            all_kw_names = [k.keyword for k in (kw.primary_keywords + kw.secondary_keywords)]
            sel_kw = st.selectbox("Select keyword for full analysis:", options=all_kw_names, key="kw_detail_sel")
            kw_obj = next((k for k in (kw.primary_keywords + kw.secondary_keywords) if k.keyword == sel_kw), None)

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

            # AI Analysis
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
        safe_crawler = SafeCrawler(verify_ssl=False, js_render=js_render)
        site_crawler = SiteCrawler(
            crawler=safe_crawler,
            max_pages=max_pages,
            max_depth=max_depth,
            respect_robots=True
        )

        # Streamlit progress tracking
        progress_bar = st.progress(0.0)
        crawl_results_stored = []
        redirect_data = {}
        crawl_start_time = time.time()

        for current_url, count, crawl_result, queue_size in site_crawler.crawl_site(url_input):
            pct = min(1.0, count / max_pages)
            progress_bar.progress(pct, text=f"{pct*100:.0f}%")
            elapsed_so_far = time.time() - crawl_start_time
            pages_per_sec = count / elapsed_so_far if elapsed_so_far > 0 else 0
            remaining = (max_pages - count) / pages_per_sec if pages_per_sec > 0 else 0

            # Show redirect chain in status if present
            redirect_info = ""
            if crawl_result and crawl_result.has_redirect:
                chain = crawl_result.redirect_chain_display
                redirect_info = f"\n↪️ Redirect: {chain}"

            status_text.caption(
                f"🕷️ Scanning ({count}/{max_pages}): {current_url} | "
                f"Queue: {queue_size} | "
                f"Elapsed: {elapsed_so_far:.0f}s | "
                f"Speed: {pages_per_sec:.1f} pages/s | "
                f"ETA: {remaining:.0f}s"
                f"{redirect_info}"
            )

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
                # Store redirect chain data for this page
                if crawl_result.has_redirect:
                    redirect_data[page_report.url] = crawl_result.redirect_chain_display

        progress_bar.progress(1.0)
        crawl_total_time = time.time() - crawl_start_time
        crawl_pages_done = len(pages_audited)
        status_text.success(
            f"✅ Crawl complete: {crawl_pages_done} pages in {crawl_total_time:.1f}s "
            f"({crawl_pages_done / crawl_total_time:.1f} pages/s)"
        )
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
        st.session_state.redirect_data = redirect_data
        status_text.empty()
        progress_bar.empty()
        st.success("✅ Audit complete! Scroll down to view your dashboard.")

# If report is loaded, show the dashboard
if st.session_state.report:
    report: WebsiteAuditReport = st.session_state.report
    redirect_data = st.session_state.get("redirect_data", {})
    
    # Pre-collect stats
    total_issues = len(report.site_issues) + sum(len(p.issues) for p in report.pages)
    critical_count = sum(1 for i in report.site_issues if i.severity == "CRITICAL") + \
                     sum(sum(1 for i in p.issues if i.severity == "CRITICAL") for p in report.pages)
    warning_count = sum(1 for i in report.site_issues if i.severity == "WARNING") + \
                    sum(sum(1 for i in p.issues if i.severity == "WARNING") for p in report.pages)
    info_count = total_issues - (critical_count + warning_count)

    # Core Navigation Tabs
    tab_report, tab_overview, tab_tech, tab_content, tab_images, tab_links, tab_perf, tab_data, tab_keywords, tab_advanced, tab_fix, tab_ai = st.tabs([
        "📑 Full Report",
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

    # 0. FULL REPORT TAB (Chapter-based with Table of Contents)
    with tab_report:
        st.subheader("📑 Full Audit Report")
        st.caption("A comprehensive, chapter-by-chapter breakdown of your site's SEO health.")

        # Collect all issues
        all_issues = []
        for p in report.pages:
            for issue in p.issues:
                all_issues.append(issue)
        for issue in report.site_issues:
            all_issues.append(issue)

        # Group issues by chapter and section
        chapters = {
            "1. Critical Errors": {
                "description": "Issues that directly harm your rankings and must be fixed immediately.",
                "sections": {}
            },
            "2. Technical SEO": {
                "description": "Server configuration, crawlability, and indexability issues.",
                "sections": {}
            },
            "3. Content Quality": {
                "description": "Title tags, meta descriptions, headings, and content issues.",
                "sections": {}
            },
            "4. Images & Media": {
                "description": "Image optimization, alt text, and media-related issues.",
                "sections": {}
            },
            "5. Links & Navigation": {
                "description": "Internal linking, external links, and navigation structure.",
                "sections": {}
            },
            "6. Structured Data & Social": {
                "description": "Schema markup, Open Graph, and social media tags.",
                "sections": {}
            },
            "7. Performance & Security": {
                "description": "Page speed, HTTPS, and security-related issues.",
                "sections": {}
            }
        }

        # Categorize issues into chapters
        for issue in all_issues:
            issue_type = issue.issue_type
            severity = issue.severity

            # Determine chapter based on issue type
            if severity == "CRITICAL" or issue_type in ["Missing Title", "Missing Meta Description", "Missing H1", "No HTTPS"]:
                chapter = "1. Critical Errors"
            elif issue_type in ["Missing robots.txt", "Missing Sitemap", "Canonical Issues", "Redirect Issues",
                               "Missing Hreflang", "Robots Meta Tag", "X-Robots-Tag", "Pagination Issues",
                               "Soft 404 Detected", "Server Error (5xx)", "404 Page Not Found", "403 Forbidden",
                               "Other Client Error (4xx)", "Redirect Loop", "Too Many Redirects"]:
                chapter = "2. Technical SEO"
            elif issue_type in ["Title Too Short", "Title Too Long", "Title Duplicate", "Meta Description Too Short",
                               "Meta Description Too Long", "Meta Description Duplicate", "Missing Viewport",
                               "Content Quality", "Thin Content", "Missing H1", "Duplicate H1",
                               "Multiple H1s", "Heading Hierarchy"]:
                chapter = "3. Content Quality"
            elif issue_type in ["Missing Image Alt", "Image Alt Too Long", "Image Alt Duplicate",
                               "Large Image", "Missing Image Dimensions", "Image Format"]:
                chapter = "4. Images & Media"
            elif issue_type in ["Internal Links", "External Links", "Broken Links",
                               "Orphan Pages", "Missing Internal Links"]:
                chapter = "5. Links & Navigation"
            elif issue_type in ["Missing Structured Data", "Invalid Structured Data",
                               "Missing Open Graph", "Missing Twitter Cards", "Missing Favicon"]:
                chapter = "6. Structured Data & Social"
            elif issue_type in ["Slow Page", "Mixed Content", "Missing SSL",
                               "Missing Security Headers", "Missing Cache Policy"]:
                chapter = "7. Performance & Security"
            else:
                chapter = "2. Technical SEO"

            # Add to chapter section
            if issue_type not in chapters[chapter]["sections"]:
                chapters[chapter]["sections"][issue_type] = []
            chapters[chapter]["sections"][issue_type].append(issue)

        # === TABLE OF CONTENTS ===
        st.markdown("---")
        st.subheader("📋 Table of Contents")
        st.caption("Click on any chapter to jump to that section.")

        toc_html = '<div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333;">'
        for chapter_name, chapter_data in chapters.items():
            if chapter_data["sections"]:
                total_in_chapter = sum(len(issues) for issues in chapter_data["sections"].values())
                critical_in_chapter = sum(1 for issues in chapter_data["sections"].values() for i in issues if i.severity == "CRITICAL")

                # Chapter header with count
                toc_html += f'<div style="margin-bottom: 15px;">'
                toc_html += f'<strong style="font-size: 16px;">{chapter_name}</strong>'
                toc_html += f' <span style="color: #888;">({total_in_chapter} issues'

                if critical_in_chapter > 0:
                    toc_html += f' - <span style="color: #ff4444;">{critical_in_chapter} critical</span>'
                toc_html += ')</span></div>'

                # Section links
                for section_name, section_issues in chapter_data["sections"].items():
                    section_critical = sum(1 for i in section_issues if i.severity == "CRITICAL")
                    icon = "🔴" if section_critical > 0 else "🟡"
                    toc_html += f'<div style="margin-left: 20px; margin-bottom: 5px;">'
                    toc_html += f'{icon} <a href="#{section_name.replace(" ", "_").lower()}" style="color: #4da6ff; text-decoration: none;">{section_name}</a>'
                    toc_html += f' <span style="color: #666;">({len(section_issues)} pages)</span></div>'

        toc_html += '</div>'
        st.markdown(toc_html, unsafe_allow_html=True)

        st.markdown("---")

        # === CHAPTERS ===
        for chapter_name, chapter_data in chapters.items():
            if not chapter_data["sections"]:
                continue

            total_in_chapter = sum(len(issues) for issues in chapter_data["sections"].values())
            critical_in_chapter = sum(1 for issues in chapter_data["sections"].values() for i in issues if i.severity == "CRITICAL")

            # Chapter header
            st.markdown(f"## {chapter_name}")
            st.caption(chapter_data["description"])

            # Chapter summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Issues", total_in_chapter)
            with col2:
                st.metric("Critical", critical_in_chapter)
            with col3:
                st.metric("Pages Affected", len(set(i.url for issues in chapter_data["sections"].values() for i in issues)))

            # Sections within chapter
            for section_name, section_issues in chapter_data["sections"].items():
                st.markdown(f"### {section_name}")

                # Section info
                section_critical = sum(1 for i in section_issues if i.severity == "CRITICAL")
                section_warning = sum(1 for i in section_issues if i.severity == "WARNING")
                affected_pages = list(set(i.url for i in section_issues))

                # Section summary
                st.info(f"**{len(section_issues)}** issues found on **{len(affected_pages)}** page(s) — "
                        f"🔴 {section_critical} critical | 🟡 {section_warning} warnings")

                # Affected pages table
                issue_data = []
                for issue in section_issues:
                    issue_data.append({
                        "URL": issue.url,
                        "Severity": issue.severity,
                        "Description": issue.description,
                        "Recommendation": issue.recommendation
                    })

                if issue_data:
                    st.dataframe(pd.DataFrame(issue_data), use_container_width=True, hide_index=True)

                # Fix guide for this section
                with st.expander(f"📖 How to Fix: {section_name}", expanded=False):
                    guide_content = get_fix_guide_as_markdown(section_name)
                    st.markdown(guide_content)

                st.markdown("---")

            # Chapter separator
            st.markdown("---")

    # 1. OVERVIEW TAB
    with tab_overview:
        # === TOP ROW: Score + Site Health ===
        col_gauge, col_health = st.columns([1.2, 2.8])

        with col_gauge:
            st.plotly_chart(draw_gauge(report.score), use_container_width=True)
            st.markdown(f"<h3 style='text-align: center; color: {get_score_color(report.score)}'>{get_score_description(report.score)}</h3>", unsafe_allow_html=True)

        with col_health:
            st.subheader("Site Health Summary")

            # Health score breakdown
            health_items = []
            https_pct = sum(1 for p in report.pages if p.is_https) / max(1, len(report.pages)) * 100
            health_items.append(("HTTPS Security", https_pct, "green" if https_pct == 100 else ("orange" if https_pct > 50 else "red")))
            health_items.append(("robots.txt", 100 if report.robots_txt_found else 0, "green" if report.robots_txt_found else "red"))
            health_items.append(("sitemap.xml", 100 if report.sitemap_xml_found else 0, "green" if report.sitemap_xml_found else "red"))

            # Content health
            pages_with_title = sum(1 for p in report.pages if p.metadata.title)
            title_pct = pages_with_title / max(1, len(report.pages)) * 100
            health_items.append(("Title Tags", title_pct, "green" if title_pct > 90 else ("orange" if title_pct > 50 else "red")))

            pages_with_meta = sum(1 for p in report.pages if p.metadata.meta_description)
            meta_pct = pages_with_meta / max(1, len(report.pages)) * 100
            health_items.append(("Meta Descriptions", meta_pct, "green" if meta_pct > 90 else ("orange" if meta_pct > 50 else "red")))

            pages_with_h1 = sum(1 for p in report.pages if p.metadata.headings and any(h.level == 1 for h in p.metadata.headings))
            h1_pct = pages_with_h1 / max(1, len(report.pages)) * 100
            health_items.append(("H1 Tags", h1_pct, "green" if h1_pct > 90 else ("orange" if h1_pct > 50 else "red")))

            # Advanced audit health
            if report.advanced_audit:
                adv = report.advanced_audit
                sec_health = max(0, 100 - (adv.total_security_issues * 10))
                health_items.append(("Security Headers", sec_health, "green" if sec_health > 80 else ("orange" if sec_health > 50 else "red")))

                mixed_health = max(0, 100 - (adv.total_mixed_content * 15))
                health_items.append(("Mixed Content", mixed_health, "green" if mixed_health > 80 else ("orange" if mixed_health > 50 else "red")))

                thin_health = max(0, 100 - (adv.total_thin_content * 20))
                health_items.append(("Content Quality", thin_health, "green" if thin_health > 80 else ("orange" if thin_health > 50 else "red")))

            # Render health bars
            for label, pct, color in health_items:
                c1, c2, c3 = st.columns([2, 4, 1])
                with c1:
                    st.caption(label)
                with c2:
                    st.progress(pct / 100)
                with c3:
                    st.caption(f"**{pct:.0f}%**")

        st.markdown("---")

        # === ROW 2: Key Metric Cards ===
        st.subheader("Key Metrics")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.metric("Pages Crawled", report.total_pages_crawled)
        with m2:
            st.metric("Total Issues", total_issues)
        with m3:
            st.metric("Critical", critical_count, delta=None, delta_color="inverse")
        with m4:
            st.metric("Warnings", warning_count, delta=None, delta_color="inverse")
        with m5:
            st.metric("Advisory", info_count)
        with m6:
            avg_score = sum(p.score for p in report.pages) // max(1, len(report.pages))
            st.metric("Avg Page Score", f"{avg_score}/100")

        st.markdown("---")

        # === ROW 3: AI Visibility + Security + Content Quality ===
        st.subheader("Advanced Insights")
        av_col, sec_col, con_col = st.columns(3)

        with av_col:
            st.markdown("#### AI Visibility Score")
            # Use the new report score
            avg_ai = report.ai_visibility_score
            ai_grades = {90: "A+", 80: "A", 70: "B", 60: "C", 50: "D", 0: "F"}
            grade = "F"
            for threshold, g in sorted(ai_grades.items(), reverse=True):
                if avg_ai >= threshold:
                    grade = g
                    break
            st.metric("Overall AI Score", f"{avg_ai}/100", help="How visible your site is to AI search engines (ChatGPT, Perplexity, Google AI)")
            st.markdown(f"<h2 style='text-align:center; color:{get_score_color(avg_ai)}'>{grade}</h2>", unsafe_allow_html=True)

        with sec_col:
            st.markdown("#### Site Speed Score")
            speed = report.site_speed_score
            speed_grades = {90: "Fast", 70: "Good", 50: "Average", 30: "Slow", 0: "Very Slow"}
            speed_grade = "Very Slow"
            for threshold, g in sorted(speed_grades.items(), reverse=True):
                if speed >= threshold:
                    speed_grade = g
                    break
            st.metric("Speed Score", f"{speed}/100", help="Page speed performance based on response time, page size, and lazy loading")
            st.markdown(f"<h2 style='text-align:center; color:{get_score_color(speed)}'>{speed_grade}</h2>", unsafe_allow_html=True)
            st.caption(f"Avg Response: {report.avg_response_time_ms:.0f}ms")

        with con_col:
            st.markdown("#### Site Health Score")
            health = report.site_health_score
            health_grades = {90: "Excellent", 70: "Good", 50: "Fair", 30: "Poor", 0: "Critical"}
            health_grade = "Critical"
            for threshold, g in sorted(health_grades.items(), reverse=True):
                if health >= threshold:
                    health_grade = g
                    break
            st.metric("Health Score", f"{health}/100", help="Overall site health combining SEO, AI visibility, speed, and technical factors")
            st.markdown(f"<h2 style='text-align:center; color:{get_score_color(health)}'>{health_grade}</h2>", unsafe_allow_html=True)

        st.markdown("---")

        # === ROW 4: Technical Checklist ===
        st.subheader("Technical Checklist")
        tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
        with tech_col1:
            st.checkbox("HTTPS", value=all(p.is_https for p in report.pages), disabled=True, key="ov_https")
            st.checkbox("robots.txt", value=report.robots_txt_found, disabled=True, key="ov_robots")
        with tech_col2:
            st.checkbox("sitemap.xml", value=report.sitemap_xml_found, disabled=True, key="ov_sitemap")
            has_canonical = sum(1 for p in report.pages if any(i.issue_type == "Canonical Tag" for i in p.issues))
            st.checkbox("Canonical Tags", value=(has_canonical == 0), disabled=True, key="ov_canonical")
        with tech_col3:
            has_viewport = sum(1 for p in report.pages if not any(i.issue_type == "Missing Viewport Tag" for i in p.issues))
            st.checkbox("Viewport Meta", value=(has_viewport > 0), disabled=True, key="ov_viewport")
            has_lang = sum(1 for p in report.pages if p.metadata.lang)
            st.checkbox("Lang Attribute", value=(has_lang > 0), disabled=True, key="ov_lang")
        with tech_col4:
            has_favicon = sum(1 for p in report.pages if not any(i.issue_type == "Missing Favicon" for i in p.issues))
            st.checkbox("Favicon", value=(has_favicon > 0), disabled=True, key="ov_favicon")
            st.checkbox("No Redirect Chains", value=(len(report.redirect_chains) == 0), disabled=True, key="ov_redirects")

        st.markdown("---")

        # === ROW 5: Duplicate & Orphan Pages ===
        dup_col, orphan_col, redirect_col = st.columns(3)
        with dup_col:
            st.metric("Duplicate Title Groups", len(report.duplicate_titles))
            st.metric("Duplicate Meta Groups", len(report.duplicate_descriptions))
            st.metric("Duplicate Content Groups", len(report.duplicate_pages))
        with orphan_col:
            st.metric("Orphan Pages", len(report.orphan_pages))
            if report.orphan_pages:
                with st.expander("View Orphan Pages"):
                    for op in report.orphan_pages[:10]:
                        st.write(f"- {op}")
        with redirect_col:
            st.metric("Redirect Chains", len(report.redirect_chains))
            if report.redirect_chains:
                with st.expander("View Redirect Chains"):
                    for url, chain in list(report.redirect_chains.items())[:10]:
                        st.write(f"**{url}**")
                        st.caption(" → ".join(chain))

        st.markdown("---")

        st.markdown("---")
        st.subheader("Download Audit Exports")
        
        # Download utilities in memory
        col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)
        
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

        # XML Sitemap Export bytes
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp_xml:
            export_report_to_xml_sitemap(report, tmp_xml.name)
            with open(tmp_xml.name, "r", encoding="utf-8") as f:
                xml_bytes = f.read()
        with col_d5:
            st.download_button(
                label="📥 Download XML Sitemap",
                data=xml_bytes,
                file_name="sitemap.xml",
                mime="application/xml",
                use_container_width=True
            )

        # llms.txt Export
        llms_pages = [{"title": p.metadata.title or p.url, "url": p.url, "description": p.metadata.meta_description or ""} for p in report.pages[:20]]
        llms_txt_content = generate_llms_txt(
            site_name=report.start_url.split("//")[-1].split("/")[0],
            site_url=report.start_url,
            site_description=f"AI SEO Audit Report for {report.start_url}. Score: {report.score}/100.",
            pages=llms_pages,
        )
        llms_full_content = generate_llms_full_txt(
            site_name=report.start_url.split("//")[-1].split("/")[0],
            site_url=report.start_url,
            site_description=f"AI SEO Audit Report for {report.start_url}. Score: {report.score}/100.",
            pages=llms_pages,
        )

        st.markdown("---")
        st.subheader("AI-Ready Files (llms.txt)")
        st.caption("Files that help AI language models (ChatGPT, Claude, Gemini) understand your website.")

        llm_col1, llm_col2 = st.columns(2)
        with llm_col1:
            st.download_button(
                "Download llms.txt",
                data=llms_txt_content,
                file_name="llms.txt",
                mime="text/plain",
                use_container_width=True,
                help="Standard format for AI models to understand your site"
            )
        with llm_col2:
            st.download_button(
                "Download llms-full.txt",
                data=llms_full_content,
                file_name="llms-full.txt",
                mime="text/plain",
                use_container_width=True,
                help="Extended format with full page details for AI models"
            )

        with st.expander("Preview llms.txt"):
            st.code(llms_txt_content, language="text")
        with st.expander("Preview llms-full.txt"):
            st.code(llms_full_content, language="text")

        st.markdown("---")
        st.subheader("Crawled Pages Overview")
        
        # Interactive table with search filter
        df_pages = pd.DataFrame([{
            "URL": p.url,
            "HTTP Status": p.status_code,
            "Security": "HTTPS" if p.is_https else "HTTP",
            "SEO Score": f"{p.score}/100",
            "Issues count": len(p.issues),
            "Redirect Chain": redirect_data.get(p.url, "")
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

        # --- Site-Level Technical Summary ---
        st.subheader("Site-Level Technical Summary")
        tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
        with tech_col1:
            st.metric("Orphan Pages", len(report.orphan_pages))
        with tech_col2:
            st.metric("Duplicate Titles", len(report.duplicate_titles))
        with tech_col3:
            st.metric("Duplicate Metas", len(report.duplicate_descriptions))
        with tech_col4:
            st.metric("Duplicate Content", len(report.duplicate_pages))

        # Redirect chains
        st.metric("Redirect Chains", len(report.redirect_chains))
        if report.redirect_chains:
            with st.expander("View Redirect Chains"):
                for redir_url, chain in list(report.redirect_chains.items())[:10]:
                    st.write(f"**{redir_url}**")
                    st.caption(" → ".join(chain))

        # Orphan pages
        if report.orphan_pages:
            with st.expander(f"View {len(report.orphan_pages)} Orphan Page(s)"):
                for op in report.orphan_pages:
                    st.write(f"- {op}")

        # Duplicate titles
        if report.duplicate_titles:
            with st.expander(f"View {len(report.duplicate_titles)} Duplicate Title Group(s)"):
                for title, urls in report.duplicate_titles.items():
                    st.write(f"**Title:** {title}")
                    for u in urls:
                        st.write(f"  - {u}")

        # Duplicate descriptions
        if report.duplicate_descriptions:
            with st.expander(f"View {len(report.duplicate_descriptions)} Duplicate Meta Description Group(s)"):
                for desc, urls in report.duplicate_descriptions.items():
                    st.write(f"**Description:** {desc[:100]}...")
                    for u in urls:
                        st.write(f"  - {u}")

        st.write("")
        st.subheader("HTTP Status Code Analysis")

        # HTTP Status Code Distribution
        status_counts = {}
        error_pages = []
        for p in report.pages:
            status = p.status_code
            status_counts[status] = status_counts.get(status, 0) + 1
            if status and (status >= 400 or status == 0):
                error_pages.append(p)

        # Status code summary
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            ok_count = sum(v for k, v in status_counts.items() if 200 <= k < 300)
            st.metric("2xx Success", ok_count)
        with col_s2:
            redirect_count = sum(v for k, v in status_counts.items() if 300 <= k < 400)
            st.metric("3xx Redirect", redirect_count)
        with col_s3:
            client_error_count = sum(v for k, v in status_counts.items() if 400 <= k < 500)
            st.metric("4xx Client Error", client_error_count)
        with col_s4:
            server_error_count = sum(v for k, v in status_counts.items() if 500 <= k < 600)
            st.metric("5xx Server Error", server_error_count)

        # Detailed HTTP Error Types Table
        st.markdown("##### HTTP Error Types Summary")
        
        # Collect all error types from issues
        error_types = {}
        for p in report.pages:
            for issue in p.issues:
                if issue.severity == "CRITICAL" or issue.severity == "WARNING":
                    if issue.issue_type not in error_types:
                        error_types[issue.issue_type] = {"count": 0, "severity": issue.severity, "urls": []}
                    error_types[issue.issue_type]["count"] += 1
                    if issue.url not in error_types[issue.issue_type]["urls"]:
                        error_types[issue.issue_type]["urls"].append(issue.url)
        
        # Also count from status codes
        status_error_types = {
            "200 OK": sum(v for k, v in status_counts.items() if k == 200),
            "301 Moved Permanently": sum(v for k, v in status_counts.items() if k == 301),
            "302 Found (Redirect)": sum(v for k, v in status_counts.items() if k == 302),
            "304 Not Modified": sum(v for k, v in status_counts.items() if k == 304),
            "400 Bad Request": sum(v for k, v in status_counts.items() if k == 400),
            "401 Unauthorized": sum(v for k, v in status_counts.items() if k == 401),
            "403 Forbidden": sum(v for k, v in status_counts.items() if k == 403),
            "404 Not Found": sum(v for k, v in status_counts.items() if k == 404),
            "405 Method Not Allowed": sum(v for k, v in status_counts.items() if k == 405),
            "408 Request Timeout": sum(v for k, v in status_counts.items() if k == 408),
            "410 Gone": sum(v for k, v in status_counts.items() if k == 410),
            "429 Too Many Requests": sum(v for k, v in status_counts.items() if k == 429),
            "500 Internal Server Error": sum(v for k, v in status_counts.items() if k == 500),
            "502 Bad Gateway": sum(v for k, v in status_counts.items() if k == 502),
            "503 Service Unavailable": sum(v for k, v in status_counts.items() if k == 503),
            "504 Gateway Timeout": sum(v for k, v in status_counts.items() if k == 504),
        }
        
        # Filter to only show errors (non-zero counts)
        error_table_data = []
        for status_type, count in status_error_types.items():
            if count > 0:
                # Determine severity
                if status_type.startswith("2"):
                    severity = "OK"
                    color = "green"
                elif status_type.startswith("3"):
                    severity = "Redirect"
                    color = "orange"
                elif status_type.startswith("4"):
                    severity = "Error"
                    color = "red"
                else:
                    severity = "Critical"
                    color = "red"
                
                error_table_data.append({
                    "HTTP Status": status_type,
                    "Count": count,
                    "Severity": severity
                })
        
        # Add issue-based error types
        for issue_type in ["Soft 404 Detected", "Server Error (5xx)", "404 Page Not Found", 
                          "403 Forbidden", "Other Client Error (4xx)", "Broken Link", "Broken Image"]:
            if issue_type in error_types:
                error_table_data.append({
                    "HTTP Status": issue_type,
                    "Count": error_types[issue_type]["count"],
                    "Severity": error_types[issue_type]["severity"]
                })
        
        if error_table_data:
            df_errors = pd.DataFrame(error_table_data)
            st.dataframe(df_errors, use_container_width=True, hide_index=True)
            
            # Summary
            total_errors = sum(d["Count"] for d in error_table_data if d["Severity"] in ["Error", "Critical"])
            if total_errors > 0:
                st.warning(f"**Total HTTP Errors: {total_errors}** - These issues should be fixed immediately.")
            else:
                st.success("No HTTP errors detected.")
        else:
            st.info("No HTTP status data available.")

        # Status code distribution chart
        if status_counts:
            with st.expander("View Status Code Distribution"):
                for status, count in sorted(status_counts.items()):
                    bar_width = int(count / max(status_counts.values()) * 30)
                    color = "🟢" if 200 <= status < 300 else ("🟡" if 300 <= status < 400 else ("🟠" if 400 <= status < 500 else "🔴"))
                    st.write(f"{color} **{status}**: {'█' * bar_width} {count} pages")

        # Error pages detail
        if error_pages:
            st.warning(f"Found **{len(error_pages)}** pages with HTTP errors (4xx/5xx)")
            with st.expander("View Pages with HTTP Errors", expanded=True):
                error_data = []
                for p in error_pages:
                    error_data.append({
                        "URL": p.url,
                        "Status Code": p.status_code,
                        "Issues": len(p.issues),
                        "Score": f"{p.score}/100"
                    })
                st.dataframe(pd.DataFrame(error_data), use_container_width=True, hide_index=True)
        else:
            st.success("No HTTP errors (4xx/5xx) detected.")

        st.write("")
        st.subheader("Technical Issues Log")

        # --- Page-Level Technical Issues ---
        # Comprehensive list of all technical SEO issue types
        TECHNICAL_ISSUE_TYPES = [
            "HTTPS Security",
            "Missing Canonical URL",
            "Canonical Mismatch",
            "Missing Viewport Tag",
            "Missing Lang Attribute",
            "Missing Favicon",
            "Missing H1 Heading",
            "Multiple H1 Headings",
            "Invalid JSON-LD",
            "Missing Open Graph Tags",
            "Missing Twitter Cards",
            "Missing Title",
            "Title Length",
            "Missing Meta Description",
            "Meta Description Length",
            "Missing Alt Text",
            "Broken Link",
            "Broken Image",
            "Soft 404 Detected",
            "Server Error (5xx)",
            "404 Page Not Found",
            "403 Forbidden",
            "Other Client Error (4xx)",
        ]

        tech_issues = []
        # Include site-level orphan issues
        for issue in report.site_issues:
            if issue.issue_type == "Orphan Pages":
                tech_issues.append(issue)
        # Include page-level technical issues
        for p in report.pages:
            for issue in p.issues:
                if issue.issue_type in TECHNICAL_ISSUE_TYPES:
                    tech_issues.append(issue)

        # Count by severity
        tech_critical = sum(1 for i in tech_issues if i.severity == "CRITICAL")
        tech_warning = sum(1 for i in tech_issues if i.severity == "WARNING")
        tech_info = len(tech_issues) - tech_critical - tech_warning

        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            st.metric("Total Technical Issues", len(tech_issues))
        with tc2:
            st.metric("Critical", tech_critical)
        with tc3:
            st.metric("Warnings", tech_warning)
        with tc4:
            st.metric("Advisory", tech_info)

        st.markdown("---")

        # Issue type filter
        available_types = sorted(set(i.issue_type for i in tech_issues))
        if available_types:
            selected_tech_type = st.multiselect(
                "Filter by issue type:",
                options=available_types,
                default=available_types,
                key="tech_issue_filter"
            )
        else:
            selected_tech_type = []

        filtered_tech_issues = [i for i in tech_issues if i.issue_type in selected_tech_type]

        if not filtered_tech_issues:
            st.success("✓ No technical SEO issues detected!")
        else:
            for issue in filtered_tech_issues:
                sev_icon = "🔴" if issue.severity == "CRITICAL" else ("🟡" if issue.severity == "WARNING" else "🔵")
                with st.expander(f"{sev_icon} [{issue.severity}] {issue.issue_type} — {issue.url}"):
                    st.write(f"**Description:** {issue.description}")
                    if issue.html_snippet:
                        st.code(issue.html_snippet, language="html")
                    if issue.css_selector:
                        st.code(f"CSS Selector: {issue.css_selector}")
                    if issue.xpath:
                        st.code(f"XPath: {issue.xpath}")
                    st.info(f"**Recommendation:** {issue.recommendation}")

        # --- Security & Mixed Content (from Advanced Audit) ---
        if report.advanced_audit:
            st.markdown("---")
            st.subheader("Security & Mixed Content Summary")

            adv = report.advanced_audit
            sec_col1, sec_col2 = st.columns(2)
            with sec_col1:
                st.metric("Security Header Issues", adv.total_security_issues)
            with sec_col2:
                st.metric("Mixed Content Resources", adv.total_mixed_content)

            # Show per-page security header issues
            if adv.total_security_issues > 0:
                with st.expander("View Security Header Details"):
                    for page_adv in adv.pages:
                        missing_sec = [h for h in page_adv.security_headers if not h.present and h.severity in ["CRITICAL", "WARNING"]]
                        if missing_sec:
                            st.write(f"**{page_adv.url}**")
                            for h in missing_sec:
                                st.warning(f"**{h.severity}:** {h.header} — {h.description}")
                                st.caption(f"Fix: {h.recommendation}")

            # Show mixed content details
            if adv.total_mixed_content > 0:
                with st.expander("View Mixed Content Details"):
                    all_mixed = []
                    for page_adv in adv.pages:
                        all_mixed.extend(page_adv.mixed_content)
                    for m in all_mixed[:20]:
                        st.write(f"**Page:** {m.page_url}")
                        st.write(f"  Resource: {m.resource_url} ({m.resource_type})")

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
        st.subheader("Structured Data (Schema.org)")

        sd_tab1, sd_tab2, sd_tab3, sd_tab4 = st.tabs(["Validations", "AI Generate", "Schema Validator", "llms.txt"])

        # === Tab 1: Existing Schema Validations ===
        with sd_tab1:
            st.subheader("Detected Schema on Site")
            all_schemas = []
            schema_errors = []
            schema_warnings = []
            for p in report.pages:
                for block in p.metadata.json_ld:
                    try:
                        import json as _json
                        data = _json.loads(block.data) if block.data else {}
                        schema_type = data.get("@type", "Unknown")
                        all_schemas.append({"Page": p.url, "Type": schema_type, "Valid": block.valid, "Error": block.error or ""})
                        if not block.valid:
                            schema_errors.append({"url": p.url, "error": block.error, "html": block.html_snippet})
                    except Exception:
                        schema_errors.append({"url": p.url, "error": "JSON parse error", "html": block.html_snippet})

            # Summary metrics
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric("Schema Blocks Found", len(all_schemas))
            with sc2:
                valid_count = sum(1 for s in all_schemas if s["Valid"])
                st.metric("Valid", valid_count)
            with sc3:
                st.metric("Errors", len(schema_errors))
            with sc4:
                types_found = set(s["Type"] for s in all_schemas)
                st.metric("Schema Types", len(types_found))

            if all_schemas:
                st.dataframe(pd.DataFrame(all_schemas), use_container_width=True, hide_index=True)

            if schema_errors:
                st.markdown("---")
                st.subheader("Schema Errors")
                for err in schema_errors:
                    with st.expander(f"❌ {err['url']}"):
                        st.write(f"**Error:** {err['error']}")
                        if err['html']:
                            st.code(err['html'], language="json")

            if not all_schemas:
                st.info("No structured data (JSON-LD) found on crawled pages. Use the AI Generate tab to create schemas.")

        # === Tab 2: AI-Powered Schema Generation ===
        with sd_tab2:
            st.subheader("AI Schema Generator")
            st.caption("AI generates schema from your crawled site content. Validates against Google Rich Results.")

            gen_type = st.selectbox(
                "Schema Type:",
                options=["Auto (AI picks best)", "BreadcrumbList", "FAQPage", "Organization", "Article", "WebPage", "Product", "LocalBusiness", "WebSite"],
                key="ai_gen_type"
            )

            # Page selector
            page_urls = [p.url for p in report.pages]
            selected_page_url = st.selectbox("Select page to generate schema for:", options=page_urls, key="ai_schema_page")
            selected_page = next((p for p in report.pages if p.url == selected_page_url), None)

            if selected_page:
                page_content = " ".join(h.text for h in selected_page.metadata.headings)
                page_content += " " + (selected_page.metadata.meta_description or "")

                # Auto-generate breadcrumbs
                st.markdown("---")
                auto_bc, auto_faq = st.columns(2)
                with auto_bc:
                    st.markdown("#### Auto Breadcrumbs")
                    st.caption("AI generates breadcrumbs from page URL and navigation")
                    if st.button("Generate Breadcrumbs", type="primary", key="gen_ai_bc"):
                        nav_links = [l.url for l in selected_page.links if l.is_internal][:15]
                        with st.spinner("AI generating breadcrumbs..."):
                            bc_schema = generate_ai_breadcrumbs(
                                user_api_key, selected_page_url,
                                selected_page.metadata.title or "Page",
                                report.start_url.split("//")[-1].split("/")[0],
                                nav_links, model=selected_model
                            )
                            st.session_state.ai_bc_schema = bc_schema
                    if "ai_bc_schema" in st.session_state:
                        st.code(st.session_state.ai_bc_schema, language="json")
                        st.download_button("Download", st.session_state.ai_bc_schema, "breadcrumbs.json", "application/json", key="dl_bc")
                        # Validate
                        val = validate_schema_for_google(st.session_state.ai_bc_schema)
                        if val["is_valid"]:
                            st.success(f"✅ Valid — Rich Result Type: {', '.join(val['rich_result_types']) or 'N/A'}")
                        else:
                            for e in val["errors"]:
                                st.error(e)

                with auto_faq:
                    st.markdown("#### Auto FAQs")
                    st.caption("AI generates FAQs from page content")
                    if st.button("Generate FAQs", type="primary", key="gen_ai_faq"):
                        with st.spinner("AI generating FAQs..."):
                            faq_schema = generate_ai_faqs(
                                user_api_key, selected_page_url,
                                selected_page.metadata.title or "Page",
                                page_content, model=selected_model
                            )
                            st.session_state.ai_faq_schema = faq_schema
                    if "ai_faq_schema" in st.session_state:
                        st.code(st.session_state.ai_faq_schema, language="json")
                        st.download_button("Download", st.session_state.ai_faq_schema, "faq.json", "application/json", key="dl_faq")
                        val = validate_schema_for_google(st.session_state.ai_faq_schema)
                        if val["is_valid"]:
                            st.success(f"✅ Valid — Rich Result Type: {', '.join(val['rich_result_types']) or 'N/A'}")
                        else:
                            for e in val["errors"]:
                                st.error(e)

                st.markdown("---")

                # Generate any schema type
                if gen_type != "Auto (AI picks best)":
                    if st.button(f"Generate {gen_type} Schema", type="primary", key="gen_ai_any"):
                        with st.spinner(f"AI generating {gen_type} schema..."):
                            schema = generate_ai_schema_for_page(
                                user_api_key, selected_page_url,
                                selected_page.metadata.title or "Page",
                                selected_page.metadata.meta_description or "",
                                report.start_url.split("//")[-1].split("/")[0],
                                page_type=gen_type, model=selected_model
                            )
                            st.session_state.ai_any_schema = schema
                    if "ai_any_schema" in st.session_state:
                        st.code(st.session_state.ai_any_schema, language="json")
                        st.download_button("Download", st.session_state.ai_any_schema, f"{gen_type.lower()}-schema.json", "application/json", key="dl_any")
                        val = validate_schema_for_google(st.session_state.ai_any_schema)
                        if val["is_valid"]:
                            st.success(f"✅ Valid — Rich Result Type: {', '.join(val['rich_result_types']) or 'N/A'}")
                        else:
                            for e in val["errors"]:
                                st.error(e)
                        if val["warnings"]:
                            for w in val["warnings"]:
                                st.warning(w)

        # === Tab 3: Schema Validator ===
        with sd_tab3:
            st.subheader("Schema.org & Google Rich Results Validator")
            st.caption("Paste any JSON-LD to validate against schema.org and Google Rich Results requirements.")

            validator_input = st.text_area(
                "Paste JSON-LD schema:",
                height=200,
                placeholder='{"@context": "https://schema.org", "@type": "FAQPage", ...}',
                key="validator_input"
            )

            if st.button("Validate Schema", type="primary", key="validate_btn") and validator_input:
                val = validate_schema_for_google(validator_input)
                v1, v2 = st.columns(2)
                with v1:
                    if val["is_valid"]:
                        st.success("✅ Valid JSON-LD")
                    else:
                        st.error("❌ Invalid JSON-LD")
                        for e in val["errors"]:
                            st.write(f"- {e}")
                with v2:
                    if val["rich_result_types"]:
                        st.info(f"Google Rich Result Type: {', '.join(val['rich_result_types'])}")
                    if val["missing_required"]:
                        st.warning(f"Missing recommended: {', '.join(val['missing_required'])}")
                    if val["warnings"]:
                        for w in val["warnings"]:
                            st.warning(w)

                # Google Rich Results link
                st.markdown("---")
                st.markdown("**Test in Google Rich Results Test:** [search.google.com/test/rich-results](https://search.google.com/test/rich-results)")
                st.markdown("**Schema.org Validator:** [validator.schema.org](https://validator.schema.org/)")

        # === Tab 4: llms.txt ===
        with sd_tab4:
            st.markdown("#### llms.txt Generator")
            st.caption("Generate files that help AI language models understand your website. Place in your site root.")

            llm_name = st.text_input("Website Name", value=report.start_url.split("//")[-1].split("/")[0], key="llm_name")
            llm_url = st.text_input("Website URL", value=url_input, key="llm_url")
            llm_desc = st.text_area("Website Description", value="AI-powered SEO audit and optimization platform.", key="llm_desc")
            llm_email = st.text_input("Contact Email", placeholder="info@yoursite.com", key="llm_email")
            llm_features_text = st.text_area("Key Features (one per line)", value="AI-powered SEO analysis\nWebsite crawling and auditing\nKeyword research\nStructured data generation", key="llm_features")

            llm_faqs = []
            for i in range(3):
                fc1, fc2 = st.columns(2)
                with fc1:
                    q = st.text_input(f"FAQ {i+1}", key=f"llm_fq_{i}")
                with fc2:
                    a = st.text_input(f"Answer {i+1}", key=f"llm_fa_{i}")
                if q and a:
                    llm_faqs.append({"question": q, "answer": a})

            if st.button("Generate llms.txt", key="gen_llms_new"):
                features = [f.strip() for f in llm_features_text.split("\n") if f.strip()]
                llms_content = generate_llms_txt(
                    site_name=llm_name, site_url=llm_url, site_description=llm_desc,
                    pages=[{"title": p.metadata.title or p.url, "url": p.url, "description": p.metadata.meta_description or ""} for p in report.pages[:20]],
                    faqs=llm_faqs if llm_faqs else None, contact_email=llm_email, features=features,
                )
                st.code(llms_content, language="text")
                st.download_button("Download llms.txt", llms_content, "llms.txt", "text/plain", key="dl_llms")
                llms_full = generate_llms_full_txt(
                    site_name=llm_name, site_url=llm_url, site_description=llm_desc,
                    pages=[{"title": p.metadata.title or p.url, "url": p.url, "description": p.metadata.meta_description or ""} for p in report.pages[:20]],
                    faqs=llm_faqs if llm_faqs else None, contact_email=llm_email, features=features,
                )
                st.download_button("Download llms-full.txt", llms_full, "llms-full.txt", "text/plain", key="dl_llms_full")

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
        st.subheader("Comprehensive Fix Guide")
        st.write("Detailed step-by-step instructions to resolve every issue found in your audit.")

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

            # CMS selector
            st.subheader("Select Your CMS Platform")
            st.caption("Get platform-specific instructions for your content management system.")
            cms_platform = st.radio(
                "Choose your CMS:",
                options=["generic", "wordpress", "shopify", "wix", "squarespace"],
                format_func=lambda x: {
                    "generic": "Generic (HTML/Code)",
                    "wordpress": "WordPress",
                    "shopify": "Shopify",
                    "wix": "Wix",
                    "squarespace": "Squarespace"
                }[x],
                horizontal=True,
                key="cms_platform"
            )

            st.markdown("---")

            # Group by issue type
            issue_types = sorted(set(i.issue_type for i in all_issues))

            # Sort by severity (CRITICAL first)
            def get_severity_priority(issue_type):
                issues = [i for i in all_issues if i.issue_type == issue_type]
                has_critical = any(i.severity == "CRITICAL" for i in issues)
                return 0 if has_critical else 1

            issue_types.sort(key=get_severity_priority)

            # Show issue count per type
            st.subheader("Issues Found")
            st.caption("Click on an issue type to see the full fix guide.")

            issue_summary = []
            for issue_type in issue_types:
                issues = [i for i in all_issues if i.issue_type == issue_type]
                has_critical = any(i.severity == "CRITICAL" for i in issues)
                issue_summary.append({
                    "Issue": issue_type,
                    "Count": len(issues),
                    "Severity": "CRITICAL" if has_critical else "WARNING"
                })

            st.dataframe(pd.DataFrame(issue_summary), use_container_width=True, hide_index=True)

            st.markdown("---")

            # Individual issue fix guides
            st.subheader("Fix Guides")

            selected_fix_type = st.selectbox(
                "Select issue type to see the fix guide:",
                options=issue_types,
                key="fix_type_select_v2"
            )

            if selected_fix_type:
                affected = [i for i in all_issues if i.issue_type == selected_fix_type]
                has_critical = any(i.severity == "CRITICAL" for i in affected)

                severity_color = "red" if has_critical else "orange"
                st.markdown(f"#### :{severity_color}[{selected_fix_type}]")
                st.info(f"Found on **{len(affected)}** page(s)")

                # Get the comprehensive guide
                guide_content = get_fix_guide_as_markdown(selected_fix_type, cms=cms_platform)
                st.markdown(guide_content)

                # Show affected URLs with details
                st.markdown("---")
                st.markdown("##### Affected URLs")

                for issue in affected:
                    with st.expander(f"[{issue.severity}] {issue.url}"):
                        st.write(f"**Description:** {issue.description}")
                        if issue.html_snippet:
                            st.markdown("**HTML Snippet:**")
                            st.code(issue.html_snippet, language="html")
                        if issue.css_selector:
                            st.caption(f"CSS Selector: `{issue.css_selector}`")
                        if issue.xpath:
                            st.caption(f"XPath: `{issue.xpath}`")
                        st.info(f"**Recommendation:** {issue.recommendation}")

                if len(affected) > 10:
                    st.caption(f"... and {len(affected) - 10} more pages with this issue")

            # Quick fix reference
            st.markdown("---")
            st.subheader("Quick Reference: Common Fixes")

            available_guides = get_all_fix_guides()
            ref_data = []
            for issue_type in ["Missing Title", "Missing Meta Description", "Missing H1",
                              "Missing Canonical", "Missing Viewport", "Missing Favicon",
                              "Missing Robots Meta", "Missing Structured Data",
                              "Missing HTTPS", "Missing Image Alt Text"]:
                if issue_type in available_guides:
                    ref_data.append({
                        "Issue": issue_type,
                        "Guide Available": "Yes"
                    })

            if ref_data:
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
                    fetch_crawler = SafeCrawler(verify_ssl=False, js_render=js_render)
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
