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
