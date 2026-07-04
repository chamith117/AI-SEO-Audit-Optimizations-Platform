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
    """Represents an image found on the page."""
    src: str = Field(..., description="The src attribute / URL of the image")
    alt: Optional[str] = Field(None, description="The alternative text of the image")
    is_missing_alt: bool = Field(..., description="Flag indicating if the ALT attribute is empty or missing")
    status_code: Optional[int] = Field(None, description="The HTTP response status code of the image check")
    is_broken: Optional[bool] = Field(None, description="Flag indicating if the image is broken")
    html_snippet: Optional[str] = None
    css_selector: Optional[str] = None
    xpath: Optional[str] = None


class LinkModel(BaseModel):
    """Represents an anchor link found on the page."""
    url: str = Field(..., description="The absolute or relative URL target of the link")
    text: str = Field(..., description="The anchor text associated with the link")
    is_internal: bool = Field(..., description="Whether the link leads to an internal resource of the site")
    status_code: Optional[int] = Field(None, description="The HTTP response status code of the link when checked")
    is_broken: Optional[bool] = Field(None, description="Flag indicating if the link is broken (non-200 or timeout)")


class JSONLDModel(BaseModel):
    """Represents the parsing validation metadata for a JSON-LD script block."""
    valid: bool = Field(..., description="True if it parsed successfully as JSON")
    data: Optional[str] = Field(None, description="The raw string content inside the block")
    error: Optional[str] = Field(None, description="The error message if parsing failed")
    html_snippet: Optional[str] = None
    css_selector: Optional[str] = None
    xpath: Optional[str] = None


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
    canonical_url: Optional[str] = Field(None, description="The canonical URL link href")
    canonical_html: Optional[str] = None
    canonical_css: Optional[str] = None
    canonical_xpath: Optional[str] = None

    favicon_url: Optional[str] = Field(None, description="Discovered favicon target URL")
    viewport: Optional[str] = Field(None, description="The content attribute of viewport tag")
    lang: Optional[str] = Field(None, description="The lang attribute of the HTML tag")
    
    headings: List[HeadingModel] = Field(default_factory=list, description="List of headings found")
    open_graph: Dict[str, str] = Field(default_factory=dict, description="Parsed Open Graph tags")
    twitter_cards: Dict[str, str] = Field(default_factory=dict, description="Parsed Twitter card tags")
    json_ld: List[JSONLDModel] = Field(default_factory=list, description="Validation of JSON-LD scripts")


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
    score: int = Field(..., ge=0, le=100, description="The aggregate site SEO health score")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        description="ISO 8601 UTC timestamp of the audit generation"
    )
