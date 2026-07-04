"""Utility functions and logging configuration for AI SEO Audit Toolkit.
"""

import logging
from urllib.parse import urlparse
import urllib3
from rich.logging import RichHandler

# Suppress SSL validation warnings when verify=False is used in audits
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ai_seo_audit")


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configures and returns the logger for the toolkit.

    Uses RichHandler for structured, beautiful terminal output.

    Args:
        verbose: If True, set logging level to DEBUG. Otherwise, INFO.

    Returns:
        logging.Logger: The configured logger instance.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Reset existing handlers to prevent duplicate messages
    logger.handlers.clear()
    logger.setLevel(level)

    handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


def is_valid_url(url: str) -> bool:
    """Validates if a URL string is well-formed with a scheme and netloc.

    Args:
        url: The URL string to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False


def get_domain(url: str) -> str:
    """Extracts the netloc domain from a URL.

    Args:
        url: The URL string.

    Returns:
        str: The domain name (e.g. 'example.com'), or empty string if invalid.
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def is_internal_url(url: str, base_url: str) -> bool:
    """Checks if a URL is internal relative to a base URL.

    Args:
        url: The URL string to check.
        base_url: The base URL of the site being audited.

    Returns:
        bool: True if the URL is internal or relative, False if it is external.
    """
    if not url:
        return False
    
    # Relative URLs are internal by default
    if url.startswith("/") or url.startswith("./") or url.startswith("../"):
        return True

    # If it is a relative path but doesn't start with / (e.g. 'about.html')
    if not urlparse(url).scheme:
        return True

    base_domain = get_domain(base_url)
    target_domain = get_domain(url)

    # Check if target domain is subdomain or same domain as base
    return target_domain == base_domain or target_domain.endswith("." + base_domain)


def get_css_selector(element) -> str:
    """Generates a unique CSS selector path for a BeautifulSoup element.

    Args:
        element: A BeautifulSoup Tag object.

    Returns:
        str: CSS selector query string.
    """
    if not element or element.name == "[document]":
        return ""
    
    path = []
    current = element
    while current and current.name != "[document]":
        name = current.name
        # Use element ID if present for shorter path anchor
        element_id = current.get("id")
        if element_id and isinstance(element_id, str):
            path.insert(0, f"{name}#{element_id}")
            break
        else:
            siblings = current.parent.find_all(name, recursive=False) if current.parent else []
            if len(siblings) > 1:
                index = siblings.index(current) + 1
                path.insert(0, f"{name}:nth-of-type({index})")
            else:
                path.insert(0, name)
        current = current.parent
    
    return " > ".join(path)


def get_xpath(element) -> str:
    """Generates a standard XPath path for a BeautifulSoup element.

    Args:
        element: A BeautifulSoup Tag object.

    Returns:
        str: XPath query string.
    """
    if not element or element.name == "[document]":
        return ""
    
    path = []
    current = element
    while current and current.name != "[document]":
        name = current.name
        siblings = current.parent.find_all(name, recursive=False) if current.parent else []
        if len(siblings) > 1:
            index = siblings.index(current) + 1
            path.insert(0, f"{name}[{index}]")
        else:
            path.insert(0, name)
        current = current.parent
    
    return "/" + "/".join(path)

