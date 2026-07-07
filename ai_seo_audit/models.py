"""Pydantic schemas representing scraped data, page-level issues, and site-level SEO audits.
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HeadingModel(BaseModel):
    """Represents a heading tag on the page (H1-H6)."""
    level: int = Field(..., description="The heading level, from 1 to 6")
    text: str = Field(..., description="The text content of the heading")


class ImageModel(BaseModel):
    """Represents an image found on the page with full attribute extraction."""
    src: str = Field(..., description="The src attribute / URL of the image")
    alt: Optional[str] = Field(None, description="The alternative text of the image")
    is_missing_alt: bool = Field(..., description="Flag indicating if the ALT attribute is empty or missing")
    status_code: Optional[int] = Field(None, description="The HTTP response status code of the image check")
    is_broken: Optional[bool] = Field(None, description="Flag indicating if the image is broken")
    html_snippet: Optional[str] = None
    css_selector: Optional[str] = None
    xpath: Optional[str] = None
    width: Optional[str] = Field(None, description="Width attribute value")
    height: Optional[str] = Field(None, description="Height attribute value")
    loading: Optional[str] = Field(None, description="Loading attribute: lazy, eager, or auto")
    is_lazy_loaded: bool = Field(default=False, description="Whether image uses lazy loading")
    decoding: Optional[str] = Field(None, description="Decoding attribute: async, sync, auto")
    srcset: Optional[str] = Field(None, description="Responsive image srcset attribute")
    sizes: Optional[str] = Field(None, description="Responsive image sizes attribute")
    fetchpriority: Optional[str] = Field(None, description="Fetch priority hint")
    format: Optional[str] = Field(None, description="Image format detected: webp, avif, png, jpeg, gif, svg")
    is_next_gen_format: bool = Field(default=False, description="Whether image uses WebP or AVIF format")
    alt_text_length: int = Field(default=0, description="Length of alt text in characters")


class LinkModel(BaseModel):
    """Represents an anchor link found on the page with full attribute extraction."""
    url: str = Field(..., description="The absolute or relative URL target of the link")
    text: str = Field(..., description="The anchor text associated with the link")
    is_internal: bool = Field(..., description="Whether the link leads to an internal resource of the site")
    status_code: Optional[int] = Field(None, description="The HTTP response status code of the link when checked")
    is_broken: Optional[bool] = Field(None, description="Flag indicating if the link is broken (non-200 or timeout)")
    rel: Optional[str] = Field(None, description="Full rel attribute value")
    is_nofollow: bool = Field(default=False, description="Whether link has rel=nofollow")
    is_sponsored: bool = Field(default=False, description="Whether link has rel=sponsored")
    is_ugc: bool = Field(default=False, description="Whether link has rel=ugc (user-generated content)")
    target: Optional[str] = Field(None, description="Target attribute: _blank, _self, etc.")
    is_self_referencing: bool = Field(default=False, description="Whether link points to same page")
    is_jump_link: bool = Field(default=False, description="Whether link is hash-only (#section)")
    anchor_text_type: Optional[str] = Field(None, description="Type: generic, brand, exact-match, partial-match, naked-url, image")
    link_position: Optional[str] = Field(None, description="Position: content, navigation, footer, sidebar, header")


class JSONLDModel(BaseModel):
    """Represents the parsing validation metadata for a JSON-LD script block."""
    valid: bool = Field(..., description="True if it parsed successfully as JSON")
    data: Optional[str] = Field(None, description="The raw string content inside the block")
    error: Optional[str] = Field(None, description="The error message if parsing failed")
    html_snippet: Optional[str] = None
    css_selector: Optional[str] = None
    xpath: Optional[str] = None
    schema_type: Optional[str] = Field(None, description="The @type value: Article, Product, FAQPage, etc.")
    schema_types: List[str] = Field(default_factory=list, description="All @type values found (including nested)")
    required_properties_missing: List[str] = Field(default_factory=list, description="Missing required properties per schema type")
    recommended_properties_missing: List[str] = Field(default_factory=list, description="Missing recommended properties")
    google_rich_results_compatible: bool = Field(default=False, description="Whether it qualifies for Google rich results")
    validation_errors: List[str] = Field(default_factory=list, description="Detailed validation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    schema_id: Optional[str] = Field(None, description="@id value for cross-referencing")


class HreflangModel(BaseModel):
    """Represents an hreflang tag for internationalization."""
    source_url: str = Field(..., description="The page containing the hreflang tag")
    target_url: str = Field(..., description="The hreflang target URL")
    language_code: str = Field(..., description="Language code: en, es, fr, etc.")
    country_code: Optional[str] = Field(None, description="Country code: US, UK, etc.")
    is_return_link_valid: Optional[bool] = Field(None, description="Whether target page has return hreflang link")
    is_broken_target: Optional[bool] = Field(None, description="Whether hreflang target returns error")
    is_x_default: bool = Field(default=False, description="Whether this is the x-default hreflang")


class RobotsDirectiveModel(BaseModel):
    """Represents a single robots directive from meta robots or x-robots-tag."""
    directive: str = Field(..., description="Directive name: noindex, nofollow, nosnippet, etc.")
    value: Optional[str] = Field(None, description="Directive value if any (e.g. max-snippet:50)")
    source: str = Field(..., description="Source: meta-robots or x-robots-tag")


class CrawlDepthModel(BaseModel):
    """Tracks how deep a page is from the homepage."""
    url: str = Field(..., description="Page URL")
    depth: int = Field(..., description="Click depth from homepage (0 = homepage)")
    is_too_deep: bool = Field(default=False, description="Whether depth exceeds 3 levels")


class ResponseMetricsModel(BaseModel):
    """HTTP response timing and size metrics."""
    url: str = Field(..., description="Page URL")
    time_to_first_byte: Optional[float] = Field(None, description="TTFB in milliseconds")
    total_response_time: Optional[float] = Field(None, description="Total response time in milliseconds")
    html_size_bytes: int = Field(default=0, description="HTML page size in bytes")
    compressed_size: Optional[int] = Field(None, description="Compressed transfer size in bytes")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio percentage")
    is_large_page: bool = Field(default=False, description="Whether page exceeds 1MB")


class IndexabilityModel(BaseModel):
    """Comprehensive indexability status for a page."""
    is_indexable: bool = Field(default=True, description="Whether page can be indexed")
    indexability_status: str = Field(default="Indexable", description="Status: Indexable, Noindex, Blocked by Robots.txt, Redirect, Canonical to non-indexable, 4xx, 5xx")
    noindex_source: Optional[str] = Field(None, description="Source of noindex: meta-robots or x-robots-tag")
    nofollow_detected: bool = Field(default=False, description="Whether nofollow directive is present")
    nosnippet_detected: bool = Field(default=False, description="Whether nosnippet directive is present")
    max_snippet: Optional[int] = Field(None, description="Max-snippet directive value")
    max_image_preview: Optional[str] = Field(None, description="Max-image-preview directive value")
    blocked_reason: Optional[str] = Field(None, description="Reason why page is not indexable")


class PageLoadModel(BaseModel):
    """Resource loading details for a page."""
    url: str = Field(..., description="Page URL")
    total_page_size_bytes: int = Field(default=0, description="Total page weight in bytes")
    html_size_bytes: int = Field(default=0, description="HTML size in bytes")
    css_count: int = Field(default=0, description="Number of CSS files")
    js_count: int = Field(default=0, description="Number of JS files")
    css_size_bytes: int = Field(default=0, description="Total CSS size in bytes")
    js_size_bytes: int = Field(default=0, description="Total JS size in bytes")
    image_count: int = Field(default=0, description="Number of images")
    image_size_bytes: int = Field(default=0, description="Total image size in bytes")
    third_party_count: int = Field(default=0, description="Number of third-party resources")
    text_to_html_ratio: float = Field(default=0.0, description="Text to HTML ratio percentage")
    inline_css_count: int = Field(default=0, description="Number of inline style blocks")
    inline_js_count: int = Field(default=0, description="Number of inline script blocks")


class PageMetadataModel(BaseModel):
    """Represents standard page SEO metadata extended with social and code checks."""
    title: Optional[str] = Field(None, description="The page title tag content")
    title_html: Optional[str] = None
    title_css: Optional[str] = None
    title_xpath: Optional[str] = None

    meta_description: Optional[str] = Field(None, description="The meta description content")
    meta_desc_html: Optional[str] = None
    meta_desc_css: Optional[str] = None
    meta_desc_xpath: Optional[str] = None

    meta_robots: Optional[str] = Field(None, description="The meta robots directive content")
    robots_directives: List[RobotsDirectiveModel] = Field(default_factory=list, description="Parsed individual robots directives")
    x_robots_tag_directives: List[RobotsDirectiveModel] = Field(default_factory=list, description="X-Robots-Tag header directives")
    canonical_url: Optional[str] = Field(None, description="The canonical URL link href")
    canonical_html: Optional[str] = None
    canonical_css: Optional[str] = None
    canonical_xpath: Optional[str] = None
    canonical_is_self_ref: Optional[bool] = Field(None, description="Whether canonical points to self")
    canonical_is_relative: Optional[bool] = Field(None, description="Whether canonical href was relative URL")
    multiple_canonicals: bool = Field(default=False, description="Whether multiple canonical tags found")

    favicon_url: Optional[str] = Field(None, description="Discovered favicon target URL")
    viewport: Optional[str] = Field(None, description="The content attribute of viewport tag")
    viewport_has_device_width: bool = Field(default=False, description="Whether viewport includes width=device-width")
    viewport_allows_scaling: bool = Field(default=True, description="Whether viewport allows user scaling")
    lang: Optional[str] = Field(None, description="The lang attribute of the HTML tag")
    is_js_rendered: bool = Field(default=False, description="Whether page appears to be JavaScript-rendered (SPA)")

    headings: List[HeadingModel] = Field(default_factory=list, description="List of headings found")
    open_graph: Dict[str, str] = Field(default_factory=dict, description="Parsed Open Graph tags")
    twitter_cards: Dict[str, str] = Field(default_factory=dict, description="Parsed Twitter card tags")
    json_ld: List[JSONLDModel] = Field(default_factory=list, description="Validation of JSON-LD scripts")
    hreflang_tags: List[HreflangModel] = Field(default_factory=list, description="Hreflang internationalization tags")
    pagination_next: Optional[str] = Field(None, description="Pagination rel=next URL")
    pagination_prev: Optional[str] = Field(None, description="Pagination rel=prev URL")
    amp_url: Optional[str] = Field(None, description="AMP alternate URL")
    http_equiv_tags: Dict[str, str] = Field(default_factory=dict, description="HTTP-EQUIV meta tags")
    indexability: Optional[IndexabilityModel] = Field(None, description="Indexability status")


class IssueModel(BaseModel):
    """An identified SEO issue on a specific page or the site as a whole."""
    url: str = Field(..., description="The URL containing the issue")
    severity: str = Field(..., description="CRITICAL, WARNING, or INFO")
    issue_type: str = Field(..., description="The category/type of the issue")
    description: str = Field(..., description="Detailed explanation of the issue")
    html_snippet: Optional[str] = Field(None, description="The raw HTML code of the failing element")
    css_selector: Optional[str] = Field(None, description="CSS selector targeting the element")
    xpath: Optional[str] = Field(None, description="XPath path targeting the element")
    recommendation: str = Field(..., description="Actionable recommendation on how to resolve the issue")


class PageAuditReport(BaseModel):
    """SEO report for an individual crawled page."""
    url: str = Field(..., description="The URL of this page")
    status_code: int = Field(..., description="The response status code")
    is_https: bool = Field(..., description="Indicates if the page uses HTTPS")
    metadata: PageMetadataModel = Field(..., description="Parsed page SEO metadata")
    links: List[LinkModel] = Field(default_factory=list, description="All links found on this page")
    images: List[ImageModel] = Field(default_factory=list, description="All images found on this page")
    issues: List[IssueModel] = Field(default_factory=list, description="SEO issues found on this page")
    score: int = Field(..., ge=0, le=100, description="The page-level SEO score")
    crawl_depth: int = Field(default=0, description="Click depth from homepage")
    response_metrics: Optional[ResponseMetricsModel] = Field(None, description="HTTP response timing and size")
    page_load: Optional[PageLoadModel] = Field(None, description="Page resource loading details")
    hreflang_issues_count: int = Field(default=0, description="Number of hreflang issues found")
    noindex_detected: bool = Field(default=False, description="Whether noindex directive is present")
    soft_404_detected: bool = Field(default=False, description="Whether page appears to be soft 404")
    is_redirect: bool = Field(default=False, description="Whether page had redirects")
    redirect_type: Optional[str] = Field(None, description="Redirect type: 301, 302, 307, 308")


class KeywordModel(BaseModel):
    """A single extracted or suggested keyword with metrics."""
    keyword: str = Field(..., description="The keyword or phrase")
    count: int = Field(default=0, description="Number of occurrences found")
    density: float = Field(default=0.0, description="Keyword density percentage")
    in_title: bool = Field(default=False, description="Whether keyword appears in any page title")
    in_meta_desc: bool = Field(default=False, description="Whether keyword appears in any meta description")
    in_headings: bool = Field(default=False, description="Whether keyword appears in any heading")
    in_url: bool = Field(default=False, description="Whether keyword appears in any URL")
    pages: List[str] = Field(default_factory=list, description="URLs where this keyword was found")


class ContentIdeaModel(BaseModel):
    """A content idea generated from keyword research."""
    title: str = Field(..., description="Suggested content title")
    description: str = Field(..., description="Brief content outline or description")
    target_keywords: List[str] = Field(default_factory=list, description="Keywords to target")
    content_type: str = Field(default="blog_post", description="Type of content: blog_post, guide, listicle, faq, comparison")
    priority: str = Field(default="medium", description="Priority: high, medium, low")


class KeywordResearchReport(BaseModel):
    """Complete keyword research report for the audited site."""
    primary_keywords: List[KeywordModel] = Field(default_factory=list, description="Top primary keywords extracted from site content")
    secondary_keywords: List[KeywordModel] = Field(default_factory=list, description="Secondary / long-tail keywords found")
    lsi_keywords: List[KeywordModel] = Field(default_factory=list, description="LSI (Latent Semantic Indexing) suggested keywords")
    recommended_keywords: List[KeywordModel] = Field(default_factory=list, description="AI-recommended keywords to target")
    content_ideas: List[ContentIdeaModel] = Field(default_factory=list, description="AI-generated content ideas")
    keyword_gaps: List[str] = Field(default_factory=list, description="Important keywords missing from the site")
    total_words_analyzed: int = Field(default=0, description="Total word count across all pages")
    unique_words_found: int = Field(default=0, description="Number of unique words found")


class DuplicateGroupModel(BaseModel):
    """A group of identical duplicate pages."""
    hash: str = Field(..., description="MD5 hash of page text content")
    urls: List[str] = Field(..., description="URLs sharing the exact content")


class SecurityHeaderModel(BaseModel):
    """Security header analysis for a page."""
    header: str = Field(..., description="Header name")
    present: bool = Field(..., description="Whether the header is present")
    value: Optional[str] = Field(None, description="Header value if present")
    severity: str = Field(default="INFO", description="CRITICAL, WARNING, or INFO")
    description: str = Field(default="", description="What this header does")
    recommendation: str = Field(default="", description="How to fix if missing")


class RedirectChainModel(BaseModel):
    """Redirect chain analysis."""
    original_url: str = Field(..., description="Starting URL")
    chain: List[str] = Field(default_factory=list, description="Redirect chain URLs")
    final_url: str = Field(..., description="Final destination URL")
    total_redirects: int = Field(default=0, description="Number of redirects")
    is_too_long: bool = Field(default=False, description="Whether chain exceeds 3 hops")


class ContentQualityModel(BaseModel):
    """Content quality metrics for a page."""
    url: str = Field(..., description="Page URL")
    word_count: int = Field(default=0, description="Total word count")
    character_count: int = Field(default=0, description="Total character count")
    sentence_count: int = Field(default=0, description="Estimated sentence count")
    avg_words_per_sentence: float = Field(default=0.0, description="Average words per sentence")
    readability_score: str = Field(default="N/A", description="Readability grade level")
    is_thin_content: bool = Field(default=False, description="Whether content is below 300 words")
    heading_hierarchy_valid: bool = Field(default=True, description="Whether heading levels follow proper order")
    internal_link_count: int = Field(default=0, description="Number of internal links")
    external_link_count: int = Field(default=0, description="Number of external links")
    image_count: int = Field(default=0, description="Number of images")
    images_with_alt: int = Field(default=0, description="Images with alt text")
    images_without_lazy: int = Field(default=0, description="Images missing lazy loading")


class MixedContentModel(BaseModel):
    """Mixed content issue (HTTP resource on HTTPS page)."""
    page_url: str = Field(..., description="The HTTPS page URL")
    resource_url: str = Field(..., description="The HTTP resource URL")
    resource_type: str = Field(default="unknown", description="Type: script, link, img, iframe, etc.")
    html_snippet: Optional[str] = None


class AIVisibilityFactorModel(BaseModel):
    """A single AI visibility scoring factor."""
    name: str = Field(..., description="Factor name")
    score: int = Field(default=0, ge=0, le=100, description="Score for this factor (0-100)")
    weight: float = Field(default=1.0, description="Weight in overall score")
    status: str = Field(default="good", description="good, warning, or critical")
    details: str = Field(default="", description="Details about this factor")
    recommendation: str = Field(default="", description="How to improve")


class AIVisibilityReport(BaseModel):
    """AI Search Engine Visibility Score report."""
    overall_score: int = Field(default=0, ge=0, le=100, description="Overall AI visibility score (0-100)")
    grade: str = Field(default="N/A", description="Grade: A+, A, B, C, D, F")
    factors: List[AIVisibilityFactorModel] = Field(default_factory=list, description="Individual scoring factors")
    summary: str = Field(default="", description="AI-generated summary of visibility")
    ai_engine_scores: Dict[str, int] = Field(default_factory=dict, description="Scores per AI engine: google_ai, chatgpt, perplexity")
    content_freshness: str = Field(default="unknown", description="Content freshness assessment")
    eeat_score: int = Field(default=0, ge=0, le=100, description="E-E-A-T signal score")
    geo_readiness: int = Field(default=0, ge=0, le=100, description="Generative Engine Optimization readiness")
    citation_potential: int = Field(default=0, ge=0, le=100, description="How likely AI engines will cite this content")
    structured_data_score: int = Field(default=0, ge=0, le=100, description="Structured data completeness for AI")
    answer_snippet_score: int = Field(default=0, ge=0, le=100, description="Content formatted for direct answers")


class AdvancedAuditReport(BaseModel):
    """Advanced audit data for a single page."""
    url: str = Field(..., description="Page URL")
    security_headers: List[SecurityHeaderModel] = Field(default_factory=list)
    redirect_chain: Optional[RedirectChainModel] = None
    content_quality: Optional[ContentQualityModel] = None
    mixed_content: List[MixedContentModel] = Field(default_factory=list)
    url_structure_score: int = Field(default=100, ge=0, le=100, description="URL structure quality score")
    internal_link_score: int = Field(default=100, ge=0, le=100, description="Internal linking quality score")
    ai_visibility: Optional[AIVisibilityReport] = Field(None, description="AI visibility score for this page")


class SiteAdvancedAuditReport(BaseModel):
    """Site-wide advanced audit summary."""
    pages: List[AdvancedAuditReport] = Field(default_factory=list)
    total_security_issues: int = Field(default=0)
    total_mixed_content: int = Field(default=0)
    total_thin_content: int = Field(default=0)
    avg_readability: str = Field(default="N/A")
    avg_word_count: int = Field(default=0)
    heading_hierarchy_issues: int = Field(default=0)
    total_images_no_lazy: int = Field(default=0)
    total_images_no_width_height: int = Field(default=0, description="Images missing width/height attributes")
    total_images_not_next_gen: int = Field(default=0, description="Images not using WebP/AVIF format")
    total_nofollow_links: int = Field(default=0, description="Total nofollow links found")
    total_nofollow_internal: int = Field(default=0, description="Internal nofollow links (link equity waste)")
    total_pages_no_indexable: int = Field(default=0, description="Pages with noindex or blocked")
    total_soft_404: int = Field(default=0, description="Soft 404 pages detected")
    total_redirect_chains: int = Field(default=0, description="Redirect chains found")
    total_redirect_loops: int = Field(default=0, description="Redirect loops detected")
    avg_response_time_ms: float = Field(default=0.0, description="Average response time in ms")
    avg_ttfb_ms: float = Field(default=0.0, description="Average time to first byte in ms")
    avg_page_size_kb: float = Field(default=0.0, description="Average page size in KB")
    total_hreflang_issues: int = Field(default=0, description="Hreflang tag issues found")
    status_distribution: Dict[int, int] = Field(default_factory=dict, description="HTTP status code distribution")
    avg_crawl_depth: float = Field(default=0.0, description="Average crawl depth from homepage")
    pages_too_deep: int = Field(default=0, description="Pages deeper than 3 clicks from homepage")


class WebsiteAuditReport(BaseModel):
    """The master website-level SEO Audit Report."""
    start_url: str = Field(..., description="The initial domain URL audited")
    total_pages_crawled: int = Field(..., description="Total pages processed")
    crawled_urls: List[str] = Field(default_factory=list, description="List of all successfully crawled page URLs")
    pages: List[PageAuditReport] = Field(default_factory=list, description="Individual page audit results")
    site_issues: List[IssueModel] = Field(default_factory=list, description="Global site-level issues")
    duplicate_pages: List[DuplicateGroupModel] = Field(default_factory=list, description="Duplicate content groups")
    duplicate_titles: Dict[str, List[str]] = Field(default_factory=dict, description="Identified duplicate page titles")
    duplicate_descriptions: Dict[str, List[str]] = Field(default_factory=dict, description="Identified duplicate meta descriptions")
    orphan_pages: List[str] = Field(default_factory=list, description="Orphan page URLs (listed in sitemap but unlinked)")
    redirect_chains: Dict[str, List[str]] = Field(default_factory=dict, description="Discovered redirect paths starting at key URLs")
    robots_txt_found: bool = Field(default=False, description="Whether robots.txt was reachable")
    sitemap_xml_found: bool = Field(default=False, description="Whether sitemap.xml was reachable")
    keyword_research: Optional[KeywordResearchReport] = Field(None, description="Keyword research analysis report")
    advanced_audit: Optional[SiteAdvancedAuditReport] = Field(None, description="Advanced audit data")
    score: int = Field(..., ge=0, le=100, description="The aggregate site SEO health score")
    status_distribution: Dict[int, int] = Field(default_factory=dict, description="HTTP status code distribution across site")
    avg_response_time_ms: float = Field(default=0.0, description="Average response time across site in ms")
    total_response_time_ms: float = Field(default=0.0, description="Total crawl time in ms")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        description="ISO 8601 UTC timestamp of the audit generation"
    )
