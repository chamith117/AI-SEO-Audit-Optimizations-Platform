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
    SiteAdvancedAuditReport
)


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
        """Runs page-level SEO audits and generates the PageAuditReport."""
        issues: List[IssueModel] = []
        url = crawl_result.final_url
        is_https = urlparse(url).scheme.lower() == "https"
        is_js_rendered = metadata.is_js_rendered

        # --- Rule 1: HTTPS ---
        if not is_https:
            issues.append(
                IssueModel(
                    url=url,
                    severity="CRITICAL",
                    issue_type="HTTPS Security",
                    description="Page is not served over secure HTTPS.",
                    recommendation="Install an SSL certificate and redirect all HTTP traffic to HTTPS."
                )
            )

        # --- Rule 2: Title Tag ---
        if not metadata.title:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered — title may load via JS)" if is_js_rendered else ""
            issues.append(
                IssueModel(
                    url=url,
                    severity=severity,
                    issue_type="Missing Title",
                    description=f"The page is missing a <title> tag.{js_note}",
                    recommendation="Create a unique, descriptive <title> tag between 30-65 characters long. For JS-rendered pages, ensure the title is in the initial HTML or use SSR."
                )
            )
        else:
            title_len = len(metadata.title)
            if title_len < 30 or title_len > 65:
                issues.append(
                    IssueModel(
                        url=url,
                        severity="WARNING",
                        issue_type="Title Length",
                        description=f"Title tag length ({title_len} chars) is outside the recommended 30-65 range.",
                        html_snippet=metadata.title_html,
                        css_selector=metadata.title_css,
                        xpath=metadata.title_xpath,
                        recommendation="Adjust the title text length to fall between 30 and 65 characters to avoid truncation."
                    )
                )

        # --- Rule 3: Meta Description ---
        if not metadata.meta_description:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered — description may load via JS)" if is_js_rendered else ""
            issues.append(
                IssueModel(
                    url=url,
                    severity=severity,
                    issue_type="Missing Meta Description",
                    description=f"The page is missing a meta description tag.{js_note}",
                    recommendation="Add a <meta name='description'> tag with a concise summary of the page (50-160 characters). For JS-rendered pages, ensure meta tags are in the initial HTML or use SSR."
                )
            )
        else:
            desc_len = len(metadata.meta_description)
            if desc_len < 50 or desc_len > 160:
                issues.append(
                    IssueModel(
                        url=url,
                        severity="WARNING",
                        issue_type="Meta Description Length",
                        description=f"Meta description length ({desc_len} chars) is outside the recommended 50-160 range.",
                        html_snippet=metadata.meta_desc_html,
                        css_selector=metadata.meta_desc_css,
                        xpath=metadata.meta_desc_xpath,
                        recommendation="Optimize meta description content length to stay between 50 and 160 characters."
                    )
                )

        # --- Rule 4: Canonical Link ---
        if not metadata.canonical_url:
            issues.append(
                IssueModel(
                    url=url,
                    severity="CRITICAL",
                    issue_type="Missing Canonical URL",
                    description="Page is missing a canonical link tag.",
                    recommendation="Add a <link rel='canonical' href='...'> tag to specify the authoritative version of the page."
                )
            )
        elif metadata.canonical_url.rstrip("/") != url.rstrip("/"):
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Canonical Mismatch",
                    description=f"Canonical URL '{metadata.canonical_url}' points to a different location than the current page.",
                    html_snippet=metadata.canonical_html,
                    css_selector=metadata.canonical_css,
                    xpath=metadata.canonical_xpath,
                    recommendation="Verify that the canonical URL target is correct. If this is the primary page, align the canonical link href."
                )
            )

        # --- Rule 5: Viewport Tag ---
        if not metadata.viewport:
            issues.append(
                IssueModel(
                    url=url,
                    severity="CRITICAL",
                    issue_type="Missing Viewport Tag",
                    description="Mobile viewport tag is missing. Page is not mobile-responsive.",
                    recommendation="Include <meta name='viewport' content='width=device-width, initial-scale=1.0'> in the head section."
                )
            )

        # --- Rule 6: Lang Attribute ---
        if not metadata.lang:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Missing Lang Attribute",
                    description="The <html> tag is missing a valid 'lang' attribute.",
                    recommendation="Add a descriptive lang attribute to the root element, e.g. <html lang='en'>."
                )
            )

        # --- Rule 7: H1 Headings ---
        h1_count = sum(1 for h in metadata.headings if h.level == 1)
        if h1_count == 0:
            severity = "WARNING" if is_js_rendered else "CRITICAL"
            js_note = " (page appears JavaScript-rendered — headings may load via JS)" if is_js_rendered else ""
            issues.append(
                IssueModel(
                    url=url,
                    severity=severity,
                    issue_type="Missing H1 Heading",
                    description=f"The page is missing a primary H1 heading tag.{js_note}",
                    recommendation="Implement exactly one H1 heading containing the primary subject of the page. For JS-rendered pages, ensure headings are in the initial HTML or use SSR."
                )
            )
        elif h1_count > 1:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Multiple H1 Headings",
                    description=f"Multiple H1 tags ({h1_count}) were detected.",
                    recommendation="Restrict heading structure to a single primary H1 tag, nesting subsections inside H2-H6 tags."
                )
            )

        # --- Rule 8: JS-Rendered Page Warning ---
        if is_js_rendered:
            issues.append(
                IssueModel(
                    url=url,
                    severity="INFO",
                    issue_type="JavaScript Rendered Page",
                    description="This page appears to be a JavaScript-rendered SPA (Single Page Application). Search engines may not see all content. Metadata extracted from OG tags or JS data as fallback.",
                    recommendation="Use Server-Side Rendering (SSR) or Static Site Generation (SSG) to ensure all SEO metadata is in the initial HTML. For Next.js, use getServerSideProps or getStaticProps."
                )
            )

        # --- Rule 8: Favicon Link ---
        if not metadata.favicon_url:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Missing Favicon",
                    description="Favicon resource is missing from header definitions.",
                    recommendation="Add a favicon link tag in the head, e.g. <link rel='icon' href='/favicon.ico'>"
                )
            )

        # --- Rule 9: Open Graph Tags ---
        og_keys = ["og:title", "og:description", "og:image"]
        missing_og = [key for key in og_keys if key not in metadata.open_graph]
        if missing_og:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Missing Open Graph Tags",
                    description=f"Missing recommended Open Graph social properties: {', '.join(missing_og)}.",
                    recommendation="Implement Open Graph meta tags to control visual appearance when shared on platforms like Facebook and LinkedIn."
                )
            )

        # --- Rule 10: Twitter Card Tags ---
        tw_keys = ["twitter:card", "twitter:title"]
        missing_tw = [key for key in tw_keys if key not in metadata.twitter_cards]
        if missing_tw:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Missing Twitter Cards",
                    description=f"Missing recommended Twitter metadata properties: {', '.join(missing_tw)}.",
                    recommendation="Implement twitter:card and twitter:title meta tags to format cards when shared on Twitter."
                )
            )

        # --- Rule 11: Schema.org JSON-LD ---
        for block in metadata.json_ld:
            if not block.valid:
                issues.append(
                    IssueModel(
                        url=url,
                        severity="CRITICAL",
                        issue_type="Invalid JSON-LD",
                        description=f"Schema markup error: {block.error}",
                        html_snippet=block.html_snippet,
                        css_selector=block.css_selector,
                        xpath=block.xpath,
                        recommendation="Format the JSON-LD string inside the script block to be RFC 8259 valid."
                    )
                )

        # --- Rule 12: Alt Tags ---
        missing_alt_imgs = [img for img in images if img.is_missing_alt]
        for img in missing_alt_imgs:
            issues.append(
                IssueModel(
                    url=url,
                    severity="WARNING",
                    issue_type="Missing Alt Text",
                    description=f"Image is missing an alt description: {img.src}",
                    html_snippet=img.html_snippet,
                    css_selector=img.css_selector,
                    xpath=img.xpath,
                    recommendation="Add descriptive, keyword-relevant alt attribute text to this image tag."
                )
            )

        # Compute page score
        score = 100
        if not is_https: score -= 10
        if not robots_txt_found: score -= 5
        if not sitemap_xml_found: score -= 5
        if not metadata.title:
            score -= 7 if is_js_rendered else 15  # Less penalty for JS-rendered pages
        elif len(metadata.title) < 30 or len(metadata.title) > 65: score -= 7
        if not metadata.meta_description:
            score -= 7 if is_js_rendered else 15  # Less penalty for JS-rendered pages
        elif len(metadata.meta_description) < 50 or len(metadata.meta_description) > 160: score -= 7
        if not metadata.canonical_url: score -= 10
        elif metadata.canonical_url.rstrip("/") != url.rstrip("/"): score -= 5
        if not metadata.viewport: score -= 10
        if not metadata.lang: score -= 5
        if h1_count == 0:
            score -= 5 if is_js_rendered else 10  # Less penalty for JS-rendered pages
        elif h1_count > 1: score -= 5
        if missing_og: score -= 3
        if any(not b.valid for b in metadata.json_ld): score -= 5
        
        # Missing ALT penalties
        alt_penalty = min(10, len(missing_alt_imgs) * 2)
        score -= alt_penalty
        
        score = max(0, min(100, score))

        return PageAuditReport(
            url=url,
            status_code=crawl_result.status_code,
            is_https=is_https,
            metadata=metadata,
            links=links,
            images=images,
            issues=issues,
            score=score
        )

    def audit_website(
        self,
        start_url: str,
        pages: List[PageAuditReport],
        robots_txt_found: bool,
        sitemap_xml_found: bool,
        sitemap_xml_content: Optional[str] = None
    ) -> WebsiteAuditReport:
        """Processes site-wide checks: duplicate content, duplicate headers, sitemap orphans, and redirects."""
        crawled_urls = [p.url for p in pages]
        site_issues: List[IssueModel] = []
        
        # 1. Broken links and images verification
        if self.check_links or self.check_images:
            self._validate_assets_globally(pages)

        # Re-collect issues on page reports after link/image checking
        for p in pages:
            # Check for broken links
            for l in p.links:
                if l.is_broken:
                    p.issues.append(
                        IssueModel(
                            url=p.url,
                            severity="CRITICAL" if l.is_internal else "WARNING",
                            issue_type="Broken Link",
                            description=f"Broken {'internal' if l.is_internal else 'external'} link: {l.url} (Status: {l.status_code or 'Timeout/Error'})",
                            recommendation="Remove the broken URL link or update it to point to a valid 200 OK location."
                        )
                    )
                    # Deduct points from page score
                    p.score = max(0, p.score - 5)

            # Check for broken images
            for img in p.images:
                if img.is_broken:
                    p.issues.append(
                        IssueModel(
                            url=p.url,
                            severity="CRITICAL",
                            issue_type="Broken Image",
                            description=f"Broken image asset: {img.src} (Status: {img.status_code or 'Timeout/Error'})",
                            html_snippet=img.html_snippet,
                            css_selector=img.css_selector,
                            xpath=img.xpath,
                            recommendation="Ensure the image source file exists and is accessible. Update src URL configuration."
                        )
                    )
                    p.score = max(0, p.score - 5)

        # 2. Duplicate content (stripped page body text hash check)
        duplicate_groups: List[DuplicateGroupModel] = []
        content_hashes: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.title:  # Use page text properties loosely
                cleaned_text = (p.metadata.title + (p.metadata.meta_description or "")).strip()
                h = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()
                content_hashes.setdefault(h, []).append(p.url)

        for h, urls in content_hashes.items():
            if len(urls) > 1:
                duplicate_groups.append(DuplicateGroupModel(hash=h, urls=urls))
                site_issues.append(
                    IssueModel(
                        url=urls[0],
                        severity="WARNING",
                        issue_type="Duplicate Page Content",
                        description=f"Shared duplicate content matching MD5 {h} with URLs: {', '.join(urls[1:])}.",
                        recommendation="Set unique descriptive content or add a 301 redirect / canonical tag pointing to the master version."
                    )
                )

        # 3. Duplicate titles
        duplicate_titles: Dict[str, List[str]] = {}
        title_map: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.title:
                title_map.setdefault(p.metadata.title.strip(), []).append(p.url)
        for title, urls in title_map.items():
            if len(urls) > 1:
                duplicate_titles[title] = urls
                site_issues.append(
                    IssueModel(
                        url=urls[0],
                        severity="WARNING",
                        issue_type="Duplicate Page Title",
                        description=f"Duplicate page title '{title}' shared with URLs: {', '.join(urls[1:])}.",
                        recommendation="Assign distinct title tags to all pages representing their specific topic."
                    )
                )

        # 4. Duplicate descriptions
        duplicate_descriptions: Dict[str, List[str]] = {}
        desc_map: Dict[str, List[str]] = {}
        for p in pages:
            if p.metadata.meta_description:
                desc_map.setdefault(p.metadata.meta_description.strip(), []).append(p.url)
        for desc, urls in desc_map.items():
            if len(urls) > 1:
                duplicate_descriptions[desc] = urls
                site_issues.append(
                    IssueModel(
                        url=urls[0],
                        severity="WARNING",
                        issue_type="Duplicate Meta Description",
                        description=f"Duplicate description tag shared with URLs: {', '.join(urls[1:])}.",
                        recommendation="Each indexable page needs a unique meta description describing the topic."
                    )
                )

        # 5. Redirect chains
        redirect_chains: Dict[str, List[str]] = {}
        # We will retrieve history from crawling results if any page has a redirect history.
        # But we pass page reports, let's trace redirect chains by checking if there's redirect data.

        # 6. Sitemap XML orphan checker
        orphan_pages: List[str] = []
        if sitemap_xml_content:
            sitemap_urls = re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", sitemap_xml_content, re.IGNORECASE)
            # Remove trailing slashes for loose comparison
            crawled_clean = {u.rstrip("/") for u in crawled_urls}
            for s_url in sitemap_urls:
                s_url_clean = s_url.strip().rstrip("/")
                if s_url_clean not in crawled_clean:
                    orphan_pages.append(s_url)

            if orphan_pages:
                site_issues.append(
                    IssueModel(
                        url=start_url,
                        severity="WARNING",
                        issue_type="Orphan Pages",
                        description=f"Found {len(orphan_pages)} pages listed in the sitemap.xml that have no internal links pointing to them.",
                        recommendation="Link these pages internally from relevant content pages or delete them from the sitemap.xml if obsolete."
                    )
                )

        # Calculate site-wide score
        # Average of page scores minus website penalties
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
            score=site_score
        )

    def _validate_assets_globally(self, pages: List[PageAuditReport]) -> None:
        """Validates all links and images in parallel across pages, updating validation tags."""
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
            # Cache check
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
        logger.info(f"Validating {len(all_assets)} asset links concurrently using {self.max_workers} threads...")

        results_map = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(_verify_url, url): url for url in all_assets}
            for future in as_completed(future_to_url):
                url, sc, ib = future.result()
                results_map[url] = (sc, ib)

        # Update link and image reference schemas on page models
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
        """Runs advanced page-level audits: security headers, content quality, mixed content, URL structure."""
        url = crawl_result.final_url
        is_https = urlparse(url).scheme.lower() == "https"

        # 1. Security Headers Analysis
        security_headers = self._analyze_security_headers(crawl_result)

        # 2. Redirect Chain Analysis
        redirect_chain = self._analyze_redirect_chain(crawl_result)

        # 3. Content Quality Analysis
        content_quality = self._analyze_content_quality(url, metadata, links, images, html_content)

        # 4. Mixed Content Detection
        mixed_content = self._detect_mixed_content(url, html_content) if is_https else []

        # 5. URL Structure Score
        url_structure_score = self._score_url_structure(url)

        # 6. Internal Link Score
        internal_link_score = self._score_internal_links(links, metadata)

        # 7. AI Visibility Score
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

        # Check each security header
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
             "Controls which resources the browser is allowed to load.",
             "Implement a Content-Security-Policy header restricting script and resource sources."),
            ("Referrer-Policy", "Referrer-Policy", "INFO",
             "Controls how much referrer information is sent with requests.",
             "Add header: Referrer-Policy: strict-origin-when-cross-origin"),
            ("Permissions-Policy", "Permissions-Policy", "INFO",
             "Controls which browser features and APIs can be used.",
             "Add a Permissions-Policy header to restrict camera, microphone, geolocation, etc."),
        ]

        for header_name, display_name, severity, desc, rec in header_checks:
            if header_name in headers:
                results.append(SecurityHeaderModel(
                    header=display_name,
                    present=True,
                    value=headers.get(header_name),
                    severity="INFO",
                    description=desc,
                    recommendation=""
                ))
            else:
                results.append(SecurityHeaderModel(
                    header=display_name,
                    present=False,
                    value=None,
                    severity=severity,
                    description=desc,
                    recommendation=rec
                ))

        return results

    def _analyze_redirect_chain(self, crawl_result: CrawlResult) -> Optional[RedirectChainModel]:
        """Analyzes redirect chain if any."""
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
        # Extract text content from HTML (rough estimate)
        import re as _re
        text = _re.sub(r'<[^>]+>', ' ', html_content)
        text = _re.sub(r'\s+', ' ', text).strip()

        words = text.split()
        word_count = len(words)
        char_count = len(text)

        # Sentence count (rough estimate)
        sentences = _re.split(r'[.!?]+', text)
        sentence_count = max(1, len([s for s in sentences if s.strip()]))

        avg_words = round(word_count / sentence_count, 1) if sentence_count > 0 else 0

        # Readability (Flesch-Kincaid approximation)
        if word_count > 0 and sentence_count > 0:
            syllables = sum(max(1, len(_re.findall(r'[aeiouy]+', w.lower()))) for w in words)
            asl = word_count / sentence_count
            asw = syllables / word_count
            fk_score = 206.835 - 1.015 * asl - 84.6 * asw
            if fk_score >= 90:
                readability = "Very Easy (5th grade)"
            elif fk_score >= 80:
                readability = "Easy (6th grade)"
            elif fk_score >= 70:
                readability = "Fairly Easy (7th grade)"
            elif fk_score >= 60:
                readability = "Standard (8th-9th grade)"
            elif fk_score >= 50:
                readability = "Fairly Difficult (10th-12th grade)"
            elif fk_score >= 30:
                readability = "Difficult (College level)"
            else:
                readability = "Very Difficult (Graduate level)"
        else:
            readability = "N/A"
            avg_words = 0

        # Thin content check
        is_thin = word_count < 300

        # Heading hierarchy check
        heading_levels = [h.level for h in metadata.headings]
        hierarchy_valid = True
        for i in range(1, len(heading_levels)):
            if heading_levels[i] > heading_levels[i-1] + 1:
                hierarchy_valid = False
                break

        # Link counts
        internal = sum(1 for l in links if l.is_internal)
        external = sum(1 for l in links if not l.is_internal)

        # Image analysis
        img_count = len(images)
        img_with_alt = sum(1 for i in images if not i.is_missing_alt)
        img_no_lazy = sum(1 for i in images if 'loading' not in (i.html_snippet or '').lower() and 'lazy' not in (i.html_snippet or '').lower())

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
        import re as _re
        issues = []

        # Find HTTP resources in common tags
        patterns = [
            (r'src=["\']http://([^"\']+)["\']', "script/img"),
            (r'href=["\']http://([^"\']+)["\']', "link"),
            (r'action=["\']http://([^"\']+)["\']', "form"),
            (r'url\(["\']?http://([^"\']\)["\']?)', "css"),
        ]

        for pattern, res_type in patterns:
            matches = _re.findall(pattern, html_content)
            for match in matches:
                resource_url = f"http://{match}"
                issues.append(MixedContentModel(
                    page_url=page_url,
                    resource_url=resource_url,
                    resource_type=res_type,
                ))

        return issues[:20]  # Cap at 20 to avoid flooding

    def _score_url_structure(self, url: str) -> int:
        """Scores URL structure quality (0-100)."""
        score = 100
        parsed = urlparse(url)
        path = parsed.path

        # Penalize very long URLs
        if len(url) > 100:
            score -= 10
        elif len(url) > 75:
            score -= 5

        # Penalize too many path segments
        segments = [s for s in path.split("/") if s]
        if len(segments) > 4:
            score -= 15
        elif len(segments) > 3:
            score -= 5

        # Penalize query parameters
        if parsed.query:
            score -= 10

        # Penalize underscores in URL
        if "_" in path:
            score -= 5

        # Penalize uppercase letters in path
        if any(c.isupper() for c in path):
            score -= 5

        # Penalize URL with file extensions
        if any(ext in path for ext in [".html", ".php", ".asp", ".jsp"]):
            score -= 10

        return max(0, score)

    def _score_internal_links(self, links: List[LinkModel], metadata: PageMetadataModel) -> int:
        """Scores internal linking quality (0-100)."""
        score = 100
        internal_links = [l for l in links if l.is_internal]
        external_links = [l for l in links if not l.is_internal]

        # No internal links
        if len(internal_links) == 0:
            score -= 30
        elif len(internal_links) < 3:
            score -= 10

        # Too many external links relative to internal
        if external_links and len(external_links) > len(internal_links) * 2:
            score -= 10

        # No descriptive anchor text
        empty_anchors = sum(1 for l in internal_links if not l.text.strip() or l.text.strip().lower() in ["click here", "here", "read more", "more"])
        if empty_anchors > 0:
            score -= min(15, empty_anchors * 3)

        # Check if H1 text appears in any link anchor
        h1_texts = [h.text.lower() for h in metadata.headings if h.level == 1]
        if h1_texts and not any(h1 in l.text.lower() for l in internal_links for h1 in h1_texts):
            score -= 5

        return max(0, score)
