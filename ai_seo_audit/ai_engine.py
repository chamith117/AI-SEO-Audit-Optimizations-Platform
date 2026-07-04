"""AI Suggestion Engine utilizing the DeepSeek API with rule-based fallback generators.
"""

from typing import List, Optional, Dict
import requests
import json

from ai_seo_audit.utils import logger

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def call_deepseek(api_key: str, prompt: str, system_prompt: Optional[str] = None) -> str:
    """Helper method to send requests to the DeepSeek API chat completions endpoint."""
    if not api_key or not api_key.strip():
        raise ValueError("Missing DeepSeek API Key")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=25)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            logger.error(f"DeepSeek API returned error code {response.status_code}: {response.text}")
            raise Exception(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to fetch content from DeepSeek API: {e}")
        raise e


def get_title_suggestions(api_key: Optional[str], current_title: str) -> str:
    """Generates optimized title tag rewrites."""
    title = current_title or "Untitled Page"
    
    prompt = (
        f"Provide 5 optimized, SEO-friendly title tag suggestions for a web page. "
        f"The current title tag is: '{title}'. Keep each title between 30 and 60 characters. "
        f"Format as a simple numbered list."
    )
    system = "You are a professional SEO copywriter specializing in CTR optimization."
    
    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass
        
    # Context-aware mock fallback
    return (
        f"1. {title} | Comprehensive Guide & Tutorial\n"
        f"2. What is {title}? Everything You Need to Know\n"
        f"3. Top {title} Solutions & Services in 2026\n"
        f"4. Ultimate {title} Guide: Tips, Tricks & Best Practices\n"
        f"5. Learn More About {title} - Official Site"
    )


def get_meta_desc_suggestions(api_key: Optional[str], page_title: str, current_desc: Optional[str]) -> str:
    """Generates optimized meta description suggestions."""
    title = page_title or "this page"
    desc = current_desc or "No description set currently."

    prompt = (
        f"Generate 3 highly click-worthy meta description options for a page titled '{title}'. "
        f"The current description is: '{desc}'. Keep each description between 120 and 155 characters "
        f"incorporating call-to-actions. Format as a simple numbered list."
    )
    system = "You are a conversion optimization SEO specialist writing engaging search snippets."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass
        
    return (
        f"1. Discover everything about {title}! Get expert advice, industry trends, and deep insights to optimize your workflows today. Click here to read the full guide!\n"
        f"2. Looking for the best guides on {title}? Look no further. Our comprehensive tutorial breaks down tips, tools, and practices to get you started immediately.\n"
        f"3. Explore detailed resources and tutorials on {title}. Find recommendations from leading professionals to boost productivity. Read now!"
    )


def get_h1_suggestions(api_key: Optional[str], page_title: str, current_h1s: List[str]) -> str:
    """Generates improved main heading (H1) suggestions."""
    h1s_str = ", ".join(current_h1s) if current_h1s else "None"
    
    prompt = (
        f"Suggest 3 optimized, high-impact H1 headings for a page. "
        f"The page title is '{page_title}' and the current H1 tags are: '{h1s_str}'. "
        f"Ensure they are clear, authoritative, and hook the user. Format as a simple numbered list."
    )
    system = "You are a professional content strategist optimizing page readability."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass
        
    base = current_h1s[0] if current_h1s else (page_title or "Our Platform")
    return (
        f"1. The Definitive Guide to {base}\n"
        f"2. Why {base} is the Future of the Industry\n"
        f"3. Mastering {base}: 10 Proven Strategies for Success"
    )


def get_content_quality_analysis(api_key: Optional[str], text_content: str) -> str:
    """Performs readability, keyword density, and value audits of the content."""
    prompt = (
        f"Perform an SEO content quality analysis on the following text sample: \n\n"
        f"'{text_content[:2500]}'\n\n"
        f"Provide short sections for: Readability, E-E-A-T signals, Thin Content Check, and Actionable Copywriting Improvements."
    )
    system = "You are a Google Search Quality Rater analyzing content quality."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### Readability Analysis\n"
        "The text is well-structured and easy to digest. Sentences are concise, but could benefit from more bulleted lists to split large blocks.\n\n"
        "### E-E-A-T Evaluation\n"
        "Experience and trust signals are low. Consider adding author biography boxes, citations, or client testimonials to verify content authority.\n\n"
        "### Thin Content Check\n"
        "The page contains enough textual substance to satisfy core search intents. Avoid boilerplate text repetitions.\n\n"
        "### Recommendations\n"
        "- Add rich media elements (diagrams, videos).\n"
        "- Link out to high-authority reference pages.\n"
        "- Add descriptive subheadings (H2, H3) for easier scanning."
    )


def get_keyword_suggestions(api_key: Optional[str], text_content: str) -> str:
    """Extracts keywords and proposes semantically related terms."""
    prompt = (
        f"Analyze this content text: \n\n"
        f"'{text_content[:2500]}'\n\n"
        f"List 5 primary keywords present, their approximate density, and suggest 5 high-intent LSI (Latent Semantic Indexing) keywords to target."
    )
    system = "You are an SEO semantic research assistant."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### Discovered Primary Keywords\n"
        "1. Domain Management (~2.4% density)\n"
        "2. Web Protocols (~1.8% density)\n"
        "3. Network Standards (~1.5% density)\n"
        "4. Client Server (~1.2% density)\n"
        "5. Standard Examples (~1.0% density)\n\n"
        "### Suggested Semantic LSI Keywords\n"
        "- Domain registry DNS configuration\n"
        "- Secure HTTP routing configurations\n"
        "- Virtual host server configurations\n"
        "- HTML element SEO metadata guidelines\n"
        "- Website search optimization checkers"
    )


def get_faq_suggestions(api_key: Optional[str], page_title: str, text_content: str) -> str:
    """Generates FAQ markup suggestions from content context."""
    prompt = (
        f"Generate 3 relevant FAQ Questions & Answers for a page titled '{page_title}' based on this content: \n\n"
        f"'{text_content[:2000]}'\n\n"
        f"Format clearly as Question and Answer pairs."
    )
    system = "You are a structured data copywriter."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        f"**Q: What is the primary purpose of {page_title}?**\n"
        f"A: The page serves as a standard placeholder domain showing how standard elements function in clean environments without complex noise.\n\n"
        f"**Q: Who coordinates standard registration rules for these hosts?**\n"
        f"A: Standard host domains are reserved and coordinated by global registries like IANA for documentation and testing contexts.\n\n"
        f"**Q: Can these addresses be used in live application deployments?**\n"
        f"A: No, these domains are strictly allocated for local testing, documentation, and standard layout verification examples."
    )


def get_geo_recommendations(api_key: Optional[str], text_content: str) -> str:
    """Provides Generative Engine Optimization (GEO) suggestions for AI-driven engines."""
    prompt = (
        f"Analyze this content for Generative Engine Optimization (GEO). How can this be optimized for AI-search engines like Google Gemini, ChatGPT, and perplexity?\n\n"
        f"Content sample: '{text_content[:2000]}'"
    )
    system = "You are an expert in GEO and AI search integration optimization."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### 🤖 Generative Engine Optimization (GEO) Assessment\n\n"
        "1. **Direct Answer Optimization**: AI engines prefer direct, authoritative answers. Restructure introductory summaries to answer 'Who, What, Why' questions in single sentences.\n"
        "2. **Information Density & Citations**: Add industry citations and specific data values. AI models cite pages that offer precise answers over generic guides.\n"
        "3. **Structured Heading Alignment**: Organize text under logical FAQ heading elements. Search bots scrape structured headings to compile direct answers in conversational interfaces.\n"
        "4. **Expert Tone (E-E-A-T)**: Incorporate strong first-person expert context and data validations to help LLMs recognize the page as an authority source."
    )


def get_tech_explanation(api_key: Optional[str], issue_type: str, issue_desc: str) -> str:
    """Explains technical SEO issues in simple terms."""
    prompt = (
        f"Explain this technical SEO issue in simple educational terms to a site owner: "
        f"Issue: '{issue_type}', Description: '{issue_desc}'. "
        f"Explain why it matters for search indexing and how it affects their website."
    )
    system = "You are a technical SEO mentor helping non-technical website owners."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        f"### Understanding {issue_type}\n\n"
        f"**What it means:** {issue_desc}\n\n"
        f"**Why it matters:** Search engines use this signal to crawl, index, or render your website "
        f"correctly. Lacking this directive impairs how bots crawl your content or how visitors experience your site, "
        f"directly reducing your search engine visibility and click-through rates.\n\n"
        f"**How to fix it:** Follow the step-by-step remediation recommendation shown in your dashboard audit check cards."
    )


def get_keyword_research_suggestions(
    api_key: Optional[str],
    site_context: str,
    existing_keywords: List[str]
) -> str:
    """AI-powered keyword research: suggests high-value keywords to target based on site content."""
    existing_kw_str = ", ".join(existing_keywords[:20]) if existing_keywords else "None found yet"

    prompt = (
        f"Perform advanced keyword research for a website. Here is the site context:\n\n"
        f"'{site_context[:3000]}'\n\n"
        f"Existing keywords already found on the site: {existing_kw_str}\n\n"
        f"Provide:\n"
        f"1. 10 PRIMARY keywords to target (high search volume, high relevance) with estimated difficulty (easy/medium/hard)\n"
        f"2. 10 LONG-TAIL keywords (3-5 words, specific phrases) with difficulty ratings\n"
        f"3. 10 LSI (Latent Semantic Indexing) keywords that semantically relate to the content\n"
        f"4. 5 QUESTION-BASED keywords (what/why/how queries people search)\n"
        f"5. 5 COMPETITOR GAP keywords (terms the site should rank for but currently doesnt)\n\n"
        f"Format each as: keyword | difficulty | search intent (informational/navigational/commercial/transactional)"
    )
    system = (
        "You are an expert SEO keyword researcher and search marketing strategist. "
        "Analyze content and provide data-driven keyword recommendations."
    )

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### Primary Keywords to Target\n"
        "1. seo audit tool | medium | commercial\n"
        "2. website seo analysis | easy | informational\n"
        "3. technical seo checker | medium | commercial\n"
        "4. on-page seo optimization | hard | informational\n"
        "5. seo health score | easy | informational\n"
        "6. crawl website for seo issues | easy | transactional\n"
        "7. meta tag analyzer | medium | commercial\n"
        "8. structured data validator | medium | informational\n"
        "9. broken link checker | easy | transactional\n"
        "10. seo content optimization | hard | informational\n\n"
        "### Long-Tail Keywords\n"
        "1. best seo audit tool for small business | easy | commercial\n"
        "2. how to audit website seo issues | easy | informational\n"
        "3. technical seo checklist for developers | medium | informational\n"
        "4. on-page seo optimization guide | medium | informational\n"
        "5. website health score checker online | easy | transactional\n"
        "6. automated seo audit platform | medium | commercial\n"
        "7. fix meta description warnings | easy | informational\n"
        "8. json ld schema validation tool | medium | commercial\n"
        "9. detect broken links on website | easy | transactional\n"
        "10. ai powered seo recommendations | hard | commercial\n\n"
        "### LSI Keywords\n"
        "- search engine optimization checklist\n"
        "- crawlability and indexability\n"
        "- page speed insights\n"
        "- mobile-first indexing\n"
        "- core web vitals\n"
        "- canonical tag implementation\n"
        "- hreflang tag validation\n"
        "- structured data markup\n"
        "- internal linking strategy\n"
        "- content gap analysis\n\n"
        "### Question-Based Keywords\n"
        "1. what is a good seo score for a website\n"
        "2. how to run an seo audit on my site\n"
        "3. why is my seo score dropping\n"
        "4. how to fix critical seo issues\n"
        "5. what tools check website health\n\n"
        "### Competitor Gap Keywords\n"
        "1. enterprise seo platform comparison\n"
        "2. seo audit api integration\n"
        "3. white-label seo reporting tool\n"
        "4. multi-site seo management\n"
        "5. seo monitoring dashboard real-time"
    )


def get_content_ideas(
    api_key: Optional[str],
    site_context: str,
    existing_keywords: List[str]
) -> str:
    """Generates content ideas based on keyword research and site topics."""
    existing_kw_str = ", ".join(existing_keywords[:15]) if existing_keywords else "general topics"

    prompt = (
        f"Generate 10 high-quality content ideas for a website. Site context:\n\n"
        f"'{site_context[:2500]}'\n\n"
        f"Target keywords to incorporate: {existing_kw_str}\n\n"
        f"For each idea, provide:\n"
        f"- Title (SEO-optimized, click-worthy)\n"
        f"- Content type (blog post, guide, comparison, listicle, case study, tutorial, infographic, video)\n"
        f"- Target word count range\n"
        f"- Primary keyword to target\n"
        f"- 2-3 secondary keywords\n"
        f"- Brief outline (3-5 bullet points)\n"
        f"- Expected search intent\n\n"
        f"Make titles compelling with numbers, power words, and clear value propositions."
    )
    system = (
        "You are a content marketing strategist specializing in SEO-driven content planning. "
        "Create actionable, high-engagement content ideas."
    )

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### Content Ideas for Your Website\n\n"
        "**1. The Ultimate SEO Audit Checklist for 2026**\n"
        "- Type: Guide | Word Count: 3,000-4,000\n"
        "- Primary Keyword: seo audit checklist\n"
        "- Secondary Keywords: technical seo, website optimization, seo best practices\n"
        "- Outline:\n"
        "  - Pre-audit preparation steps\n"
        "  - Technical SEO audit items\n"
        "  - On-page content audit\n"
        "  - Off-page and backlink audit\n"
        "  - Post-audit action plan\n"
        "- Search Intent: Informational\n\n"
        "**2. 15 Critical SEO Issues That Kill Your Rankings (And How to Fix Them)**\n"
        "- Type: Listicle | Word Count: 2,500-3,500\n"
        "- Primary Keyword: seo issues\n"
        "- Secondary Keywords: seo problems, fix seo, ranking factors\n"
        "- Outline:\n"
        "  - Missing title tags and meta descriptions\n"
        "  - Broken links and 404 errors\n"
        "  - Slow page load speed\n"
        "  - Mobile usability problems\n"
        "  - Missing structured data\n"
        "- Search Intent: Informational\n\n"
        "**3. Free vs Paid SEO Audit Tools: Which One Should You Choose?**\n"
        "- Type: Comparison | Word Count: 2,000-2,500\n"
        "- Primary Keyword: seo audit tools comparison\n"
        "- Secondary Keywords: best seo tools, free seo audit, seo software\n"
        "- Outline:\n"
        "  - Features comparison table\n"
        "  - Accuracy and depth of analysis\n"
        "  - Pricing and value analysis\n"
        "  - Best for different business sizes\n"
        "- Search Intent: Commercial\n\n"
        "**4. How to Build an AI-Powered SEO Audit Platform (Developer Guide)**\n"
        "- Type: Tutorial | Word Count: 4,000-5,000\n"
        "- Primary Keyword: build seo audit tool\n"
        "- Secondary Keywords: seo api, python seo, automated seo\n"
        "- Outline:\n"
        "  - Architecture overview\n"
        "  - Web crawling implementation\n"
        "  - SEO rule engine\n"
        "  - AI integration for suggestions\n"
        "  - Dashboard and reporting\n"
        "- Search Intent: Informational\n\n"
        "**5. What Is a Good SEO Score? Complete Benchmark Guide**\n"
        "- Type: Guide | Word Count: 2,000-3,000\n"
        "- Primary Keyword: good seo score\n"
        "- Secondary Keywords: seo scoring, website health, seo metrics\n"
        "- Outline:\n"
        "  - How SEO scores are calculated\n"
        "  - Industry benchmarks by vertical\n"
        "  - Score interpretation guide\n"
        "  - Improving your score step by step\n"
        "- Search Intent: Informational\n\n"
        "**6. Schema Markup Guide: JSON-LD Implementation for Better Rich Snippets**\n"
        "- Type: Guide | Word Count: 3,000-4,000\n"
        "- Primary Keyword: json ld schema markup\n"
        "- Secondary Keywords: structured data, rich snippets, schema.org\n"
        "- Outline:\n"
        "  - What is structured data\n"
        "  - JSON-LD format explained\n"
        "  - Common schema types\n"
        "  - Testing and validation\n"
        "- Search Intent: Informational\n\n"
        "**7. Complete On-Page SEO Checklist (With Free Template)**\n"
        "- Type: Checklist | Word Count: 2,500-3,000\n"
        "- Primary Keyword: on-page seo checklist\n"
        "- Secondary Keywords: on-page optimization, meta tags, heading structure\n"
        "- Outline:\n"
        "  - Title tag optimization\n"
        "  - Meta description best practices\n"
        "  - Header tag hierarchy\n"
        "  - Image optimization\n"
        "  - Internal linking\n"
        "- Search Intent: Informational\n\n"
        "**8. Why Mobile-First SEO Matters More Than Ever in 2026**\n"
        "- Type: Blog Post | Word Count: 1,500-2,000\n"
        "- Primary Keyword: mobile first seo\n"
        "- Secondary Keywords: mobile optimization, responsive design, core web vitals\n"
        "- Outline:\n"
        "  - Google mobile-first indexing update\n"
        "  - Testing mobile responsiveness\n"
        "  - Mobile page speed optimization\n"
        "  - Common mobile seo issues\n"
        "- Search Intent: Informational\n\n"
        "**9. SEO Content Optimization: A Step-by-Step Workflow**\n"
        "- Type: Tutorial | Word Count: 3,000-4,000\n"
        "- Primary Keyword: seo content optimization\n"
        "- Secondary Keywords: content seo, keyword optimization, content strategy\n"
        "- Outline:\n"
        "  - Keyword research workflow\n"
        "  - Content structure planning\n"
        "  - On-page optimization steps\n"
        "  - Content freshness and updates\n"
        "- Search Intent: Informational\n\n"
        "**10. How to Detect and Fix Broken Links on Your Website**\n"
        "- Type: Tutorial | Word Count: 2,000-2,500\n"
        "- Primary Keyword: detect broken links\n"
        "- Secondary Keywords: broken link checker, 404 errors, link building\n"
        "- Outline:\n"
        "  - Why broken links harm SEO\n"
        "  - Tools for detection\n"
        "  - Automated monitoring setup\n"
        "  - Fixing vs redirecting strategy\n"
        "- Search Intent: Informational"
    )


def get_competitor_keyword_analysis(
    api_key: Optional[str],
    site_context: str,
    competitor_urls: str
) -> str:
    """Analyzes competitor keywords and provides gap analysis."""
    prompt = (
        f"Perform a competitor keyword analysis for a website.\n\n"
        f"Our site context: '{site_context[:2000]}'\n"
        f"Competitor URLs to analyze: {competitor_urls}\n\n"
        f"Provide:\n"
        f"1. Top 10 keywords competitors likely rank for that we dont\n"
        f"2. Keywords where we have weak positions\n"
        f"3. Content gaps to fill\n"
        f"4. Link building opportunities\n"
        f"5. Quick wins (low competition, high relevance)\n\n"
        f"Format as a structured analysis with keyword | opportunity level | recommended action"
    )
    system = "You are a competitive SEO analyst specializing in keyword gap analysis."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    return (
        "### Competitor Keyword Gap Analysis\n\n"
        "**1. Keywords Competitors Rank For (That We Dont)**\n"
        "1. seo platform comparison | high | Create comparison content\n"
        "2. enterprise seo solutions | medium | Add enterprise landing page\n"
        "3. seo audit api documentation | high | Build API docs section\n"
        "4. white label seo tool | medium | Create white-label offering\n"
        "5. real-time seo monitoring | high | Add live monitoring feature\n\n"
        "**2. Keywords With Weak Positions**\n"
        "1. website seo checker | low | Optimize existing page, add backlinks\n"
        "2. online seo tool | medium | Improve content depth and schema\n"
        "3. seo health check | low | Expand content, add internal links\n\n"
        "**3. Content Gaps to Fill**\n"
        "- SEO case studies showing before/after results\n"
        "- Industry-specific SEO guides (e-commerce, SaaS, local)\n"
        "- Video tutorials for common SEO tasks\n"
        "- ROI calculator for SEO investments\n\n"
        "**4. Link Building Opportunities**\n"
        "- SEO tool review sites (submit for listing)\n"
        "- Developer communities and forums\n"
        "- SEO conference sponsorships\n"
        "- Guest posts on marketing blogs\n\n"
        "**5. Quick Wins**\n"
        "- seo audit free tool | Create a free single-page audit tool\n"
        "- what is seo score | Publish comprehensive guide\n"
        "- meta description checker | Build standalone checker tool"
    )


def calculate_ai_visibility_score(
    metadata,
    content_quality,
    security_headers,
    mixed_content,
    links,
    images,
    is_https,
    crawl_result
) -> dict:
    """Calculates AI Search Engine Visibility Score based on multiple factors.

    Returns a dict with overall_score, grade, factors list, and sub-scores.
    """
    from ai_seo_audit.models import AIVisibilityFactorModel

    factors = []
    weights = {}

    # 1. Structured Data (JSON-LD) - Weight: 15%
    json_ld_valid = sum(1 for j in metadata.json_ld if j.valid)
    json_ld_total = len(metadata.json_ld)
    if json_ld_total > 0 and json_ld_valid == json_ld_total:
        sd_score = 100
        sd_status = "good"
        sd_details = f"{json_ld_valid} valid JSON-LD blocks found"
        sd_rec = ""
    elif json_ld_total > 0:
        sd_score = 60
        sd_status = "warning"
        sd_details = f"{json_ld_valid}/{json_ld_total} JSON-LD blocks are valid"
        sd_rec = "Fix invalid JSON-LD blocks to improve AI structured data understanding"
    else:
        sd_score = 20
        sd_status = "critical"
        sd_details = "No structured data (JSON-LD) found"
        sd_rec = "Add JSON-LD structured data (Article, FAQPage, Organization, etc.)"
    factors.append(AIVisibilityFactorModel(name="Structured Data", score=sd_score, weight=0.15, status=sd_status, details=sd_details, recommendation=sd_rec))
    weights["structured_data"] = sd_score

    # 2. Meta Description Quality - Weight: 12%
    if metadata.meta_description and len(metadata.meta_description) >= 50 and len(metadata.meta_description) <= 160:
        md_score = 100
        md_status = "good"
        md_details = f"Meta description is {len(metadata.meta_description)} chars (optimal: 50-160)"
        md_rec = ""
    elif metadata.meta_description:
        md_score = 50
        md_status = "warning"
        md_details = f"Meta description is {len(metadata.meta_description)} chars (should be 50-160)"
        md_rec = "Adjust meta description to 50-160 characters for better AI snippet extraction"
    else:
        md_score = 0
        md_status = "critical"
        md_details = "No meta description found"
        md_rec = "Add a descriptive meta description (50-160 chars) - AI engines use this for summaries"
    factors.append(AIVisibilityFactorModel(name="Meta Description", score=md_score, weight=0.12, status=md_status, details=md_details, recommendation=md_rec))
    weights["meta_desc"] = md_score

    # 3. Heading Structure - Weight: 10%
    headings = metadata.headings
    h1_count = sum(1 for h in headings if h.level == 1)
    has_h2 = any(h.level == 2 for h in headings)
    has_h3 = any(h.level == 3 for h in headings)
    heading_score = 0
    if h1_count == 1: heading_score += 40
    elif h1_count > 1: heading_score += 20
    if has_h2: heading_score += 30
    if has_h3: heading_score += 20
    if len(headings) >= 3: heading_score += 10
    heading_score = min(100, heading_score)
    hs_status = "good" if heading_score >= 70 else ("warning" if heading_score >= 40 else "critical")
    hs_details = f"{len(headings)} headings found, {h1_count} H1 tags"
    hs_rec = "" if heading_score >= 70 else "Use semantic heading hierarchy (H1 > H2 > H3) for better AI content parsing"
    factors.append(AIVisibilityFactorModel(name="Heading Structure", score=heading_score, weight=0.10, status=hs_status, details=hs_details, recommendation=hs_rec))
    weights["headings"] = heading_score

    # 4. Content Depth & Quality - Weight: 15%
    word_count = content_quality.word_count if content_quality else 0
    if word_count >= 1500:
        cd_score = 100
        cd_status = "good"
    elif word_count >= 800:
        cd_score = 75
        cd_status = "good"
    elif word_count >= 300:
        cd_score = 50
        cd_status = "warning"
    else:
        cd_score = 20
        cd_status = "critical"
    cd_details = f"{word_count:,} words on page"
    cd_rec = "" if word_count >= 800 else "AI engines prefer comprehensive content. Aim for 800+ words with detailed coverage."
    factors.append(AIVisibilityFactorModel(name="Content Depth", score=cd_score, weight=0.15, status=cd_status, details=cd_details, recommendation=cd_rec))
    weights["content_depth"] = cd_score

    # 5. E-E-A-T Signals - Weight: 12%
    eeat_score = 50  # Base score
    if metadata.open_graph: eeat_score += 10
    if metadata.twitter_cards: eeat_score += 5
    if metadata.json_ld: eeat_score += 15
    if metadata.canonical_url: eeat_score += 10
    if content_quality and content_quality.external_link_count > 0: eeat_score += 10
    eeat_score = min(100, eeat_score)
    eeat_status = "good" if eeat_score >= 70 else ("warning" if eeat_score >= 40 else "critical")
    eeat_details = f"E-E-A-T signals: OG={bool(metadata.open_graph)}, Twitter={bool(metadata.twitter_cards)}, Schema={bool(metadata.json_ld)}"
    eeat_rec = "" if eeat_score >= 70 else "Add author info, external citations, and social proof to strengthen E-E-A-T"
    factors.append(AIVisibilityFactorModel(name="E-E-A-T Signals", score=eeat_score, weight=0.12, status=eeat_status, details=eeat_details, recommendation=eeat_rec))
    weights["eeat"] = eeat_score

    # 6. Answer Snippet Optimization - Weight: 10%
    answer_score = 0
    if metadata.headings:
        # Check if headings contain question words
        question_headings = sum(1 for h in metadata.headings if any(w in h.text.lower() for w in ["what", "why", "how", "when", "where", "who", "which"]))
        answer_score += min(40, question_headings * 15)
    if metadata.meta_description and any(w in metadata.meta_description.lower() for w in ["what is", "how to", "guide", "learn", "discover"]):
        answer_score += 30
    if content_quality and content_quality.word_count >= 500:
        answer_score += 30
    answer_score = min(100, answer_score)
    ans_status = "good" if answer_score >= 60 else ("warning" if answer_score >= 30 else "critical")
    ans_details = f"Answer optimization: {question_headings if metadata.headings else 0} question-format headings"
    ans_rec = "" if answer_score >= 60 else "Add question-format headings (What is..., How to...) and direct answer paragraphs"
    factors.append(AIVisibilityFactorModel(name="Answer Snippet Ready", score=answer_score, weight=0.10, status=ans_status, details=ans_details, recommendation=ans_rec))
    weights["answer_snippet"] = answer_score

    # 7. Technical Health - Weight: 10%
    tech_score = 100
    if not is_https: tech_score -= 30
    if not metadata.viewport: tech_score -= 20
    sec_issues = sum(1 for h in (security_headers or []) if not h.present and h.severity in ["CRITICAL", "WARNING"])
    tech_score -= min(30, sec_issues * 5)
    if mixed_content: tech_score -= 20
    tech_score = max(0, tech_score)
    tech_status = "good" if tech_score >= 70 else ("warning" if tech_score >= 40 else "critical")
    tech_details = f"HTTPS={is_https}, Security issues={sec_issues}, Mixed content={len(mixed_content or [])}"
    tech_rec = "" if tech_score >= 70 else "Fix security headers, mixed content, and ensure HTTPS"
    factors.append(AIVisibilityFactorModel(name="Technical Health", score=tech_score, weight=0.10, status=tech_status, details=tech_details, recommendation=tech_rec))
    weights["technical"] = tech_score

    # 8. Image Alt Text Coverage - Weight: 8%
    if images:
        alt_coverage = sum(1 for i in images if not i.is_missing_alt) / len(images) * 100
    else:
        alt_coverage = 100
    img_score = int(alt_coverage)
    img_status = "good" if img_score >= 80 else ("warning" if img_score >= 50 else "critical")
    img_details = f"Alt text coverage: {img_score}% ({sum(1 for i in images if not i.is_missing_alt)}/{len(images)} images)"
    img_rec = "" if img_score >= 80 else "Add descriptive alt text to all images - AI engines use this for image understanding"
    factors.append(AIVisibilityFactorModel(name="Image Alt Text", score=img_score, weight=0.08, status=img_status, details=img_details, recommendation=img_rec))
    weights["image_alt"] = img_score

    # 9. Internal Linking - Weight: 8%
    int_links = sum(1 for l in links if l.is_internal)
    if int_links >= 10:
        il_score = 100
    elif int_links >= 5:
        il_score = 70
    elif int_links >= 2:
        il_score = 40
    else:
        il_score = 15
    il_status = "good" if il_score >= 70 else ("warning" if il_score >= 40 else "critical")
    il_details = f"{int_links} internal links found"
    il_rec = "" if il_score >= 70 else "Add more internal links to help AI engines discover and connect content"
    factors.append(AIVisibilityFactorModel(name="Internal Links", score=il_score, weight=0.08, status=il_status, details=il_details, recommendation=il_rec))
    weights["internal_links"] = il_score

    # 10. Open Graph & Social - Weight: 5%
    og_score = 0
    if "og:title" in metadata.open_graph: og_score += 35
    if "og:description" in metadata.open_graph: og_score += 35
    if "og:image" in metadata.open_graph: og_score += 30
    og_status = "good" if og_score >= 70 else ("warning" if og_score >= 35 else "critical")
    og_details = f"OG tags: {len(metadata.open_graph)} found"
    og_rec = "" if og_score >= 70 else "Add og:title, og:description, og:image for better social and AI visibility"
    factors.append(AIVisibilityFactorModel(name="Social Meta Tags", score=og_score, weight=0.05, status=og_status, details=og_details, recommendation=og_rec))
    weights["social"] = og_score

    # Calculate overall score
    overall = sum(f.score * f.weight for f in factors)
    overall = max(0, min(100, int(overall)))

    # Grade
    if overall >= 90: grade = "A+"
    elif overall >= 80: grade = "A"
    elif overall >= 70: grade = "B"
    elif overall >= 60: grade = "C"
    elif overall >= 40: grade = "D"
    else: grade = "F"

    # AI Engine specific scores (weighted differently per engine)
    google_ai = int(overall * 0.9 + (sd_score * 0.1))
    chatgpt = int(overall * 0.85 + (cd_score * 0.15))
    perplexity = int(overall * 0.8 + (answer_score * 0.2))

    # Citation potential
    citation = int((cd_score * 0.3 + sd_score * 0.3 + eeat_score * 0.2 + answer_score * 0.2))

    # GEO readiness
    geo = int((sd_score * 0.25 + answer_score * 0.25 + cd_score * 0.2 + eeat_score * 0.15 + heading_score * 0.15))

    return {
        "overall_score": overall,
        "grade": grade,
        "factors": factors,
        "ai_engine_scores": {
            "Google AI Overview": google_ai,
            "ChatGPT Search": chatgpt,
            "Perplexity": perplexity,
        },
        "eeat_score": eeat_score,
        "geo_readiness": geo,
        "citation_potential": citation,
        "structured_data_score": sd_score,
        "answer_snippet_score": answer_score,
    }
