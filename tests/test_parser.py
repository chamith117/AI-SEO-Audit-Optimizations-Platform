"""Unit tests for the HTML parser module.
"""

from ai_seo_audit.parser import SEOHTMLParser


def test_parser_metadata_extraction():
    """Tests parsing of basic meta tags (Title, Description, Robots, Canonical)."""
    html = """
    <html>
      <head>
        <title>Test Page Title</title>
        <meta name="description" content="This is a test description for SEO.">
        <meta name="robots" content="noindex, nofollow">
        <link rel="canonical" href="/primary-page">
        <link rel="icon" href="/favicon.png">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body lang="en"></body>
    </html>
    """
    parser = SEOHTMLParser(html, base_url="https://example.com/sub/index.html")
    metadata = parser.parse_metadata()

    assert metadata.title == "Test Page Title"
    assert metadata.meta_description == "This is a test description for SEO."
    assert metadata.meta_robots == "noindex, nofollow"
    assert metadata.canonical_url == "https://example.com/primary-page"
    assert metadata.favicon_url == "https://example.com/favicon.png"
    assert metadata.viewport == "width=device-width, initial-scale=1.0"
    # Lang from root html tag is tested separately below; here html has no lang on root, let's see.


def test_parser_lang_on_html():
    """Tests lang extraction from the HTML tag."""
    html = "<html lang='en-US'><head></head><body></body></html>"
    parser = SEOHTMLParser(html, base_url="https://example.com")
    metadata = parser.parse_metadata()
    assert metadata.lang == "en-US"


def test_parser_social_tags():
    """Tests parsing of Open Graph and Twitter Card tags."""
    html = """
    <html>
      <head>
        <meta property="og:title" content="OG Title">
        <meta property="og:description" content="OG Description">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Twitter Title">
      </head>
      <body></body>
    </html>
    """
    parser = SEOHTMLParser(html, base_url="https://example.com")
    og = parser.get_open_graph()
    tw = parser.get_twitter_cards()

    assert og["og:title"] == "OG Title"
    assert og["og:description"] == "OG Description"
    assert tw["twitter:card"] == "summary_large_image"
    assert tw["twitter:title"] == "Twitter Title"


def test_parser_json_ld():
    """Tests parsing and validation of JSON-LD script blocks."""
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "WebSite",
          "name": "Test Site"
        }
        </script>
        <script type="application/ld+json">
        {
          invalid json here
        }
        </script>
      </head>
      <body></body>
    </html>
    """
    parser = SEOHTMLParser(html, base_url="https://example.com")
    blocks = parser.get_json_ld()

    assert len(blocks) == 2
    # First block is valid
    assert blocks[0].valid
    assert "WebSite" in blocks[0].data

    # Second block is invalid
    assert not blocks[0].error
    assert not blocks[1].valid
    assert "JSON parsing error" in blocks[1].error
    assert blocks[1].html_snippet is not None
