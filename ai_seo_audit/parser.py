"""HTML Parser for extracting page contents, metadata, social tags, viewport, lang, JSON-LD, hreflang, and more.
"""

import json
import re
from typing import List, Optional, Dict, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from ai_seo_audit.models import (
    PageMetadataModel,
    HeadingModel,
    ImageModel,
    LinkModel,
    JSONLDModel,
    HreflangModel,
    RobotsDirectiveModel,
    IndexabilityModel,
)
from ai_seo_audit.utils import (
    is_internal_url,
    get_css_selector,
    get_xpath
)

# Common JS framework indicators in raw HTML
JS_FRAMEWORK_INDICATORS = [
    "react", "vue", "angular", "next", "nuxt", "gatsby", "remix",
    "__NEXT_DATA__", "__NUXT__", "__APP_DATA__", "__INITIAL_STATE__",
    "id=\"__next\"", "id=\"__nuxt\"", "id=\"root\"", "id=\"app\"",
    "data-reactroot", "data-v-", "ng-app", "ng-controller",
]

# Image format detection from URL
IMAGE_FORMAT_MAP = {
    ".webp": "webp",
    ".avif": "avif",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".gif": "gif",
    ".svg": "svg",
    ".bmp": "bmp",
    ".tiff": "tiff",
    ".tif": "tiff",
}

NEXT_GEN_FORMATS = {"webp", "avif"}

# Generic anchor text patterns
GENERIC_ANCHORS = {
    "click here", "here", "read more", "more", "learn more",
    "this link", "link", "go", "continue", "see more",
    "click here to", "find out more", "discover more",
}


class SEOHTMLParser:
    """Parses HTML content to extract core SEO and metadata elements, including social and Schema markup."""

    def __init__(self, html_content: str, base_url: str, x_robots_tag_header: Optional[str] = None):
        """Initializes the parser.

        Args:
            html_content: Raw HTML text of the page.
            base_url: The absolute base URL (final crawl URL) to resolve relative links.
            x_robots_tag_header: Optional X-Robots-Tag header value from HTTP response.
        """
        self.raw_html = html_content
        self.soup = BeautifulSoup(html_content, "lxml")
        self.base_url = base_url
        self.x_robots_tag_header = x_robots_tag_header

    def _is_js_rendered_page(self) -> bool:
        """Detects if page is likely JavaScript-rendered (SPA framework)."""
        html_lower = self.raw_html[:50000].lower()
        for indicator in JS_FRAMEWORK_INDICATORS:
            if indicator.lower() in html_lower:
                return True
        return False

    def _extract_title_from_js(self) -> Optional[str]:
        """Try to extract title from JavaScript-embedded data (Next.js, Nuxt, etc.)."""
        for pattern, extractor in [
            (r'__NEXT_DATA__\s*=\s*(\{.*?\})\s*(?:;|</script>)', self._extract_from_next_data),
            (r'__NUXT__\s*=\s*(\{.*?\})\s*(?:;|</script>)', self._extract_from_nuxt),
            (r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*(?:;|</script>)', self._recursive_find_title),
            (r'window\.__APP_DATA__\s*=\s*(\{.*?\})\s*(?:;|</script>)', self._recursive_find_title),
        ]:
            match = re.search(pattern, self.raw_html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    result = extractor(data) if extractor != self._recursive_find_title else extractor(data)
                    if result:
                        return result
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
        return None

    def _extract_from_next_data(self, data: dict) -> Optional[str]:
        props = data.get("props", {}).get("pageProps", {})
        if "title" in props:
            return props["title"]
        if "meta" in props and isinstance(props["meta"], dict):
            return props["meta"].get("title")
        return self._recursive_find_title(data)

    def _extract_from_nuxt(self, data: dict) -> Optional[str]:
        head = data.get("head", {})
        if "title" in head:
            return head["title"]
        return None

    def _recursive_find_title(self, obj, depth=0) -> Optional[str]:
        """Recursively search a dict/list for a 'title' key."""
        if depth > 5:
            return None
        if isinstance(obj, dict):
            if "title" in obj and isinstance(obj["title"], str) and len(obj["title"]) > 3:
                return obj["title"]
            for v in obj.values():
                result = self._recursive_find_title(v, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj[:10]:
                result = self._recursive_find_title(item, depth + 1)
                if result:
                    return result
        return None

    def _extract_desc_from_js(self) -> Optional[str]:
        """Try to extract meta description from JavaScript-embedded data."""
        for pattern in [
            r'__NEXT_DATA__\s*=\s*(\{.*?\})\s*(?:;|</script>)',
            r'__NUXT__\s*=\s*(\{.*?\})\s*(?:;|</script>)',
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*(?:;|</script>)',
        ]:
            match = re.search(pattern, self.raw_html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    desc = self._recursive_find_description(data)
                    if desc:
                        return desc
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
        return None

    def _recursive_find_description(self, obj, depth=0) -> Optional[str]:
        """Recursively search for description in JSON data."""
        if depth > 5:
            return None
        if isinstance(obj, dict):
            for key in ["description", "metaDescription", "meta_description", "desc"]:
                if key in obj and isinstance(obj[key], str) and len(obj[key]) > 20:
                    return obj[key]
            for v in obj.values():
                result = self._recursive_find_description(v, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj[:10]:
                result = self._recursive_find_description(item, depth + 1)
                if result:
                    return result
        return None

    def _parse_robots_directives(self, content: str) -> List[RobotsDirectiveModel]:
        """Parse individual directives from robots meta content string."""
        directives = []
        if not content:
            return directives
        for part in content.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                name, value = part.split(":", 1)
                directives.append(RobotsDirectiveModel(
                    directive=name.strip().lower(),
                    value=value.strip(),
                    source="meta-robots"
                ))
            else:
                directives.append(RobotsDirectiveModel(
                    directive=part.strip().lower(),
                    value=None,
                    source="meta-robots"
                ))
        return directives

    def _parse_x_robots_tag(self, header_value: str) -> List[RobotsDirectiveModel]:
        """Parse X-Robots-Tag header value into individual directives."""
        directives = []
        if not header_value:
            return directives
        for part in header_value.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                name, value = part.split(":", 1)
                directives.append(RobotsDirectiveModel(
                    directive=name.strip().lower(),
                    value=value.strip(),
                    source="x-robots-tag"
                ))
            else:
                directives.append(RobotsDirectiveModel(
                    directive=part.strip().lower(),
                    value=None,
                    source="x-robots-tag"
                ))
        return directives

    def _detect_image_format(self, url: str) -> Optional[str]:
        """Detect image format from URL extension."""
        url_lower = url.lower().split("?")[0].split("#")[0]
        for ext, fmt in IMAGE_FORMAT_MAP.items():
            if url_lower.endswith(ext):
                return fmt
        return None

    def _classify_anchor_text(self, text: str) -> str:
        """Classify anchor text type."""
        text_lower = text.lower().strip()
        if not text or text_lower in ("[empty anchor text]", ""):
            return "empty"
        if text_lower in GENERIC_ANCHORS:
            return "generic"
        if text_lower.startswith(("http://", "https://", "www.")):
            return "naked-url"
        if len(text.split()) == 1 and text_lower == text_lower.title():
            return "brand"
        return "partial-match"

    def _classify_link_position(self, tag) -> str:
        """Determine link position based on parent elements."""
        parent = tag.parent
        while parent and parent.name:
            if parent.name in ("nav", "header"):
                return "navigation"
            if parent.name == "footer":
                return "footer"
            if parent.name == "aside":
                return "sidebar"
            if parent.name in ("article", "main", "section", "div"):
                # Check if this div is likely a sidebar or nav
                classes = " ".join(parent.get("class", []))
                if any(x in classes.lower() for x in ["sidebar", "side-bar", "widget"]):
                    return "sidebar"
                if any(x in classes.lower() for x in ["nav", "menu", "header"]):
                    return "navigation"
                if any(x in classes.lower() for x in ["footer", "bottom"]):
                    return "footer"
            parent = parent.parent
        return "content"

    def parse_metadata(self, robots_txt_blocked: bool = False) -> PageMetadataModel:
        """Extracts standard page level SEO meta elements, social elements, and JSON-LD validations.

        Returns:
            PageMetadataModel: The parsed metadata structure.
        """
        is_js_rendered = self._is_js_rendered_page()

        # Title tag details
        title_tag = self.soup.find("title")
        title_val = title_tag.get_text().strip() if title_tag else None
        title_html = str(title_tag) if title_tag else None
        title_css = get_css_selector(title_tag) if title_tag else None
        title_xpath = get_xpath(title_tag) if title_tag else None

        # If title is empty or missing, try JS data and OG tags
        og_data = self.get_open_graph()
        if not title_val or title_val.strip() == "":
            if "og:title" in og_data:
                title_val = og_data["og:title"]
            else:
                js_title = self._extract_title_from_js()
                if js_title:
                    title_val = js_title

        # Meta description details
        meta_desc = self.soup.find(
            "meta",
            attrs={"name": lambda x: x and x.lower() == "description"}
        )
        desc_val = None
        desc_html = None
        desc_css = None
        desc_xpath = None
        if meta_desc and hasattr(meta_desc, "get"):
            desc_val = meta_desc.get("content", "").strip() or None
            desc_html = str(meta_desc)
            desc_css = get_css_selector(meta_desc)
            desc_xpath = get_xpath(meta_desc)

        if not desc_val or desc_val.strip() == "":
            if "og:description" in og_data:
                desc_val = og_data["og:description"]
            else:
                js_desc = self._extract_desc_from_js()
                if js_desc:
                    desc_val = js_desc

        # Meta robots
        meta_robots = self.soup.find(
            "meta",
            attrs={"name": lambda x: x and x.lower() == "robots"}
        )
        robots_val = meta_robots.get("content", "").strip() or None if meta_robots and hasattr(meta_robots, "get") else None
        robots_directives = self._parse_robots_directives(robots_val)

        # X-Robots-Tag directives from HTTP header
        x_robots_directives = self._parse_x_robots_tag(self.x_robots_tag_header)

        # Check for noindex from any source
        all_directives = robots_directives + x_robots_directives
        noindex_detected = any(d.directive == "noindex" for d in all_directives)
        nofollow_detected = any(d.directive == "nofollow" for d in all_directives)
        nosnippet_detected = any(d.directive == "nosnippet" for d in all_directives)
        max_snippet_val = None
        max_image_preview_val = None
        for d in all_directives:
            if d.directive == "max-snippet" and d.value:
                try:
                    max_snippet_val = int(d.value)
                except ValueError:
                    pass
            if d.directive == "max-image-preview" and d.value:
                max_image_preview_val = d.value

        # Build indexability status
        is_indexable = True
        indexability_status = "Indexable"
        noindex_source = None
        blocked_reason = None

        if robots_txt_blocked:
            is_indexable = False
            indexability_status = "Blocked by Robots.txt"
            blocked_reason = "Page blocked by robots.txt rule"
        elif noindex_detected:
            is_indexable = False
            indexability_status = "Noindex"
            for d in all_directives:
                if d.directive == "noindex":
                    noindex_source = d.source
                    break

        indexability = IndexabilityModel(
            is_indexable=is_indexable,
            indexability_status=indexability_status,
            noindex_source=noindex_source,
            nofollow_detected=nofollow_detected,
            nosnippet_detected=nosnippet_detected,
            max_snippet=max_snippet_val,
            max_image_preview=max_image_preview_val,
            blocked_reason=blocked_reason,
        )

        # Canonical details
        canonical_tags = self.soup.find_all(
            "link",
            attrs={"rel": lambda x: x and x.lower() == "canonical"}
        )
        multiple_canonicals = len(canonical_tags) > 1
        canonical_tag = canonical_tags[0] if canonical_tags else None
        canon_val = None
        canon_html = None
        canon_css = None
        canon_xpath = None
        canon_is_self_ref = None
        canon_is_relative = None
        if canonical_tag and hasattr(canonical_tag, "get"):
            href = canonical_tag.get("href", "").strip()
            if href:
                canon_is_relative = not href.startswith(("http://", "https://"))
                canon_val = urljoin(self.base_url, href)
                canon_html = str(canonical_tag)
                canon_css = get_css_selector(canonical_tag)
                canon_xpath = get_xpath(canonical_tag)
                # Check self-referencing
                canon_is_self_ref = canon_val.rstrip("/") == self.base_url.rstrip("/")

        # Favicon URL
        favicon_url = self.get_favicon_url()

        # Viewport details
        viewport_tag = self.soup.find(
            "meta",
            attrs={"name": lambda x: x and x.lower() == "viewport"}
        )
        viewport_val = viewport_tag.get("content", "").strip() or None if viewport_tag and hasattr(viewport_tag, "get") else None
        viewport_has_device_width = False
        viewport_allows_scaling = True
        if viewport_val:
            viewport_lower = viewport_val.lower()
            viewport_has_device_width = "width=device-width" in viewport_lower
            if "user-scalable=no" in viewport_lower or "maximum-scale=1" in viewport_lower or "maximum-scale=0" in viewport_lower:
                viewport_allows_scaling = False

        # Lang attribute
        html_tag = self.soup.find("html")
        lang_val = html_tag.get("lang", "").strip() or None if html_tag and hasattr(html_tag, "get") else None

        # Hreflang tags
        hreflang_tags = self.get_hreflang_tags()

        # Pagination links
        pagination_next = None
        pagination_prev = None
        next_link = self.soup.find("link", attrs={"rel": lambda x: x and "next" in x.lower()})
        prev_link = self.soup.find("link", attrs={"rel": lambda x: x and "prev" in x.lower()})
        if next_link and next_link.get("href"):
            pagination_next = urljoin(self.base_url, next_link["href"].strip())
        if prev_link and prev_link.get("href"):
            pagination_prev = urljoin(self.base_url, prev_link["href"].strip())

        # AMP link
        amp_url = None
        amp_link = self.soup.find("link", attrs={"rel": lambda x: x and "amphtml" in x.lower()})
        if amp_link and amp_link.get("href"):
            amp_url = urljoin(self.base_url, amp_link["href"].strip())

        # HTTP-EQUIV meta tags
        http_equiv_tags = {}
        for tag in self.soup.find_all("meta", attrs={"http-equiv": True}):
            equiv = tag.get("http-equiv", "").strip()
            content = tag.get("content", "").strip()
            if equiv and content:
                http_equiv_tags[equiv.lower()] = content

        return PageMetadataModel(
            title=title_val,
            title_html=title_html,
            title_css=title_css,
            title_xpath=title_xpath,
            meta_description=desc_val,
            meta_desc_html=desc_html,
            meta_desc_css=desc_css,
            meta_desc_xpath=desc_xpath,
            meta_robots=robots_val,
            robots_directives=robots_directives,
            x_robots_tag_directives=x_robots_directives,
            canonical_url=canon_val,
            canonical_html=canon_html,
            canonical_css=canon_css,
            canonical_xpath=canon_xpath,
            canonical_is_self_ref=canon_is_self_ref,
            canonical_is_relative=canon_is_relative,
            multiple_canonicals=multiple_canonicals,
            favicon_url=favicon_url,
            viewport=viewport_val,
            viewport_has_device_width=viewport_has_device_width,
            viewport_allows_scaling=viewport_allows_scaling,
            lang=lang_val,
            is_js_rendered=is_js_rendered,
            headings=self.get_headings(),
            open_graph=og_data,
            twitter_cards=self.get_twitter_cards(),
            json_ld=self.get_json_ld(),
            hreflang_tags=hreflang_tags,
            pagination_next=pagination_next,
            pagination_prev=pagination_prev,
            amp_url=amp_url,
            http_equiv_tags=http_equiv_tags,
            indexability=indexability,
        )

    def get_favicon_url(self) -> Optional[str]:
        """Resolves page favicon URL from link tag."""
        for rel_val in ["icon", "shortcut icon", "apple-touch-icon"]:
            icon_tag = self.soup.find(
                "link",
                attrs={"rel": lambda x: x and rel_val in x.lower()}
            )
            if icon_tag and hasattr(icon_tag, "get"):
                href = icon_tag.get("href")
                if href:
                    return urljoin(self.base_url, href.strip())
        return None

    def get_headings(self) -> List[HeadingModel]:
        """Extracts all headings (H1-H6)."""
        headings: List[HeadingModel] = []
        heading_tags = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        for tag in heading_tags:
            try:
                level = int(tag.name[1])
                text = tag.get_text().strip()
                if text:
                    headings.append(HeadingModel(level=level, text=text))
            except (ValueError, IndexError):
                continue
        return headings

    def get_images(self) -> List[ImageModel]:
        """Extracts all <img> tags with full attribute analysis."""
        images: List[ImageModel] = []
        img_tags = self.soup.find_all("img")
        for tag in img_tags:
            src = tag.get("src") or tag.get("data-src") or tag.get("data-lazy-src") or tag.get("data-original")
            if not src:
                continue

            absolute_src = urljoin(self.base_url, src.strip())
            alt = tag.get("alt")

            is_missing = alt is None or alt.strip() == ""
            alt_val = alt.strip() if (alt and alt.strip()) else None
            alt_length = len(alt_val) if alt_val else 0

            # Extract extended attributes
            width = tag.get("width")
            height = tag.get("height")
            loading = tag.get("loading")
            is_lazy = loading == "lazy" or bool(tag.get("data-src") or tag.get("data-lazy-src"))
            decoding = tag.get("decoding")
            srcset = tag.get("srcset")
            sizes = tag.get("sizes")
            fetchpriority = tag.get("fetchpriority")

            # Detect image format
            img_format = self._detect_image_format(absolute_src)
            is_next_gen = img_format in NEXT_GEN_FORMATS if img_format else False

            images.append(
                ImageModel(
                    src=absolute_src,
                    alt=alt_val,
                    is_missing_alt=is_missing,
                    html_snippet=str(tag),
                    css_selector=get_css_selector(tag),
                    xpath=get_xpath(tag),
                    width=width,
                    height=height,
                    loading=loading,
                    is_lazy_loaded=is_lazy,
                    decoding=decoding,
                    srcset=srcset,
                    sizes=sizes,
                    fetchpriority=fetchpriority,
                    format=img_format,
                    is_next_gen_format=is_next_gen,
                    alt_text_length=alt_length,
                )
            )
        return images

    def get_links(self) -> List[LinkModel]:
        """Extracts all valid internal and external <a> links with full attribute analysis."""
        links: List[LinkModel] = []
        seen_urls: set = set()
        a_tags = self.soup.find_all("a")

        for tag in a_tags:
            href = tag.get("href")
            if not href:
                continue

            href_stripped = href.strip()
            is_jump_link = href_stripped.startswith("#") and len(href_stripped) > 1

            if (
                not href_stripped
                or href_stripped.lower().startswith(("javascript:", "mailto:", "tel:", "sms:", "data:"))
            ):
                continue

            # Skip pure jump links (hash-only) from URL tracking but note them
            if href_stripped.startswith("#"):
                continue

            absolute_url = urljoin(self.base_url, href_stripped)

            # Deduplicate by URL
            url_key = absolute_url.split("#")[0]  # Ignore fragment for dedup
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)

            text = tag.get_text().strip()
            if not text:
                # Check for image alt text inside anchor
                img = tag.find("img")
                text = img.get("alt", "").strip() if img else ""
            if not text:
                text = "[Empty Anchor Text]"

            is_internal = is_internal_url(absolute_url, self.base_url)

            # Extract rel attribute
            rel_raw = tag.get("rel")
            rel_val = " ".join(rel_raw) if isinstance(rel_raw, list) else (rel_raw or "")
            rel_lower = rel_val.lower()
            is_nofollow = "nofollow" in rel_lower
            is_sponsored = "sponsored" in rel_lower
            is_ugc = "ugc" in rel_lower

            target = tag.get("target")
            is_self_ref = url_key.rstrip("/") == self.base_url.rstrip("/")

            anchor_type = self._classify_anchor_text(text)
            position = self._classify_link_position(tag)

            links.append(
                LinkModel(
                    url=absolute_url,
                    text=text,
                    is_internal=is_internal,
                    rel=rel_val or None,
                    is_nofollow=is_nofollow,
                    is_sponsored=is_sponsored,
                    is_ugc=is_ugc,
                    target=target,
                    is_self_referencing=is_self_ref,
                    is_jump_link=is_jump_link,
                    anchor_text_type=anchor_type,
                    link_position=position,
                )
            )
        return links

    def get_open_graph(self) -> Dict[str, str]:
        """Extracts Open Graph metadata properties."""
        og_data: Dict[str, str] = {}
        meta_tags = self.soup.find_all("meta")
        for tag in meta_tags:
            if not hasattr(tag, "get"):
                continue
            prop = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if prop and content and prop.lower().startswith("og:"):
                og_data[prop.lower()] = content.strip()
        return og_data

    def get_twitter_cards(self) -> Dict[str, str]:
        """Extracts Twitter Cards metadata properties."""
        twitter_data: Dict[str, str] = {}
        meta_tags = self.soup.find_all("meta")
        for tag in meta_tags:
            if not hasattr(tag, "get"):
                continue
            name = tag.get("name") or tag.get("property")
            content = tag.get("content")
            if name and content and name.lower().startswith("twitter:"):
                twitter_data[name.lower()] = content.strip()
        return twitter_data

    def get_hreflang_tags(self) -> List[HreflangModel]:
        """Extracts hreflang internationalization tags."""
        hreflang_tags = []
        link_tags = self.soup.find_all(
            "link",
            attrs={"rel": lambda x: x and "alternate" in (x if isinstance(x, str) else " ".join(x)).lower()}
        )
        for tag in link_tags:
            if not hasattr(tag, "get"):
                continue
            hreflang = tag.get("hreflang")
            href = tag.get("href")
            if not hreflang or not href:
                continue

            hreflang_lower = hreflang.lower().strip()
            is_x_default = hreflang_lower == "x-default"

            # Parse language and country codes
            parts = hreflang_lower.split("-")
            lang_code = parts[0] if parts else hreflang_lower
            country_code = parts[1] if len(parts) > 1 else None

            target_url = urljoin(self.base_url, href.strip())

            hreflang_tags.append(HreflangModel(
                source_url=self.base_url,
                target_url=target_url,
                language_code=lang_code,
                country_code=country_code,
                is_x_default=is_x_default,
            ))

        return hreflang_tags

    def get_json_ld(self) -> List[JSONLDModel]:
        """Discovers Schema.org JSON-LD script blocks and validates with deep schema analysis."""
        results: List[JSONLDModel] = []
        script_tags = self.soup.find_all("script", attrs={"type": "application/ld+json"})
        for tag in script_tags:
            content = tag.string
            if not content:
                continue

            raw_content = content.strip()
            html_snippet = str(tag)
            css_selector = get_css_selector(tag)
            xpath = get_xpath(tag)

            try:
                data = json.loads(raw_content)
                # Extract schema type(s)
                schema_types = []
                schema_type = None
                validation_errors = []
                warnings = []
                required_missing = []
                recommended_missing = []
                schema_id = None
                google_compatible = False

                if isinstance(data, dict):
                    schema_type = data.get("@type")
                    schema_id = data.get("@id")
                    if schema_type:
                        if isinstance(schema_type, list):
                            schema_types = [str(t) for t in schema_type]
                        else:
                            schema_types = [str(schema_type)]

                    # Validate required properties per schema type
                    google_compatible, required_missing, recommended_missing, validation_errors, warnings = \
                        self._validate_schema(data, schema_type)

                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            t = item["@type"]
                            if isinstance(t, list):
                                schema_types.extend([str(x) for x in t])
                            else:
                                schema_types.append(str(t))

                results.append(
                    JSONLDModel(
                        valid=True,
                        data=raw_content,
                        html_snippet=html_snippet,
                        css_selector=css_selector,
                        xpath=xpath,
                        schema_type=schema_type,
                        schema_types=schema_types,
                        required_properties_missing=required_missing,
                        recommended_properties_missing=recommended_missing,
                        google_rich_results_compatible=google_compatible,
                        validation_errors=validation_errors,
                        warnings=warnings,
                        schema_id=schema_id,
                    )
                )
            except json.JSONDecodeError as err:
                results.append(
                    JSONLDModel(
                        valid=False,
                        data=raw_content,
                        error=f"JSON parsing error: {err}",
                        html_snippet=html_snippet,
                        css_selector=css_selector,
                        xpath=xpath,
                    )
                )
        return results

    def _validate_schema(self, data: dict, schema_type: Optional[str]) -> Tuple[bool, List[str], List[str], List[str], List[str]]:
        """Validate schema.org data against Google Rich Results requirements."""
        required_missing = []
        recommended_missing = []
        validation_errors = []
        warnings = []
        google_compatible = False

        if not schema_type:
            warnings.append("No @type property found")
            return False, required_missing, recommended_missing, validation_errors, warnings

        type_str = str(schema_type).lower() if isinstance(schema_type, str) else ""

        # Google Rich Results required properties per type
        SCHEMA_REQUIREMENTS = {
            "article": {
                "required": ["headline", "image"],
                "recommended": ["author", "datePublished", "description"],
            },
            "newsarticle": {
                "required": ["headline", "image"],
                "recommended": ["author", "datePublished", "dateModified"],
            },
            "blogposting": {
                "required": ["headline", "image"],
                "recommended": ["author", "datePublished", "dateModified"],
            },
            "product": {
                "required": ["name", "image"],
                "recommended": ["description", "offers", "brand"],
            },
            "organization": {
                "required": ["name"],
                "recommended": ["url", "logo", "contactPoint"],
            },
            "localbusiness": {
                "required": ["name", "address"],
                "recommended": ["telephone", "url", "openingHours"],
            },
            "breadcrumblist": {
                "required": ["itemListElement"],
                "recommended": [],
            },
            "faqpage": {
                "required": ["mainEntity"],
                "recommended": [],
            },
            "howto": {
                "required": ["name", "step"],
                "recommended": ["image", "totalTime"],
            },
            "event": {
                "required": ["name", "startDate", "location"],
                "recommended": ["endDate", "description", "image"],
            },
            "recipe": {
                "required": ["name", "image"],
                "recommended": ["author", "cookTime", "nutrition"],
            },
            "videoobject": {
                "required": ["name", "description", "thumbnailUrl"],
                "recommended": ["uploadDate", "duration", "contentUrl"],
            },
            "webpage": {
                "required": ["name"],
                "recommended": ["description", "datePublished"],
            },
            "softwareapplication": {
                "required": ["name", "operatingSystem"],
                "recommended": ["applicationCategory", "offers"],
            },
            "book": {
                "required": ["name"],
                "recommended": ["author", "isbn", "bookFormat"],
            },
            "jobposting": {
                "required": ["title", "description", "datePosted", "hiringOrganization"],
                "recommended": ["validThrough", "employmentType"],
            },
        }

        # Find matching schema type
        req_info = None
        for key, val in SCHEMA_REQUIREMENTS.items():
            if key in type_str:
                req_info = val
                break

        if not req_info:
            warnings.append(f"No Google Rich Results requirements defined for schema type: {schema_type}")
            return google_compatible, required_missing, recommended_missing, validation_errors, warnings

        # Check required properties
        for prop in req_info["required"]:
            if prop not in data:
                required_missing.append(prop)
                validation_errors.append(f"Missing required property: {prop}")

        # Check recommended properties
        for prop in req_info["recommended"]:
            if prop not in data:
                recommended_missing.append(prop)
                warnings.append(f"Missing recommended property: {prop}")

        # Determine Google compatibility
        if not required_missing:
            google_compatible = True

        # Validate @context
        context = data.get("@context", "")
        if context and "schema.org" not in str(context).lower():
            validation_errors.append(f"@context should be 'https://schema.org', found: {context}")

        return google_compatible, required_missing, recommended_missing, validation_errors, warnings
