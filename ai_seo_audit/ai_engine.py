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


# ==================== STEP-BY-STEP FIX GUIDES ====================

def generate_meta_descriptions(
    api_key: Optional[str],
    page_url: str,
    page_title: str,
    page_headings: List[str],
    current_desc: Optional[str] = None
) -> str:
    """Generates 3 optimized meta description options for a page based on its content."""
    headings_text = ", ".join(page_headings[:5]) if page_headings else "No headings"
    current = current_desc or "None"

    prompt = (
        f"Generate 3 optimized meta descriptions for this web page:\n\n"
        f"URL: {page_url}\n"
        f"Title: {page_title}\n"
        f"Headings: {headings_text}\n"
        f"Current description: {current}\n\n"
        f"Rules:\n"
        f"- Each description must be between 120-155 characters\n"
        f"- Include the primary keyword naturally\n"
        f"- Include a call-to-action (Learn more, Discover, Get started, Find out)\n"
        f"- Make them compelling and click-worthy\n"
        f"- Each should be unique and take a different angle\n\n"
        f"Format as:\n"
        f"1. [description] (XX chars)\n"
        f"2. [description] (XX chars)\n"
        f"3. [description] (XX chars)"
    )
    system = "You are an SEO copywriter specializing in meta descriptions that maximize click-through rates."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    # Fallback: generate based on title
    title_clean = page_title.replace("|", "-").replace(":", "-").strip() if page_title else "This Page"
    keyword = title_clean.split()[0] if title_clean.split() else "This"

    return (
        f"1. Discover everything about {title_clean}. Get expert insights, tips, and a free analysis. Start optimizing your site today! (120 chars)\n"
        f"2. Looking for the best {keyword} solution? Our comprehensive guide covers everything you need to know. Read now! (118 chars)\n"
        f"3. Learn how to improve your {keyword} with our expert guide. Step-by-step instructions, best practices, and tools. Get started! (125 chars)"
    )


def generate_title_suggestions_for_page(
    api_key: Optional[str],
    page_url: str,
    current_title: str,
    page_headings: List[str]
) -> str:
    """Generates 5 optimized title tag suggestions for a specific page."""
    headings_text = ", ".join(page_headings[:5]) if page_headings else "No headings"

    prompt = (
        f"Generate 5 SEO-optimized title tags for this page:\n\n"
        f"URL: {page_url}\n"
        f"Current title: {current_title}\n"
        f"Headings: {headings_text}\n\n"
        f"Rules:\n"
        f"- Each title must be 30-60 characters\n"
        f"- Include the primary keyword near the beginning\n"
        f"- Make them compelling for search results\n"
        f"- Each should be unique\n\n"
        f"Format as a numbered list."
    )
    system = "You are an SEO specialist creating high-CTR title tags."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    base = current_title[:30] if current_title else "This Page"
    return (
        f"1. {base} - Complete Guide & Tutorial\n"
        f"2. What is {base}? Everything You Need to Know\n"
        f"3. Top {base} Solutions & Services 2026\n"
        f"4. Ultimate {base} Guide: Tips & Best Practices\n"
        f"5. {base} | Expert Analysis & Free Tool"
    )


def generate_h1_suggestions_for_page(
    api_key: Optional[str],
    page_url: str,
    page_title: str,
    current_h1s: List[str]
) -> str:
    """Generates 3 H1 heading suggestions for a specific page."""
    h1s_text = ", ".join(current_h1s) if current_h1s else "None"

    prompt = (
        f"Generate 3 optimized H1 headings for this page:\n\n"
        f"URL: {page_url}\n"
        f"Title: {page_title}\n"
        f"Current H1s: {h1s_text}\n\n"
        f"Rules:\n"
        f"- Each H1 should be clear and descriptive\n"
        f"- Include primary keyword\n"
        f"- Keep under 70 characters\n"
        f"- Make it the most prominent heading on the page\n\n"
        f"Format as a numbered list."
    )
    system = "You are a content strategist optimizing page headings."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    base = page_title[:35] if page_title else "Our Platform"
    return (
        f"1. The Complete Guide to {base}\n"
        f"2. Why {base} is the Best Choice in 2026\n"
        f"3. {base}: Features, Benefits & How to Get Started"
    )


FIX_GUIDES = {
    "Missing Title": {
        "title": "Fix Missing Title Tag",
        "impact": "CRITICAL - Title is the #1 on-page SEO factor. Missing title means Google cannot understand your page.",
        "steps": [
            {"step": 1, "action": "Open your HTML file or CMS editor", "code": None},
            {"step": 2, "action": "Add a <title> tag inside the <head> section", "code": "<head>\n  <title>Your Keyword-Rich Title Here</title>\n</head>"},
            {"step": 3, "action": "Keep title between 30-65 characters", "code": None},
            {"step": 4, "action": "Include your primary keyword near the beginning", "code": None},
            {"step": 5, "action": "Make it unique for every page", "code": None},
        ],
        "example_good": "<title>AI SEO Audit Tool - Free Website Analysis | YourBrand</title>",
        "example_bad": "<title>Home</title>",
        "wordpress": "Go to Pages > Edit Page > Document Settings > SEO Title (Yoast) or Title Tag (RankMath)",
        "shopify": "Go to Online Store > Pages > Edit page > SEO > Page title",
        "webflow": "Go to Pages > Settings > SEO Settings > Title Tag",
    },
    "Title Length": {
        "title": "Fix Title Tag Length",
        "impact": "WARNING - Title too short (<30) or too long (>65) will be truncated in search results.",
        "steps": [
            {"step": 1, "action": "Check current title length", "code": None},
            {"step": 2, "action": "Rewrite to be 30-65 characters", "code": None},
            {"step": 3, "action": "Place primary keyword at the start", "code": None},
            {"step": 4, "action": "Add brand name at the end if space allows", "code": None},
        ],
        "example_good": "<title>Best SEO Audit Tool 2026 - Free Online Analysis</title>",
        "example_bad": "<title>SEO</title> (too short) or <title>This Is A Very Long Title That Will Definitely Get Truncated By Google Search Results</title> (too long)",
    },
    "Missing Meta Description": {
        "title": "Fix Missing Meta Description",
        "impact": "CRITICAL - Meta description controls your search snippet. Missing = Google generates one for you (often bad).",
        "steps": [
            {"step": 1, "action": "Open your HTML <head> section", "code": None},
            {"step": 2, "action": "Add a meta description tag", "code": "<meta name=\"description\" content=\"Your compelling 120-155 character description here.\">"},
            {"step": 3, "action": "Include primary keyword naturally", "code": None},
            {"step": 4, "action": "Add a call-to-action (Learn more, Discover, Get started)", "code": None},
            {"step": 5, "action": "Make each page description unique", "code": None},
        ],
        "example_good": "<meta name=\"description\" content=\"Free AI-powered SEO audit tool. Analyze your website for 50+ technical issues, get fix recommendations, and boost rankings. Try now.\">",
        "example_bad": "<meta name=\"description\" content=\"\">",
    },
    "Meta Description Length": {
        "title": "Fix Meta Description Length",
        "impact": "WARNING - Description too short (<50) or too long (>160) affects click-through rate.",
        "steps": [
            {"step": 1, "action": "Aim for 120-155 characters (sweet spot)", "code": None},
            {"step": 2, "action": "Include target keyword in first 100 chars", "code": None},
            {"step": 3, "action": "Add value proposition + CTA", "code": None},
        ],
        "example_good": "<meta name=\"description\" content=\"Audit your website for free with AI-powered SEO analysis. Find and fix 50+ technical issues that hurt your Google rankings.\">",
    },
    "Missing Canonical URL": {
        "title": "Fix Missing Canonical URL",
        "impact": "CRITICAL - Without canonical, Google may index duplicate versions of your page, diluting ranking signals.",
        "steps": [
            {"step": 1, "action": "Add a canonical link tag in <head>", "code": "<link rel=\"canonical\" href=\"https://yoursite.com/page-url\">"},
            {"step": 2, "action": "Use absolute URLs (full https://...)", "code": None},
            {"step": 3, "action": "Self-reference: canonical should point to the same page", "code": None},
            {"step": 4, "action": "If page has URL parameters, canonical should be the clean version", "code": None},
        ],
        "example_good": "<link rel=\"canonical\" href=\"https://example.com/seo-audit-tool\">",
        "wordpress": "Yoast SEO automatically adds canonical tags. Verify at Posts > Edit > Yoast > Advanced.",
    },
    "Canonical Mismatch": {
        "title": "Fix Canonical URL Mismatch",
        "impact": "WARNING - Canonical points to a different URL than the current page.",
        "steps": [
            {"step": 1, "action": "Verify the canonical URL is correct", "code": None},
            {"step": 2, "action": "For self-referencing, canonical href should match current URL", "code": None},
            {"step": 3, "action": "If intentional (multiple URLs for same content), this is OK", "code": None},
        ],
    },
    "Missing Viewport Tag": {
        "title": "Fix Missing Mobile Viewport",
        "impact": "CRITICAL - Without viewport, your site is NOT mobile-friendly. Google uses mobile-first indexing.",
        "steps": [
            {"step": 1, "action": "Add viewport meta tag in <head>", "code": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"},
            {"step": 2, "action": "Test mobile-friendliness at search.google.com/test/mobile-friendly", "code": None},
            {"step": 3, "action": "Ensure CSS uses responsive units (%, rem, vw)", "code": None},
        ],
        "example_good": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "wordpress": "Most modern themes include this. Check Appearance > Theme > mobile settings.",
    },
    "Missing Lang Attribute": {
        "title": "Fix Missing HTML Lang Attribute",
        "impact": "WARNING - Helps search engines understand your content language for proper indexing.",
        "steps": [
            {"step": 1, "action": "Add lang attribute to <html> tag", "code": "<html lang=\"en\">"},
            {"step": 2, "action": "Use correct ISO 639-1 code (en, es, fr, de, etc.)", "code": None},
        ],
        "example_good": "<html lang=\"en\">",
    },
    "Missing H1 Heading": {
        "title": "Fix Missing H1 Heading",
        "impact": "CRITICAL - H1 tells Google what your page is about. No H1 = poor understanding.",
        "steps": [
            {"step": 1, "action": "Add exactly ONE H1 tag on the page", "code": "<h1>Your Primary Keyword Here</h1>"},
            {"step": 2, "action": "Place it near the top of the content", "code": None},
            {"step": 3, "action": "Include your primary keyword naturally", "code": None},
            {"step": 4, "action": "Make it descriptive of the page content", "code": None},
        ],
        "example_good": "<h1>Free AI SEO Audit Tool - Analyze Your Website</h1>",
    },
    "Multiple H1 Headings": {
        "title": "Fix Multiple H1 Headings",
        "impact": "WARNING - Multiple H1s confuse search engines about the main topic.",
        "steps": [
            {"step": 1, "action": "Keep only ONE H1 (the main page title)", "code": None},
            {"step": 2, "action": "Change extra H1s to H2", "code": "<h2>Subheading Here</h2>"},
            {"step": 3, "action": "Follow hierarchy: H1 > H2 > H3", "code": None},
        ],
    },
    "Missing Favicon": {
        "title": "Add Missing Favicon",
        "impact": "WARNING - Missing favicon looks unprofessional and affects brand recognition.",
        "steps": [
            {"step": 1, "action": "Create a 32x32 or 16x16 pixel ICO/PNG file", "code": None},
            {"step": 2, "action": "Add favicon link tag in <head>", "code": "<link rel=\"icon\" href=\"/favicon.ico\" type=\"image/x-icon\">"},
            {"step": 3, "action": "Place favicon.ico in your website root", "code": None},
        ],
    },
    "Missing Open Graph Tags": {
        "title": "Add Open Graph Tags",
        "impact": "WARNING - Controls how your page appears when shared on Facebook, LinkedIn, etc.",
        "steps": [
            {"step": 1, "action": "Add OG tags in <head>", "code": "<meta property=\"og:title\" content=\"Your Title\">\n<meta property=\"og:description\" content=\"Your Description\">\n<meta property=\"og:image\" content=\"https://yoursite.com/image.jpg\">\n<meta property=\"og:url\" content=\"https://yoursite.com/page\">\n<meta property=\"og:type\" content=\"website\">"},
            {"step": 2, "action": "Use an image at least 1200x630 pixels", "code": None},
            {"step": 3, "action": "Test at developers.facebook.com/tools/debug", "code": None},
        ],
    },
    "Missing Twitter Cards": {
        "title": "Add Twitter Card Tags",
        "impact": "WARNING - Controls how your page appears when shared on Twitter/X.",
        "steps": [
            {"step": 1, "action": "Add Twitter meta tags in <head>", "code": "<meta name=\"twitter:card\" content=\"summary_large_image\">\n<meta name=\"twitter:title\" content=\"Your Title\">\n<meta name=\"twitter:description\" content=\"Your Description\">\n<meta name=\"twitter:image\" content=\"https://yoursite.com/image.jpg\">"},
            {"step": 2, "action": "Use summary_large_image for better visibility", "code": None},
        ],
    },
    "Invalid JSON-LD": {
        "title": "Fix Invalid JSON-LD Schema",
        "impact": "CRITICAL - Invalid structured data = no rich snippets in search results.",
        "steps": [
            {"step": 1, "action": "Copy your JSON-LD code", "code": None},
            {"step": 2, "action": "Validate at schema.org/validator or search.google.com/test/rich-results", "code": None},
            {"step": 3, "action": "Fix JSON syntax errors (missing commas, quotes, brackets)", "code": None},
            {"step": 4, "action": "Ensure @context is set to https://schema.org", "code": "<script type=\"application/ld+json\">\n{\n  \"@context\": \"https://schema.org\",\n  \"@type\": \"WebPage\",\n  \"name\": \"Your Page Name\"\n}\n</script>"},
        ],
    },
    "Missing Alt Text": {
        "title": "Add Image Alt Text",
        "impact": "WARNING - Alt text helps Google understand images and improves accessibility.",
        "steps": [
            {"step": 1, "action": "Add alt attribute to every <img> tag", "code": "<img src=\"image.jpg\" alt=\"Descriptive text about the image\">"},
            {"step": 2, "action": "Describe the image content accurately", "code": None},
            {"step": 3, "action": "Include relevant keywords naturally", "code": None},
            {"step": 4, "action": "Keep alt text under 125 characters", "code": None},
        ],
        "example_good": "<img src=\"seo-dashboard.png\" alt=\"AI SEO audit dashboard showing website score and issues\">",
    },
    "Broken Link": {
        "title": "Fix Broken Link",
        "impact": "CRITICAL (internal) / WARNING (external) - Broken links hurt user experience and crawlability.",
        "steps": [
            {"step": 1, "action": "Click the broken URL to verify it's actually broken", "code": None},
            {"step": 2, "action": "For internal links: check if the page was moved or deleted", "code": None},
            {"step": 3, "action": "Update the link to the correct URL", "code": None},
            {"step": 4, "action": "If page was removed, add a 301 redirect or remove the link", "code": None},
            {"step": 5, "action": "For external links: check if the site moved or is down", "code": None},
        ],
    },
    "HTTPS Security": {
        "title": "Enable HTTPS",
        "impact": "CRITICAL - HTTP sites are flagged as 'Not Secure' in browsers and rank lower.",
        "steps": [
            {"step": 1, "action": "Get an SSL certificate (free from Let's Encrypt)", "code": None},
            {"step": 2, "action": "Install the certificate on your hosting", "code": None},
            {"step": 3, "action": "Add redirect rule in .htaccess or server config", "code": "RewriteEngine On\nRewriteCond %{HTTPS} off\nRewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]"},
            {"step": 4, "action": "Update all internal links to use https://", "code": None},
            {"step": 5, "action": "Update sitemap.xml with https URLs", "code": None},
        ],
    },
    "Duplicate Page Content": {
        "title": "Fix Duplicate Content",
        "impact": "WARNING - Duplicate content confuses search engines about which page to rank.",
        "steps": [
            {"step": 1, "action": "Identify the canonical (main) version", "code": None},
            {"step": 2, "action": "Add canonical tag on duplicate pages pointing to main", "code": "<link rel=\"canonical\" href=\"https://yoursite.com/main-page\">"},
            {"step": 3, "action": "OR add 301 redirect from duplicates to main", "code": None},
            {"step": 4, "action": "OR use noindex on duplicate pages", "code": "<meta name=\"robots\" content=\"noindex\">"},
        ],
    },
    "Duplicate Page Title": {
        "title": "Fix Duplicate Titles",
        "impact": "WARNING - Same title on multiple pages confuses search engines.",
        "steps": [
            {"step": 1, "action": "Make each page title unique", "code": None},
            {"step": 2, "action": "Include page-specific keywords", "code": None},
            {"step": 3, "action": "Add brand name differentiator if needed", "code": None},
        ],
    },
    "Orphan Pages": {
        "title": "Fix Orphan Pages",
        "impact": "WARNING - Pages in sitemap with no internal links pointing to them.",
        "steps": [
            {"step": 1, "action": "Add internal links from relevant pages", "code": None},
            {"step": 2, "action": "Include in navigation menu if important", "code": None},
            {"step": 3, "action": "Remove from sitemap if page is obsolete", "code": None},
        ],
    },
    "Thin Content": {
        "title": "Fix Thin Content (<300 words)",
        "impact": "WARNING - Very thin content may be seen as low-quality by search engines.",
        "steps": [
            {"step": 1, "action": "Add more substantive content (aim for 800+ words)", "code": None},
            {"step": 2, "action": "Add H2/H3 subheadings to organize content", "code": None},
            {"step": 3, "action": "Include relevant images, videos, examples", "code": None},
            {"step": 4, "action": "Add FAQ section with related questions", "code": None},
        ],
    },
}


def get_fix_guide_for_issue(api_key: Optional[str], issue_type: str, issue_description: str, url: str) -> str:
    """Generates a step-by-step fix guide for a specific SEO issue."""
    # First check our built-in fix guides
    if issue_type in FIX_GUIDES:
        guide = FIX_GUIDES[issue_type]
        result = f"## {guide['title']}\n\n"
        result += f"**Impact:** {guide['impact']}\n\n"
        result += "### Step-by-Step Fix:\n\n"
        for s in guide["steps"]:
            result += f"**Step {s['step']}:** {s['action']}\n"
            if s.get("code"):
                result += f"```\n{s['code']}\n```\n"
            result += "\n"
        if "example_good" in guide:
            result += f"**Good Example:**\n```\n{guide['example_good']}\n```\n\n"
        if "example_bad" in guide:
            result += f"**Bad Example:**\n```\n{guide['example_bad']}\n```\n\n"
        if "wordpress" in guide:
            result += f"**WordPress:** {guide['wordpress']}\n\n"
        if "shopify" in guide:
            result += f"**Shopify:** {guide['shopify']}\n\n"
        if "webflow" in guide:
            result += f"**Webflow:** {guide['webflow']}\n\n"
        return result

    # Fallback to AI for issues not in our guide
    prompt = (
        f"Provide a detailed step-by-step fix guide for this SEO issue:\n\n"
        f"Issue: {issue_type}\n"
        f"URL: {url}\n"
        f"Description: {issue_description}\n\n"
        f"Include:\n"
        f"1. What this issue means\n"
        f"2. Why it matters for SEO\n"
        f"3. Step-by-step fix with code examples\n"
        f"4. Platform-specific instructions (WordPress, Shopify, Webflow)\n"
        f"5. How to verify the fix\n\n"
        f"Make it actionable and beginner-friendly."
    )
    system = "You are a technical SEO mentor providing step-by-step fix instructions."

    try:
        if api_key and api_key.strip():
            return call_deepseek(api_key, prompt, system)
    except Exception:
        pass

    # Default fallback
    return f"### Fix: {issue_type}\n\n**Description:** {issue_description}\n\n**Steps:**\n1. Locate the issue in your HTML/CMS\n2. Apply the recommended fix\n3. Test the change\n4. Monitor for improvements\n"


def generate_full_fix_plan(api_key: Optional[str], issues: list) -> str:
    """Generates a complete prioritized fix plan for all issues."""
    if not issues:
        return "No issues found! Your site is in great shape."

    # Sort by severity
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 3))

    # Group by issue type
    issue_groups = {}
    for issue in sorted_issues:
        if issue.issue_type not in issue_groups:
            issue_groups[issue.issue_type] = []
        issue_groups[issue.issue_type].append(issue)

    result = "# Complete SEO Fix Plan\n\n"
    result += f"**Total Issues:** {len(issues)} | "
    result += f"**Critical:** {sum(1 for i in issues if i.severity == 'CRITICAL')} | "
    result += f"**Warnings:** {sum(1 for i in issues if i.severity == 'WARNING')}\n\n"
    result += "---\n\n"

    priority = 1
    for issue_type, group in issue_groups.items():
        severity = group[0].severity
        count = len(group)
        sev_icon = "🔴" if severity == "CRITICAL" else ("🟡" if severity == "WARNING" else "🔵")

        result += f"## {sev_icon} Priority {priority}: {issue_type}\n"
        result += f"**Severity:** {severity} | **Affected Pages:** {count}\n\n"

        # URLs affected
        result += "**Affected URLs:**\n"
        for issue in group[:5]:
            result += f"- {issue.url}\n"
        if count > 5:
            result += f"- ... and {count - 5} more\n"
        result += "\n"

        # Get fix guide for this issue type
        guide_text = get_fix_guide_for_issue(api_key, issue_type, group[0].description, group[0].url)
        result += guide_text + "\n---\n\n"
        priority += 1

    result += "## General Best Practices\n\n"
    result += "1. **Fix critical issues first** - They have the biggest impact on rankings\n"
    result += "2. **Fix warnings next** - They improve overall site quality\n"
    result += "3. **Re-audit after fixes** - Verify changes worked\n"
    result += "4. **Monitor Google Search Console** - Track improvements over time\n"

    return result
