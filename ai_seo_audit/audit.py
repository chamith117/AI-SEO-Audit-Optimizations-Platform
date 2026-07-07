"""SEO auditing engine for validating page and website-wide rules, identifying detailed issues with selectors and recommendations.
"""

import hashlib
import re
from typing import List, Dict, Set, Tuple, Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from ai_seo_audit.utils import logger, get_domain
from ai_seo_audit.crawler import CrawlResult
from ai_seo_audit.models import (
    PageMetadataModel,
    HeadingModel,
    ImageModel,
    LinkModel,
    IssueModel,
    PageAuditReport,
    DuplicateGroupModel,
    WebsiteAuditReport,
    SecurityHeaderModel,
    RedirectChainModel,
    ContentQualityModel,
    MixedContentModel,
    AdvancedAuditReport,
    SiteAdvancedAuditReport,
    ResponseMetricsModel,
    PageLoadModel,
    CrawlDepthModel,
    HreflangModel,
)


# Generic anchor text that signals poor link quality
GENERIC_ANCHORS = {
    "click here", "here", "read more", "more", "learn more",
    "this link", "link", "go", "continue", "see more",
}


class SEOAuditor:
    """Evaluates page-level and website-level rules to identify issues and compute quality scores."""

    def __init__(
        self,
        check_links: bool = True,
        check_images: bool = True,
        max_workers: int = 10,
        timeout: int = 4
    ):
        self.check_links = check_links
        self.check_images = check_images
        self.max_workers = max_workers
        self.timeout = timeout
        self.checked_urls_cache: Dict[str, Tuple[Optional[int], bool]] = {}

    def audit_page(
        self,
        crawl_result: CrawlResult,
        metadata: PageMetadataModel,
        links: List[LinkModel],
        images: List[ImageModel],
        robots_txt_found: bool,
        sitemap_xml_found: bool
    ) -> PageAuditReport:
        """Runs comprehensive page-level SEO audits and generates the PageAuditReport."""
        issues: List[IssueModel] = []
        url = crawl_result.final_url
        is_https = urlparse(url).scheme.lower() == "https"
        is_js_rendered = metadata.is_js_rendered

        # --- Rule 1: HTTPS ---
        if not is_https:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="HTTPS Security",
                description="Page is not served over secure HTTPS.",
                recommendation="Install an SSL certificate and redirect all HTTP traffic to HTTPS."
            ))

        # --- Rule 2: Title Tag ---
        if not metadata.title:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered)" if is_js_rendered else ""
            issues.append(IssueModel(
                url=url, severity=severity, issue_type="Missing Title",
                description=f"The page is missing a <title> tag.{js_note}",
                recommendation="Create a unique, descriptive <title> tag between 30-65 characters long."
            ))
        else:
            title_len = len(metadata.title)
            if title_len < 10:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Title Too Short",
                    description=f"Title tag is very short ({title_len} chars). Titles under 10 chars may not rank well.",
                    html_snippet=metadata.title_html, css_selector=metadata.title_css, xpath=metadata.title_xpath,
                    recommendation="Expand the title to 30-65 characters with relevant keywords."
                ))
            elif title_len > 65:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Title Too Long",
                    description=f"Title tag length ({title_len} chars) exceeds 65 characters and may be truncated in search results.",
                    html_snippet=metadata.title_html, css_selector=metadata.title_css, xpath=metadata.title_xpath,
                    recommendation="Shorten the title to 65 characters or less to avoid truncation."
                ))
            # Check for special characters
            special_chars = re.findall(r'[^\x00-\x7F]', metadata.title)
            if special_chars:
                issues.append(IssueModel(
                    url=url, severity="INFO", issue_type="Title Special Characters",
                    description=f"Title contains non-ASCII characters: {''.join(set(special_chars[:5]))}. These may display incorrectly in search results.",
                    html_snippet=metadata.title_html,
                    recommendation="Remove or replace special characters with standard ASCII equivalents."
                ))

        # --- Rule 3: Meta Description ---
        if not metadata.meta_description:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered)" if is_js_rendered else ""
            issues.append(IssueModel(
                url=url, severity=severity, issue_type="Missing Meta Description",
                description=f"The page is missing a meta description tag.{js_note}",
                recommendation="Add a <meta name='description'> tag with a concise summary (50-160 characters)."
            ))
        else:
            desc_len = len(metadata.meta_description)
            if desc_len < 50:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Meta Description Too Short",
                    description=f"Meta description is too short ({desc_len} chars). Recommended minimum is 50 characters.",
                    html_snippet=metadata.meta_desc_html, css_selector=metadata.meta_desc_css, xpath=metadata.meta_desc_xpath,
                    recommendation="Expand meta description to 50-160 characters with a compelling summary."
                ))
            elif desc_len > 160:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Meta Description Too Long",
                    description=f"Meta description length ({desc_len} chars) exceeds 160 characters and may be truncated.",
                    html_snippet=metadata.meta_desc_html, css_selector=metadata.meta_desc_css, xpath=metadata.meta_desc_xpath,
                    recommendation="Shorten meta description to 160 characters or less."
                ))

        # --- Rule 4: Canonical Link ---
        if metadata.multiple_canonicals:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Multiple Canonical Tags",
                description="Multiple canonical tags found on the page. Search engines may ignore all of them.",
                html_snippet=metadata.canonical_html,
                recommendation="Remove duplicate canonical tags and keep only one with the correct self-referencing URL."
            ))
        elif not metadata.canonical_url:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Missing Canonical URL",
                description="Page is missing a canonical link tag.",
                recommendation="Add a <link rel='canonical' href='...'> tag to specify the authoritative version."
            ))
        else:
            if metadata.canonical_is_relative:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Canonical Relative URL",
                    description=f"Canonical URL uses a relative path instead of absolute URL.",
                    html_snippet=metadata.canonical_html,
                    recommendation="Use an absolute URL in the canonical href attribute."
                ))
            if metadata.canonical_url.rstrip("/") != url.rstrip("/"):
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Canonical Mismatch",
                    description=f"Canonical URL '{metadata.canonical_url}' points to a different location than the current page.",
                    html_snippet=metadata.canonical_html, css_selector=metadata.canonical_css, xpath=metadata.canonical_xpath,
                    recommendation="Verify canonical target is correct. If this is the primary page, set self-referencing canonical."
                ))
            if not is_https and metadata.canonical_url and metadata.canonical_url.startswith("https://"):
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Canonical Protocol Mismatch",
                    description="HTTPS canonical URL on HTTP page.",
                    recommendation="Ensure canonical URL uses the same protocol as the page."
                ))

        # --- Rule 5: Viewport Tag ---
        if not metadata.viewport:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Missing Viewport Tag",
                description="Mobile viewport tag is missing. Page is not mobile-responsive.",
                recommendation="Include <meta name='viewport' content='width=device-width, initial-scale=1.0'> in the head."
            ))
        else:
            if not metadata.viewport_has_device_width:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Viewport Missing Device Width",
                    description="Viewport tag does not include width=device-width.",
                    recommendation="Set viewport content to 'width=device-width, initial-scale=1.0'."
                ))
            if not metadata.viewport_allows_scaling:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Viewport Blocks User Scaling",
                    description="Viewport prevents user scaling (user-scalable=no or maximum-scale=1). This hurts accessibility.",
                    recommendation="Allow user scaling by removing user-scalable=no and setting maximum-scale >= 2."
                ))

        # --- Rule 6: Lang Attribute ---
        if not metadata.lang:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Missing Lang Attribute",
                description="The <html> tag is missing a valid 'lang' attribute.",
                recommendation="Add a descriptive lang attribute to the root element, e.g. <html lang='en'>."
            ))

        # --- Rule 7: H1 Headings ---
        h1_count = sum(1 for h in metadata.headings if h.level == 1)
        if h1_count == 0:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered)" if is_js_rendered else ""
            issues.append(IssueModel(
                url=url, severity=severity, issue_type="Missing H1 Heading",
                description=f"The page is missing a primary H1 heading tag.{js_note}",
                recommendation="Implement exactly one H1 heading containing the primary subject of the page."
            ))
        elif h1_count > 1:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Multiple H1 Headings",
                description=f"Multiple H1 tags ({h1_count}) were detected.",
                recommendation="Restrict to a single primary H1 tag, nesting subsections inside H2-H6."
            ))

        # Check heading hierarchy
        heading_levels = [h.level for h in metadata.headings]
        if heading_levels:
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    issues.append(IssueModel(
                        url=url, severity="INFO", issue_type="Heading Hierarchy Skip",
                        description=f"Heading level skipped: H{heading_levels[i-1]} to H{heading_levels[i]}.",
                        recommendation="Use heading levels sequentially (H1 > H2 > H3) without skipping."
                    ))
                    break

        # --- Rule 8: JS-Rendered Page Warning ---
        if is_js_rendered:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="JavaScript Rendered Page",
                description="This page appears to be a JavaScript-rendered SPA. Metadata was extracted from OG tags or JS data as fallback.",
                recommendation="Use Server-Side Rendering (SSR) or Static Site Generation (SSG) for better SEO."
            ))

        # --- Rule 9: Favicon ---
        if not metadata.favicon_url:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Missing Favicon",
                description="Favicon resource is missing from header definitions.",
                recommendation="Add a favicon link tag: <link rel='icon' href='/favicon.ico'>"
            ))

        # --- Rule 10: Open Graph Tags ---
        og_keys = ["og:title", "og:description", "og:image"]
        missing_og = [key for key in og_keys if key not in metadata.open_graph]
        if missing_og:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Missing Open Graph Tags",
                description=f"Missing Open Graph properties: {', '.join(missing_og)}.",
                recommendation="Add og:title, og:description, og:image for proper social sharing."
            ))
        # Validate og:url
        if "og:url" in metadata.open_graph:
            og_url = metadata.open_graph["og:url"]
            if not og_url.startswith(("http://", "https://")):
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="OG URL Invalid",
                    description=f"og:url is not an absolute URL: {og_url}",
                    recommendation="og:url must be an absolute URL matching the canonical URL."
                ))

        # --- Rule 11: Twitter Card Tags ---
        tw_keys = ["twitter:card", "twitter:title"]
        missing_tw = [key for key in tw_keys if key not in metadata.twitter_cards]
        if missing_tw:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Missing Twitter Cards",
                description=f"Missing Twitter metadata: {', '.join(missing_tw)}.",
                recommendation="Add twitter:card and twitter:title meta tags."
            ))

        # --- Rule 12: JSON-LD Schema ---
        for block in metadata.json_ld:
            if not block.valid:
                issues.append(IssueModel(
                    url=url, severity="CRITICAL", issue_type="Invalid JSON-LD",
                    description=f"Schema markup error: {block.error}",
                    html_snippet=block.html_snippet, css_selector=block.css_selector, xpath=block.xpath,
                    recommendation="Fix the JSON syntax error in the structured data block."
                ))
            elif block.required_properties_missing:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Schema Missing Required Properties",
                    description=f"Schema type '{block.schema_type}' is missing required properties: {', '.join(block.required_properties_missing)}",
                    html_snippet=block.html_snippet,
                    recommendation=f"Add required properties for Google Rich Results: {', '.join(block.required_properties_missing)}"
                ))

        # --- Rule 13: Image Alt Tags ---
        missing_alt_imgs = [img for img in images if img.is_missing_alt]
        for img in missing_alt_imgs:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Missing Alt Text",
                description=f"Image is missing an alt description: {img.src[:100]}",
                html_snippet=img.html_snippet, css_selector=img.css_selector, xpath=img.xpath,
                recommendation="Add descriptive, keyword-relevant alt attribute text to this image."
            ))

        # --- Rule 14: Image Missing Width/Height (CLS) ---
        for img in images:
            if not img.width or not img.height:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Image Missing Dimensions",
                    description=f"Image missing width/height attributes (CLS impact): {img.src[:80]}",
                    html_snippet=img.html_snippet,
                    recommendation="Add width and height attributes to prevent Cumulative Layout Shift (CLS)."
                ))
                break  # Only report first instance per page

        # --- Rule 15: Image Not Next-Gen Format ---
        non_next_gen = [img for img in images if img.format and not img.is_next_gen_format]
        if non_next_gen and len(non_next_gen) == len([img for img in images if img.format]):
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Images Not Next-Gen Format",
                description=f"{len(non_next_gen)} images use legacy formats. No WebP/AVIF detected.",
                recommendation="Convert images to WebP or AVIF for 25-50% smaller file sizes."
            ))

        # --- Rule 16: Image Missing Lazy Loading ---
        lazy_candidates = [img for img in images if not img.is_lazy_loaded and not img.fetchpriority]
        if len(lazy_candidates) > 3:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Images Missing Lazy Loading",
                description=f"{len(lazy_candidates)} images are not lazy loaded.",
                recommendation="Add loading='lazy' to below-the-fold images to improve page load speed."
            ))

        # --- Rule 17: Nofollow Links ---
        nofollow_internal = [l for l in links if l.is_nofollow and l.is_internal]
        if nofollow_internal:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Internal Nofollow Links",
                description=f"{len(nofollow_internal)} internal links use rel=nofollow, wasting link equity.",
                recommendation="Remove nofollow from internal links unless specifically needed (e.g. login pages)."
            ))

        # --- Rule 18: Generic Anchor Text ---
        generic_links = [l for l in links if l.anchor_text_type == "generic"]
        if generic_links:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Generic Anchor Text",
                description=f"{len(generic_links)} links use generic anchor text ('click here', 'read more', etc.).",
                recommendation="Replace generic anchors with descriptive text that tells users and search engines what the link target is about."
            ))

        # --- Rule 19: Empty Anchor Text ---
        empty_anchors = [l for l in links if l.text == "[Empty Anchor Text]"]
        if empty_anchors:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Empty Anchor Text",
                description=f"{len(empty_anchors)} links have no anchor text.",
                recommendation="Add descriptive text between <a> and </a> tags."
            ))

        # --- Rule 20: Links Opening New Tab Without noopener ---
        new_tab_noopener = [l for l in links if l.target == "_blank" and l.rel and "noopener" not in l.rel]
        if new_tab_noopener:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Links Missing noopener",
                description=f"{len(new_tab_noopener)} links open in new tab without rel=noopener.",
                recommendation="Add rel='noopener' to links with target='_blank' for security."
            ))

        # --- Rule 21: Noindex Detection ---
        if metadata.indexability and not metadata.indexability.is_indexable:
            if metadata.indexability.noindex_source:
                issues.append(IssueModel(
                    url=url, severity="WARNING", issue_type="Noindex Detected",
                    description=f"Page has noindex directive via {metadata.indexability.noindex_source}.",
                    recommendation="Remove noindex if this page should be indexed by search engines."
                ))

        # --- Rule 22: Nofollow Directive ---
        if metadata.indexability and metadata.indexability.nofollow_detected:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Nofollow Directive Detected",
                description="Page has nofollow meta robots directive. All outgoing links will not pass PageRank.",
                recommendation="Only use nofollow when linking to untrusted or paid content."
            ))

        # --- Rule 23: Nosnippet Directive ---
        if metadata.indexability and metadata.indexability.nosnippet_detected:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Nosnippet Detected",
                description="Page has nosnippet directive. Search engines won't show a snippet for this page.",
                recommendation="Remove nosnippet unless you want to prevent snippet display in search results."
            ))

        # --- Rule 24: Hreflang Issues ---
        if metadata.hreflang_tags:
            for hl in metadata.hreflang_tags:
                if hl.is_broken_target:
                    issues.append(IssueModel(
                        url=url, severity="WARNING", issue_type="Hreflang Broken Target",
                        description=f"Hreflang target {hl.target_url} returns an error.",
                        recommendation="Fix or remove hreflang tag pointing to broken URL."
                    ))

        # --- Rule 25: Pagination ---
        if metadata.pagination_next or metadata.pagination_prev:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="Pagination Detected",
                description=f"Page has pagination links (next: {bool(metadata.pagination_next)}, prev: {bool(metadata.pagination_prev)}).",
                recommendation="Consider using rel=canonical to the main page or implementing infinite scroll for better indexing."
            ))

        # --- Rule 26: AMP ---
        if metadata.amp_url:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="AMP Page Detected",
                description=f"Page has AMP alternate: {metadata.amp_url}",
                recommendation="Ensure AMP page follows Google AMP requirements and has valid structured data."
            ))

        # --- Rule 27: Redirect Loops ---
        if crawl_result.has_redirect_loop:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Redirect Loop",
                description="Page has a redirect loop detected in the redirect chain.",
                recommendation="Fix the redirect chain to avoid circular redirects."
            ))

        # --- Rule 28: Too Many Redirects ---
        if len(crawl_result.redirect_history) > 3:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Too Many Redirects",
                description=f"Page has {len(crawl_result.redirect_history)} redirects in chain (max recommended: 3).",
                recommendation="Consolidate redirects to reduce chain length."
            ))

        # --- Rule 29: Soft 404 ---
        if crawl_result.is_soft_404:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Soft 404 Detected",
                description="Page returns HTTP 200 but content appears to be an error page.",
                recommendation="Return proper 404/410 status code for non-existent pages, or fix the content."
            ))

        # --- Rule 30: HTTP Status Code Errors ---
        if crawl_result.status_code >= 500:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Server Error",
                description=f"Page returned HTTP {crawl_result.status_code} server error.",
                recommendation="Investigate and fix the server-side error causing 5xx responses."
            ))
        elif crawl_result.status_code == 404:
            issues.append(IssueModel(
                url=url, severity="CRITICAL", issue_type="Page Not Found",
                description="Page returned HTTP 404 Not Found.",
                recommendation="Fix the broken URL or set up a proper redirect."
            ))
        elif crawl_result.status_code == 403:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Access Forbidden",
                description="Page returned HTTP 403 Forbidden.",
                recommendation="Check server permissions and ensure the page is accessible to crawlers."
            ))

        # --- Rule 31: Response Time ---
        if crawl_result.total_response_time and crawl_result.total_response_time > 3000:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Slow Response Time",
                description=f"Page took {crawl_result.total_response_time:.0f}ms to respond (over 3 seconds).",
                recommendation="Optimize server response time. Target TTFB under 200ms."
            ))
        elif crawl_result.time_to_first_byte and crawl_result.time_to_first_byte > 1000:
            issues.append(IssueModel(
                url=url, severity="INFO", issue_type="High TTFB",
                description=f"Time to first byte is {crawl_result.time_to_first_byte:.0f}ms (over 1 second).",
                recommendation="Optimize server performance, use CDN, enable caching."
            ))

        # --- Rule 32: Page Size ---
        if crawl_result.html_size_bytes > 1048576:  # > 1MB
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Large Page Size",
                description=f"HTML page size is {crawl_result.html_size_bytes / 1024:.0f}KB (over 1MB).",
                recommendation="Reduce page size by minifying HTML, removing unnecessary code."
            ))

        # --- Rule 33: Crawl Depth ---
        if crawl_result.crawl_depth > 3:
            issues.append(IssueModel(
                url=url, severity="WARNING", issue_type="Deep Page Depth",
                description=f"Page is {crawl_result.crawl_depth} clicks from homepage. Important pages should be within 3 clicks.",
                recommendation="Improve internal linking to flatten site architecture."
            ))

        # --- Rule 34: Word Count / Thin Content ---
        # (Calculated in content quality analysis)

        # --- Rule 35: Text-to-HTML Ratio ---
        # (Calculated in page load analysis)

        # Compute page score
        score = 100
        if not is_https: score -= 10
        if not robots_txt_found: score -= 5
        if not sitemap_xml_found: score -= 5
        if not metadata.title:
            score -= 7 if is_js_rendered else 15
        elif len(metadata.title) < 10:
            score -= 7
        elif len(metadata.title) > 65:
            score -= 5
        if not metadata.meta_description:
            score -= 7 if is_js_rendered else 15
        elif len(metadata.meta_description) < 50:
            score -= 5
        elif len(metadata.meta_description) > 160:
            score -= 3
        if metadata.multiple_canonicals:
            score -= 10
        elif not metadata.canonical_url:
            score -= 10
        elif metadata.canonical_url.rstrip("/") != url.rstrip("/"):
            score -= 5
        if not metadata.viewport: score -= 10
        if not metadata.lang: score -= 5
        if h1_count == 0:
            score -= 5 if is_js_rendered else 10
        elif h1_count > 1: score -= 5
        if missing_og: score -= 3
        if any(not b.valid for b in metadata.json_ld): score -= 5
        if missing_alt_imgs: score -= min(10, len(missing_alt_imgs) * 2)
        if crawl_result.is_soft_404: score -= 20
        if crawl_result.has_redirect_loop: score -= 15
        if len(crawl_result.redirect_history) > 3: score -= 5
        if crawl_result.total_response_time and crawl_result.total_response_time > 3000: score -= 5
        if crawl_result.html_size_bytes > 1048576: score -= 5
        if crawl_result.crawl_depth > 3: score -= 3

        score = max(0, min(100, score))

        # Build response metrics
        response_metrics = ResponseMetricsModel(
            url=url,
            time_to_first_byte=crawl_result.time_to_first_byte,
            total_response_time=crawl_result.total_response_time,
            html_size_bytes=crawl_result.html_size_bytes,
            compressed_size=crawl_result.compressed_size,
            compression_ratio=crawl_result.compression_ratio,
            is_large_page=crawl_result.html_size_bytes > 1048576,
        )

        # Determine redirect type
        redirect_type = None
        if crawl_result.redirect_status_codes:
            redirect_type = str(crawl_result.redirect_status_codes[-1])

        return PageAuditReport(
            url=url,
            status_code=crawl_result.status_code,
            is_https=is_https,
            metadata=metadata,
            links=links,
            images=images,
            issues=issues,
            score=score,
            crawl_depth=crawl_result.crawl_depth,
            response_metrics=response_metrics,
            noindex_detected=metadata.indexability.noindex_source is not None if metadata.indexability else False,
            soft_404_detected=crawl_result.is_soft_404,
            is_redirect=crawl_result.has_redirect,
            redirect_type=redirect_type,
        )

    def audit_website(
        self,
        start_url: str,
        pages: List[PageAuditReport],
        robots_txt_found: bool,
        sitemap_xml_found: bool,
        sitemap_xml_content: Optional[str] = None
    ) -> WebsiteAuditReport:
        """Processes site-wide checks: duplicate content, orphan pages, status distribution, etc."""
        crawled_urls = [p.url for p in pages]
        site_issues: List[IssueModel] = []

        # 1. Broken links and images verification
        if self.check_links or self.check_images:
            self._validate_assets_globally(pages)

        # Re-collect issues on page reports after link/image checking
        for p in pages:
            for l in p.links:
                if l.is_broken:
                    p.issues.append(IssueModel(
                        url=p.url,
                        severity="CRITICAL" if l.is_internal else "WARNING",
                        issue_type="Broken Link",
                        description=f"Broken {'internal' if l.is_internal else 'external'} link: {l.url} (Status: {l.status_code or 'Timeout'})",
                        recommendation="Update or remove the broken link."
                    ))
                    p.score = max(0, p.score - 5)

            for img in p.images:
                if img.is_broken:
                    p.issues.append(IssueModel(
                        url=p.url, severity="CRITICAL", issue_type="Broken Image",
                        description=f"Broken image: {img.src} (Status: {img.status_code or 'Timeout'})",
                        html_snippet=img.html_snippet,
                        recommendation="Fix or remove the broken image source."
                    ))
                    p.score = max(0, p.score - 5)

        # 2. Duplicate content
        duplicate_groups: List[DuplicateGroupModel] = []
        content_hashes: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.title:
                cleaned_text = (p.metadata.title + (p.metadata.meta_description or "")).strip()
                h = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()
                content_hashes.setdefault(h, []).append(p.url)

        for h, urls in content_hashes.items():
            if len(urls) > 1:
                duplicate_groups.append(DuplicateGroupModel(hash=h, urls=urls))
                site_issues.append(IssueModel(
                    url=urls[0], severity="WARNING", issue_type="Duplicate Page Content",
                    description=f"Shared duplicate content with URLs: {', '.join(urls[1:])}.",
                    recommendation="Set unique content or add canonical/301 redirect to master version."
                ))

        # 3. Duplicate titles
        duplicate_titles: Dict[str, List[str]] = {}
        title_map: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.title:
                title_map.setdefault(p.metadata.title.strip(), []).append(p.url)
        for title, urls in title_map.items():
            if len(urls) > 1:
                duplicate_titles[title] = urls
                site_issues.append(IssueModel(
                    url=urls[0], severity="WARNING", issue_type="Duplicate Page Title",
                    description=f"Duplicate title '{title}' shared with: {', '.join(urls[1:])}.",
                    recommendation="Assign distinct title tags to all pages."
                ))

        # 4. Duplicate descriptions
        duplicate_descriptions: Dict[str, List[str]] = {}
        desc_map: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.meta_description:
                desc_map.setdefault(p.metadata.meta_description.strip(), []).append(p.url)
        for desc, urls in desc_map.items():
            if len(urls) > 1:
                duplicate_descriptions[desc] = urls
                site_issues.append(IssueModel(
                    url=urls[0], severity="WARNING", issue_type="Duplicate Meta Description",
                    description=f"Duplicate description shared with: {', '.join(urls[1:])}.",
                    recommendation="Create unique meta descriptions for each page."
                ))

        # 5. Redirect chains
        redirect_chains: Dict[str, List[str]] = {}
        for p in pages:
            if p.is_redirect and p.redirect_type:
                redirect_chains[p.url] = [p.url]  # Simplified

        # 6. Sitemap orphan checker
        orphan_pages: List[str] = []
        if sitemap_xml_content:
            sitemap_urls = re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", sitemap_xml_content, re.IGNORECASE)
            crawled_clean = {u.rstrip("/") for u in crawled_urls}
            for s_url in sitemap_urls:
                s_url_clean = s_url.strip().rstrip("/")
                if s_url_clean not in crawled_clean:
                    orphan_pages.append(s_url)

            if orphan_pages:
                site_issues.append(IssueModel(
                    url=start_url, severity="WARNING", issue_type="Orphan Pages",
                    description=f"{len(orphan_pages)} pages in sitemap have no internal links pointing to them.",
                    recommendation="Link these pages internally or remove from sitemap."
                ))

        # Calculate site-wide score
        if pages:
            avg_page_score = sum(p.score for p in pages) / len(pages)
        else:
            avg_page_score = 100.0

        penalty = 0
        if duplicate_groups: penalty += 10
        if duplicate_titles: penalty += 5
        if duplicate_descriptions: penalty += 5
        if orphan_pages: penalty += 5

        site_score = max(0, min(100, int(avg_page_score - penalty)))

        # Status code distribution
        status_dist: Dict[int, int] = {}
        for p in pages:
            status_dist[p.status_code] = status_dist.get(p.status_code, 0) + 1

        # Calculate AI Visibility Score (based on structured data, schemas, meta tags)
        ai_score = 100
        pages_with_jsonld = sum(1 for p in pages if p.metadata.json_ld)
        jsonld_pct = pages_with_jsonld / max(1, len(pages)) * 100
        if jsonld_pct < 50: ai_score -= 20
        elif jsonld_pct < 80: ai_score -= 10
        
        pages_with_og = sum(1 for p in pages if p.metadata.open_graph)
        og_pct = pages_with_og / max(1, len(pages)) * 100
        if og_pct < 50: ai_score -= 15
        elif og_pct < 80: ai_score -= 5
        
        pages_with_twitter = sum(1 for p in pages if p.metadata.twitter_cards)
        twitter_pct = pages_with_twitter / max(1, len(pages)) * 100
        if twitter_pct < 30: ai_score -= 10
        
        # Check for FAQ/HowTo schemas (good for AI)
        has_faq = any("FAQPage" in str(j.type) for p in pages for j in p.metadata.json_ld)
        has_howto = any("HowTo" in str(j.type) for p in pages for j in p.metadata.json_ld)
        if not has_faq and not has_howto: ai_score -= 5
        
        ai_visibility_score = max(0, min(100, ai_score))

        # Calculate Site Speed Score (based on response time, page size)
        speed_score = 100
        avg_response = sum((p.response_metrics.total_response_time or 0) if p.response_metrics else 0 for p in pages) / max(1, len(pages))
        if avg_response > 3000: speed_score -= 30
        elif avg_response > 2000: speed_score -= 20
        elif avg_response > 1000: speed_score -= 10
        
        avg_size = sum((p.response_metrics.html_size_bytes or 0) if p.response_metrics else 0 for p in pages) / max(1, len(pages))
        if avg_size > 2000000: speed_score -= 25
        elif avg_size > 1000000: speed_score -= 15
        elif avg_size > 500000: speed_score -= 5
        
        # Check for lazy loading
        pages_with_lazy = sum(1 for p in pages if any("lazy" in (img.loading or "") for img in p.images))
        lazy_pct = pages_with_lazy / max(1, len(pages)) * 100
        if lazy_pct < 30: speed_score -= 10
        
        site_speed_score = max(0, min(100, speed_score))

        # Calculate Site Health Score (composite of all factors)
        health_score = (
            site_score * 0.4 +  # SEO Score
            ai_visibility_score * 0.2 +  # AI Visibility
            site_speed_score * 0.2 +  # Speed
            (100 if robots_txt_found else 0) * 0.1 +  # robots.txt
            (100 if sitemap_xml_found else 0) * 0.1  # sitemap
        )
        site_health_score = max(0, min(100, int(health_score)))

        return WebsiteAuditReport(
            start_url=start_url,
            total_pages_crawled=len(pages),
            crawled_urls=crawled_urls,
            pages=pages,
            site_issues=site_issues,
            duplicate_pages=duplicate_groups,
            duplicate_titles=duplicate_titles,
            duplicate_descriptions=duplicate_descriptions,
            orphan_pages=orphan_pages,
            redirect_chains=redirect_chains,
            robots_txt_found=robots_txt_found,
            sitemap_xml_found=sitemap_xml_found,
            score=site_score,
            ai_visibility_score=ai_visibility_score,
            site_speed_score=site_speed_score,
            site_health_score=site_health_score,
            status_distribution=status_dist,
            avg_response_time_ms=sum((p.response_metrics.total_response_time or 0) if p.response_metrics else 0 for p in pages) / max(1, len(pages)),
        )

    def _validate_assets_globally(self, pages: List[PageAuditReport]) -> None:
        """Validates all links and images in parallel."""
        links_to_check: Set[str] = set()
        images_to_check: Set[str] = set()

        for p in pages:
            if self.check_links:
                for l in p.links:
                    links_to_check.add(l.url)
            if self.check_images:
                for img in p.images:
                    images_to_check.add(img.src)

        headers = {"User-Agent": "AI-SEO-Audit-Toolkit/1.0"}

        def _verify_url(url: str) -> Tuple[str, Optional[int], bool]:
            if url in self.checked_urls_cache:
                return url, self.checked_urls_cache[url][0], self.checked_urls_cache[url][1]
            try:
                res = requests.head(url, headers=headers, timeout=self.timeout, allow_redirects=True, verify=False)
                if res.status_code in (400, 404, 405, 501):
                    res = requests.get(url, headers=headers, timeout=self.timeout, stream=True, allow_redirects=True, verify=False)
                status_code = res.status_code
                is_broken = not (200 <= status_code < 400)
            except Exception:
                status_code = None
                is_broken = True
            result_tuple = (status_code, is_broken)
            self.checked_urls_cache[url] = result_tuple
            return url, status_code, is_broken

        all_assets = list(links_to_check | images_to_check)
        logger.info(f"Validating {len(all_assets)} assets with {self.max_workers} threads...")

        results_map = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(_verify_url, url): url for url in all_assets}
            for future in as_completed(future_to_url):
                url, sc, ib = future.result()
                results_map[url] = (sc, ib)

        for p in pages:
            for l in p.links:
                if l.url in results_map:
                    l.status_code = results_map[l.url][0]
                    l.is_broken = results_map[l.url][1]
            for img in p.images:
                if img.src in results_map:
                    img.status_code = results_map[img.src][0]
                    img.is_broken = results_map[img.src][1]

    def audit_advanced_page(
        self,
        crawl_result: CrawlResult,
        metadata: PageMetadataModel,
        links: List[LinkModel],
        images: List[ImageModel],
        html_content: str
    ) -> AdvancedAuditReport:
        """Runs advanced page-level audits."""
        url = crawl_result.final_url
        is_https = urlparse(url).scheme.lower() == "https"

        security_headers = self._analyze_security_headers(crawl_result)
        redirect_chain = self._analyze_redirect_chain(crawl_result)
        content_quality = self._analyze_content_quality(url, metadata, links, images, html_content)
        mixed_content = self._detect_mixed_content(url, html_content) if is_https else []
        url_structure_score = self._score_url_structure(url)
        internal_link_score = self._score_internal_links(links, metadata)

        from ai_seo_audit.ai_engine import calculate_ai_visibility_score
        ai_visibility_data = calculate_ai_visibility_score(
            metadata=metadata,
            content_quality=content_quality,
            security_headers=security_headers,
            mixed_content=mixed_content,
            links=links,
            images=images,
            is_https=is_https,
            crawl_result=crawl_result
        )
        from ai_seo_audit.models import AIVisibilityReport
        ai_visibility = AIVisibilityReport(
            overall_score=ai_visibility_data["overall_score"],
            grade=ai_visibility_data["grade"],
            factors=ai_visibility_data["factors"],
            ai_engine_scores=ai_visibility_data["ai_engine_scores"],
            eeat_score=ai_visibility_data["eeat_score"],
            geo_readiness=ai_visibility_data["geo_readiness"],
            citation_potential=ai_visibility_data["citation_potential"],
            structured_data_score=ai_visibility_data["structured_data_score"],
            answer_snippet_score=ai_visibility_data["answer_snippet_score"],
        )

        return AdvancedAuditReport(
            url=url,
            security_headers=security_headers,
            redirect_chain=redirect_chain,
            content_quality=content_quality,
            mixed_content=mixed_content,
            url_structure_score=url_structure_score,
            internal_link_score=internal_link_score,
            ai_visibility=ai_visibility,
        )

    def _analyze_security_headers(self, crawl_result: CrawlResult) -> List[SecurityHeaderModel]:
        """Analyzes HTTP security headers."""
        headers = crawl_result.headers or {}
        results = []

        header_checks = [
            ("Strict-Transport-Security", "HSTS", "CRITICAL",
             "HTTP Strict Transport Security forces browsers to use HTTPS.",
             "Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains"),
            ("X-Content-Type-Options", "X-Content-Type-Options", "WARNING",
             "Prevents MIME type sniffing attacks.",
             "Add header: X-Content-Type-Options: nosniff"),
            ("X-Frame-Options", "X-Frame-Options", "WARNING",
             "Prevents clickjacking by controlling iframe embedding.",
             "Add header: X-Frame-Options: DENY or SAMEORIGIN"),
            ("X-XSS-Protection", "X-XSS-Protection", "INFO",
             "Enables browser XSS filtering.",
             "Add header: X-XSS-Protection: 1; mode=block"),
            ("Content-Security-Policy", "Content-Security-Policy", "WARNING",
             "Controls which resources the browser can load.",
             "Implement a Content-Security-Policy header."),
            ("Referrer-Policy", "Referrer-Policy", "INFO",
             "Controls referrer information sent with requests.",
             "Add header: Referrer-Policy: strict-origin-when-cross-origin"),
            ("Permissions-Policy", "Permissions-Policy", "INFO",
             "Controls which browser features can be used.",
             "Add a Permissions-Policy header to restrict camera, microphone, etc."),
        ]

        for header_name, display_name, severity, desc, rec in header_checks:
            # Case-insensitive header check
            header_value = None
            for k, v in headers.items():
                if k.lower() == header_name.lower():
                    header_value = v
                    break

            if header_value:
                results.append(SecurityHeaderModel(
                    header=display_name, present=True, value=header_value,
                    severity="INFO", description=desc, recommendation=""
                ))
            else:
                results.append(SecurityHeaderModel(
                    header=display_name, present=False, value=None,
                    severity=severity, description=desc, recommendation=rec
                ))

        return results

    def _analyze_redirect_chain(self, crawl_result: CrawlResult) -> Optional[RedirectChainModel]:
        """Analyzes redirect chain."""
        history = crawl_result.redirect_history or []
        if not history:
            return None

        chain = list(history)
        chain.append(crawl_result.final_url)
        total = len(chain) - 1

        return RedirectChainModel(
            original_url=chain[0] if chain else crawl_result.final_url,
            chain=chain,
            final_url=crawl_result.final_url,
            total_redirects=total,
            is_too_long=total > 3
        )

    def _analyze_content_quality(
        self,
        url: str,
        metadata: PageMetadataModel,
        links: List[LinkModel],
        images: List[ImageModel],
        html_content: str
    ) -> ContentQualityModel:
        """Analyzes content quality metrics."""
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()

        words = text.split()
        word_count = len(words)
        char_count = len(text)

        sentences = re.split(r'[.!?]+', text)
        sentence_count = max(1, len([s for s in sentences if s.strip()]))
        avg_words = round(word_count / sentence_count, 1) if sentence_count > 0 else 0

        if word_count > 0 and sentence_count > 0:
            syllables = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in words)
            asl = word_count / sentence_count
            asw = syllables / word_count
            fk_score = 206.835 - 1.015 * asl - 84.6 * asw
            if fk_score >= 90: readability = "Very Easy (5th grade)"
            elif fk_score >= 80: readability = "Easy (6th grade)"
            elif fk_score >= 70: readability = "Fairly Easy (7th grade)"
            elif fk_score >= 60: readability = "Standard (8th-9th grade)"
            elif fk_score >= 50: readability = "Fairly Difficult (10th-12th grade)"
            elif fk_score >= 30: readability = "Difficult (College level)"
            else: readability = "Very Difficult (Graduate level)"
        else:
            readability = "N/A"
            avg_words = 0

        is_thin = word_count < 300

        heading_levels = [h.level for h in metadata.headings]
        hierarchy_valid = True
        for i in range(1, len(heading_levels)):
            if heading_levels[i] > heading_levels[i-1] + 1:
                hierarchy_valid = False
                break

        internal = sum(1 for l in links if l.is_internal)
        external = sum(1 for l in links if not l.is_internal)

        img_count = len(images)
        img_with_alt = sum(1 for i in images if not i.is_missing_alt)
        img_no_lazy = sum(1 for i in images if not i.is_lazy_loaded)

        return ContentQualityModel(
            url=url,
            word_count=word_count,
            character_count=char_count,
            sentence_count=sentence_count,
            avg_words_per_sentence=avg_words,
            readability_score=readability,
            is_thin_content=is_thin,
            heading_hierarchy_valid=hierarchy_valid,
            internal_link_count=internal,
            external_link_count=external,
            image_count=img_count,
            images_with_alt=img_with_alt,
            images_without_lazy=img_no_lazy,
        )

    def _detect_mixed_content(self, page_url: str, html_content: str) -> List[MixedContentModel]:
        """Detects HTTP resources loaded on HTTPS pages."""
        issues = []
        patterns = [
            (r'src=["\']http://([^"\']+)["\']', "script/img"),
            (r'href=["\']http://([^"\']+)["\']', "link"),
            (r'action=["\']http://([^"\']+)["\']', "form"),
            (r'url\(["\']?http://([^"\']\)["\']?)', "css"),
        ]
        for pattern, res_type in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                resource_url = f"http://{match}"
                issues.append(MixedContentModel(
                    page_url=page_url,
                    resource_url=resource_url,
                    resource_type=res_type,
                ))
        return issues[:20]

    def _score_url_structure(self, url: str) -> int:
        """Scores URL structure quality (0-100)."""
        score = 100
        parsed = urlparse(url)
        path = parsed.path

        if len(url) > 100: score -= 10
        elif len(url) > 75: score -= 5

        segments = [s for s in path.split("/") if s]
        if len(segments) > 4: score -= 15
        elif len(segments) > 3: score -= 5

        if parsed.query: score -= 10
        if "_" in path: score -= 5
        if any(c.isupper() for c in path): score -= 5
        if any(ext in path for ext in [".html", ".php", ".asp", ".jsp"]): score -= 10

        return max(0, score)

    def _score_internal_links(self, links: List[LinkModel], metadata: PageMetadataModel) -> int:
        """Scores internal linking quality (0-100)."""
        score = 100
        internal_links = [l for l in links if l.is_internal]
        external_links = [l for l in links if not l.is_internal]

        if len(internal_links) == 0: score -= 30
        elif len(internal_links) < 3: score -= 10

        if external_links and len(external_links) > len(internal_links) * 2: score -= 10

        empty_anchors = sum(1 for l in internal_links if not l.text.strip() or l.text.strip().lower() in GENERIC_ANCHORS)
        if empty_anchors > 0: score -= min(15, empty_anchors * 3)

        h1_texts = [h.text.lower() for h in metadata.headings if h.level == 1]
        if h1_texts and not any(h1 in l.text.lower() for l in internal_links for h1 in h1_texts): score -= 5

        return max(0, score)
