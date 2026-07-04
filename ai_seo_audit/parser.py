"""HTML Parser for extracting page contents, metadata, social tags, viewport, lang, and JSON-LD blocks.
"""

import json
from typing import List, Optional, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from ai_seo_audit.models import (
    PageMetadataModel,
    HeadingModel,
    ImageModel,
    LinkModel,
    JSONLDModel
)
from ai_seo_audit.utils import (
    is_internal_url,
    get_css_selector,
    get_xpath
)


class SEOHTMLParser:
    """Parses HTML content to extract core SEO and metadata elements, including social and Schema markup."""

    def __init__(self, html_content: str, base_url: str):
        """Initializes the parser.

        Args:
            html_content: Raw HTML text of the page.
            base_url: The absolute base URL (final crawl URL) to resolve relative links.
        """
        self.soup = BeautifulSoup(html_content, "lxml")
        self.base_url = base_url

    def parse_metadata(self) -> PageMetadataModel:
        """Extracts standard page level SEO meta elements, social elements, and JSON-LD validations.

        Returns:
            PageMetadataModel: The parsed metadata structure.
        """
        # Title tag details
        title_tag = self.soup.find("title")
        title_val = title_tag.get_text().strip() if title_tag else None
        title_html = str(title_tag) if title_tag else None
        title_css = get_css_selector(title_tag) if title_tag else None
        title_xpath = get_xpath(title_tag) if title_tag else None

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

        # Meta robots
        meta_robots = self.soup.find(
            "meta",
            attrs={"name": lambda x: x and x.lower() == "robots"}
        )
        robots_val = meta_robots.get("content", "").strip() or None if meta_robots and hasattr(meta_robots, "get") else None

        # Canonical details
        canonical_tag = self.soup.find(
            "link",
            attrs={"rel": lambda x: x and x.lower() == "canonical"}
        )
        canon_val = None
        canon_html = None
        canon_css = None
        canon_xpath = None
        if canonical_tag and hasattr(canonical_tag, "get"):
            href = canonical_tag.get("href")
            if href:
                canon_val = urljoin(self.base_url, href.strip())
                canon_html = str(canonical_tag)
                canon_css = get_css_selector(canonical_tag)
                canon_xpath = get_xpath(canonical_tag)

        # Favicon URL
        favicon_url = self.get_favicon_url()

        # Viewport details
        viewport_tag = self.soup.find(
            "meta",
            attrs={"name": lambda x: x and x.lower() == "viewport"}
        )
        viewport_val = viewport_tag.get("content", "").strip() or None if viewport_tag and hasattr(viewport_tag, "get") else None

        # Lang attribute
        html_tag = self.soup.find("html")
        lang_val = html_tag.get("lang", "").strip() or None if html_tag and hasattr(html_tag, "get") else None

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
            canonical_url=canon_val,
            canonical_html=canon_html,
            canonical_css=canon_css,
            canonical_xpath=canon_xpath,
            favicon_url=favicon_url,
            viewport=viewport_val,
            lang=lang_val,
            headings=self.get_headings(),
            open_graph=self.get_open_graph(),
            twitter_cards=self.get_twitter_cards(),
            json_ld=self.get_json_ld()
        )

    def get_favicon_url(self) -> Optional[str]:
        """Resolves page favicon URL from link tag.

        Returns:
            Optional[str]: Absolute favicon URL, or None.
        """
        icon_tag = self.soup.find(
            "link",
            attrs={"rel": lambda x: x and x.lower() in ("icon", "shortcut icon")}
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
        """Extracts all <img> tags and analyzes their ALT attributes, capturing selector paths."""
        images: List[ImageModel] = []
        img_tags = self.soup.find_all("img")
        for tag in img_tags:
            src = tag.get("src")
            if not src:
                continue
            
            absolute_src = urljoin(self.base_url, src.strip())
            alt = tag.get("alt")
            
            # Alt attribute is missing or contains only whitespace
            is_missing = alt is None or alt.strip() == ""
            alt_val = alt.strip() if (alt and alt.strip()) else None
            
            images.append(
                ImageModel(
                    src=absolute_src,
                    alt=alt_val,
                    is_missing_alt=is_missing,
                    html_snippet=str(tag),
                    css_selector=get_css_selector(tag),
                    xpath=get_xpath(tag)
                )
            )
        return images

    def get_links(self) -> List[LinkModel]:
        """Extracts all valid internal and external <a> links."""
        links: List[LinkModel] = []
        seen_urls = set()
        a_tags = self.soup.find_all("a")
        
        for tag in a_tags:
            href = tag.get("href")
            if not href:
                continue
            
            href_stripped = href.strip()
            if (
                not href_stripped
                or href_stripped.startswith("#")
                or href_stripped.lower().startswith(("javascript:", "mailto:", "tel:", "sms:", "data:"))
            ):
                continue

            absolute_url = urljoin(self.base_url, href_stripped)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            text = tag.get_text().strip() or "[Empty Anchor Text]"
            is_internal = is_internal_url(absolute_url, self.base_url)

            links.append(
                LinkModel(
                    url=absolute_url,
                    text=text,
                    is_internal=is_internal
                )
            )
        return links

    def get_open_graph(self) -> Dict[str, str]:
        """Extracts Open Graph metadata properties.

        Returns:
            Dict[str, str]: Map of property names (e.g. 'og:title') to their content value.
        """
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
        """Extracts Twitter Cards metadata properties.

        Returns:
            Dict[str, str]: Map of twitter tag names to content values.
        """
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

    def get_json_ld(self) -> List[JSONLDModel]:
        """Discovers Schema.org JSON-LD script blocks and validates their JSON format.

        Returns:
            List[JSONLDModel]: List of structured schema blocks and their parse status.
        """
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
                # Attempt to parse json
                json.loads(raw_content)
                results.append(
                    JSONLDModel(
                        valid=True,
                        data=raw_content,
                        html_snippet=html_snippet,
                        css_selector=css_selector,
                        xpath=xpath
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
                        xpath=xpath
                    )
                )
        return results
