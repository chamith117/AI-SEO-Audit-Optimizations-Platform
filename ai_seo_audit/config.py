"""Configuration schemas and TOML file loader for the AI SEO Audit Toolkit.
"""

from pathlib import Path
from typing import Optional
import tomllib
from pydantic import BaseModel, Field

from ai_seo_audit.utils import logger


class CrawlConfig(BaseModel):
    """Configuration for the website crawler."""
    max_pages: int = Field(50, ge=1, description="Maximum pages to crawl")
    max_depth: int = Field(3, ge=0, description="Maximum crawl depth limit")
    user_agent: str = Field("AI-SEO-Audit-Toolkit/1.0", description="User-Agent string")
    timeout: int = Field(10, ge=1, description="Connection and read timeout in seconds")
    max_size: int = Field(5242880, ge=0, description="Maximum file size in bytes to download")
    verify_ssl: bool = Field(True, description="Verify SSL certs")
    js_render: bool = Field(False, description="Use Playwright to render JavaScript (SPA/CSR pages)")


class AuditConfig(BaseModel):
    """Configuration for page audits and link checks."""
    check_links: bool = Field(True, description="Enable broken link checking")
    check_images: bool = Field(True, description="Enable broken image checking")
    max_workers: int = Field(10, ge=1, description="Thread pool size for concurrent validation")


class OutputConfig(BaseModel):
    """Configuration for report export locations."""
    json_path: Optional[str] = Field("reports/seo_report.json", description="JSON export path")
    html_path: Optional[str] = Field("reports/seo_report.html", description="HTML export path")
    pdf_path: Optional[str] = Field("reports/seo_report.pdf", description="PDF export path")
    csv_path: Optional[str] = Field("reports/seo_report.csv", description="CSV export path")


class SEOAuditConfig(BaseModel):
    """Master SEO Audit Toolkit configuration model."""
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(config_path: Optional[str] = None) -> SEOAuditConfig:
    """Loads configuration from a TOML file.

    If no file is specified, looks for 'seoaudit.toml' in the current working directory.
    Falls back to default settings if no configuration file is located.

    Args:
        config_path: Optional filepath to the configuration TOML.

    Returns:
        SEOAuditConfig: Parsed configuration object.
    """
    path_to_load = None
    
    if config_path:
        path_to_load = Path(config_path)
    else:
        # Check standard default path
        default_path = Path("seoaudit.toml")
        if default_path.is_file():
            path_to_load = default_path

    if not path_to_load or not path_to_load.is_file():
        logger.debug("No configuration file found. Using default configurations.")
        return SEOAuditConfig()

    try:
        with open(path_to_load, "rb") as f:
            data = tomllib.load(f)
        
        # Load and validate utilizing Pydantic
        config = SEOAuditConfig(**data)
        logger.info(f"Loaded configuration settings from: {path_to_load}")
        return config
    except Exception as e:
        logger.error(f"Failed to parse config file '{path_to_load}'. Error: {e}. Using defaults.")
        return SEOAuditConfig()
