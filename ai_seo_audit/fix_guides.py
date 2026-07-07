"""Comprehensive fix guides for every SEO issue type with step-by-step instructions, code examples, and CMS-specific guidance.
"""

from typing import Dict, List, Optional


class FixGuide:
    """Represents a detailed fix guide for an SEO issue."""

    def __init__(
        self,
        issue_type: str,
        title: str,
        severity: str,
        what_is_it: str,
        why_it_matters: str,
        how_to_fix: List[str],
        code_examples: Dict[str, str],
        cms_guides: Dict[str, List[str]],
        verification_steps: List[str],
        priority: str = "medium",
    ):
        self.issue_type = issue_type
        self.title = title
        self.severity = severity
        self.what_is_it = what_is_it
        self.why_it_matters = why_it_matters
        self.how_to_fix = how_to_fix
        self.code_examples = code_examples
        self.cms_guides = cms_guides
        self.verification_steps = verification_steps
        self.priority = priority


# ============================================================
# COMPLETE FIX GUIDE DATABASE
# ============================================================

FIX_GUIDES: Dict[str, FixGuide] = {

    # =====================================================
    # HTTPS & SECURITY
    # =====================================================
    "HTTPS Security": FixGuide(
        issue_type="HTTPS Security",
        title="Page Not Using HTTPS",
        severity="CRITICAL",
        what_is_it="Your page is served over unencrypted HTTP instead of secure HTTPS. Browsers show 'Not Secure' warning to visitors.",
        why_it_matters="Google confirmed HTTPS is a ranking signal. Chrome flags HTTP sites as 'Not Secure', killing user trust. 84% of users abandon a purchase if the connection isn't secure.",
        how_to_fix=[
            "1. Purchase and install an SSL certificate (free options: Let's Encrypt, Cloudflare)",
            "2. Configure your web server to serve all pages over HTTPS",
            "3. Set up 301 redirects from HTTP to HTTPS for ALL pages",
            "4. Update internal links to use HTTPS URLs",
            "5. Update your sitemap.xml to use HTTPS URLs",
            "6. Set the canonical URL to HTTPS version",
            "7. Enable HSTS (HTTP Strict Transport Security) header",
            "8. Update Google Search Console and Bing Webmaster Tools",
        ],
        code_examples={
            "Nginx": """server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com www.example.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Enable HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}""",
            "Apache": """<VirtualHost *:80>
    ServerName example.com
    Redirect permanent / https://example.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName example.com
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    
    # Enable HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</VirtualHost>""",
            "Cloudflare": "1. Go to SSL/TLS → Overview → Set to 'Full (Strict)'\n2. Go to SSL/TLS → Edge Certificates → Enable 'Always Use HTTPS'\n3. Enable HSTS with max-age of at least 6 months",
        },
        cms_guides={
            "WordPress": [
                "1. Install 'Really Simple SSL' plugin",
                "2. Go to Settings → General → Change WordPress Address and Site Address to https://",
                "3. Run the SSL setup wizard",
                "4. Enable 'Force SSL' in plugin settings",
            ],
            "Shopify": [
                "1. Go to Online Store → Preferences",
                "2. Enable 'Force SSL for all pages' (Settings → Domains)",
                "3. Shopify provides free SSL automatically",
            ],
            "Wix": [
                "1. Go to Settings → Domains",
                "2. Click on your domain → Enable SSL",
                "3. Wix provides free SSL automatically",
            ],
            "Squarespace": [
                "1. Go to Settings → Advanced → SSL",
                "2. Set to 'Secure and HSTS Enabled'",
                "3. Squarespace provides free SSL automatically",
            ],
        },
        verification_steps=[
            "Visit the page in Chrome — look for the lock icon",
            "Check that HTTP redirects to HTTPS automatically",
            "Use https://httpstatus.io to verify redirect chain",
            "Test with SSL Labs: https://www.ssllabs.com/ssltest/",
        ],
        priority="critical",
    ),

    # =====================================================
    # TITLE TAGS
    # =====================================================
    "Missing Title": FixGuide(
        issue_type="Missing Title",
        title="Missing Title Tag",
        severity="CRITICAL",
        what_is_it="The page has no <title> tag in the HTML <head>. This is the most important on-page SEO element.",
        why_it_matters="The title tag is the #1 on-page ranking factor. It appears as the clickable headline in search results. Without it, Google cannot determine what your page is about.",
        how_to_fix=[
            "1. Add a unique <title> tag inside the <head> section of your HTML",
            "2. Make it 30-65 characters long (Google truncates after ~60 chars)",
            "3. Include your primary keyword near the beginning",
            "4. Make it descriptive and compelling for users",
            "5. Ensure each page has a unique title",
            "6. For JS-rendered pages, ensure title is in the initial HTML (use SSR/SSG)",
        ],
        code_examples={
            "HTML": """<head>
    <title>Your Primary Keyword - Secondary Keyword | Brand Name</title>
</head>""",
            "Next.js (SSR)": """// pages/_document.js or app/layout.js
export const metadata = {
    title: 'Your Primary Keyword | Brand Name',
}""",
            "React (Client-Side)": """// Use react-helmet
import { Helmet } from 'react-helmet';

function Page() {
    return (
        <Helmet>
            <title>Your Primary Keyword | Brand Name</title>
        </Helmet>
    );
}""",
        },
        cms_guides={
            "WordPress": [
                "1. Install Yoast SEO or Rank Math plugin",
                "2. Edit the page/post → Scroll to SEO section",
                "3. Enter the SEO title",
                "4. Or edit theme: Appearance → Theme Editor → header.php",
            ],
            "Shopify": [
                "1. Go to Online Store → Pages (or Products)",
                "2. Click on the page → Edit",
                "3. Scroll to 'Search engine listing preview' → Click 'Edit website SEO'",
                "4. Enter the Page title",
            ],
            "Wix": [
                "1. Go to Pages → Click on the page",
                "2. Click the SEO icon (Google 'G')",
                "3. Enter the SEO title under 'Title Tag'",
            ],
            "Squarespace": [
                "1. Go to Pages → Click on the page",
                "2. Click the gear icon (Settings)",
                "3. Go to SEO → Enter the SEO Title",
            ],
            "HTML Static": [
                "1. Open the HTML file in a text editor",
                "2. Find the <head> section",
                "3. Add: <title>Your Title Here</title>",
                "4. Save and upload the file",
            ],
        },
        verification_steps=[
            "View page source (Ctrl+U) — check for <title> tag",
            "Use browser DevTools → Elements → search for <title>",
            "Run the audit again to confirm the issue is resolved",
        ],
        priority="critical",
    ),

    "Title Too Short": FixGuide(
        issue_type="Title Too Short",
        title="Title Tag Too Short",
        severity="WARNING",
        what_is_it="Your title tag has fewer than 10 characters. Very short titles waste valuable SEO real estate.",
        why_it_matters="Short titles miss keyword opportunities. Google allocates ~60 characters for titles in search results — using only a few words means lost ranking potential.",
        how_to_fix=[
            "1. Expand the title to 30-65 characters",
            "2. Include the primary keyword and a descriptive modifier",
            "3. Add your brand name at the end",
            "4. Make it compelling for users to click",
        ],
        code_examples={
            "Before": "<title>Home</title>",
            "After": "<title>Best Organic Coffee Beans Online | FreshRoast Co.</title>",
        },
        cms_guides={
            "WordPress": "Edit the page → Scroll to Yoast/Rank Math SEO section → Expand the title",
            "Shopify": "Edit the page → Scroll to 'Search engine listing preview' → Edit website SEO → Update title",
        },
        verification_steps=["Check title length is 30-65 characters", "Include primary keyword"],
        priority="high",
    ),

    "Title Too Long": FixGuide(
        issue_type="Title Too Long",
        title="Title Tag Too Long",
        severity="WARNING",
        what_is_it=f"Your title tag exceeds 65 characters. Google will truncate it in search results, cutting off important information.",
        why_it_matters="Truncated titles look unprofessional in search results and may lose important keywords or brand name. Users may not click if they can't see what the page is about.",
        how_to_fix=[
            "1. Shorten the title to 60 characters or fewer",
            "2. Put the most important keywords first",
            "3. Move brand name to the end or remove if space is tight",
            "4. Remove unnecessary words or separators",
        ],
        code_examples={
            "Before": "<title>Best Organic Fair Trade Single Origin Coffee Beans Online Store - Buy Fresh Roasted Premium Coffee | FreshRoast Company</title>",
            "After": "<title>Best Organic Coffee Beans Online | FreshRoast</title>",
        },
        cms_guides={
            "WordPress": "Edit the page → Yoast/Rank Math SEO section → Shorten the SEO title field",
            "Shopify": "Edit the page → Search engine listing preview → Edit → Shorten title",
        },
        verification_steps=["Count characters — should be 60 or fewer", "Check in Google search results preview"],
        priority="high",
    ),

    "Title Special Characters": FixGuide(
        issue_type="Title Special Characters",
        title="Title Contains Special Characters",
        severity="INFO",
        what_is_it="Your title contains non-ASCII characters (emojis, symbols, special letters) that may not display correctly in search results.",
        why_it_matters="Special characters can cause encoding issues, display as garbled text, and waste title character space.",
        how_to_fix=[
            "1. Replace special characters with standard ASCII equivalents",
            "2. Use text instead of emojis in titles",
            "3. Ensure proper UTF-8 encoding in your HTML",
        ],
        code_examples={
            "Before": "<title>Café ☕ Best Coffee</title>",
            "After": "<title>Best Coffee - Cafe FreshRoast</title>",
        },
        cms_guides={"WordPress": "Edit the page → Update the title to remove special characters"},
        verification_steps=["Check title contains only standard ASCII characters"],
        priority="low",
    ),

    # =====================================================
    # META DESCRIPTIONS
    # =====================================================
    "Missing Meta Description": FixGuide(
        issue_type="Missing Meta Description",
        title="Missing Meta Description",
        severity="CRITICAL",
        what_is_it="The page has no meta description tag. This means Google will auto-generate a snippet from your page content.",
        why_it_matters="Meta descriptions control your search result snippet. A compelling description can increase click-through rates by 5-30%. Without one, Google may show irrelevant text.",
        how_to_fix=[
            "1. Add a <meta name='description'> tag in the <head> section",
            "2. Write 50-160 characters (Google truncates after ~155 chars)",
            "3. Include your primary keyword naturally",
            "4. Write a compelling summary that entices clicks",
            "5. Make each page's description unique",
            "6. For JS-rendered pages, ensure meta description is in initial HTML",
        ],
        code_examples={
            "HTML": """<head>
    <meta name="description" content="Shop the best organic coffee beans online. Free shipping on orders over $30. Fresh roasted, ethically sourced, 100% satisfaction guaranteed.">
</head>""",
            "Next.js": """// app/layout.js or pages/_document.js
export const metadata = {
    description: 'Shop the best organic coffee beans online. Free shipping on orders over $30.',
}""",
        },
        cms_guides={
            "WordPress": [
                "1. Install Yoast SEO or Rank Math plugin",
                "2. Edit the page → Scroll to SEO section",
                "3. Enter the meta description (120-155 chars recommended)",
            ],
            "Shopify": [
                "1. Edit the page/product",
                "2. Scroll to 'Search engine listing preview' → Edit website SEO",
                "3. Enter the Description field",
            ],
            "Wix": [
                "1. Click the page → SEO icon (Google 'G')",
                "2. Enter description under 'Meta Description'",
            ],
            "Squarespace": [
                "1. Page Settings → SEO → SEO Description",
            ],
        },
        verification_steps=[
            "View page source — search for meta name='description'",
            "Use Google SERP simulator to preview",
            "Run audit again to verify",
        ],
        priority="critical",
    ),

    "Meta Description Too Short": FixGuide(
        issue_type="Meta Description Too Short",
        title="Meta Description Too Short",
        severity="WARNING",
        what_is_it="Your meta description is under 50 characters. Short descriptions waste SEO opportunity.",
        why_it_matters="Short descriptions don't provide enough context for users or search engines. You're missing keyword opportunities and click-through rate optimization.",
        how_to_fix=[
            "1. Expand to 120-155 characters",
            "2. Include a call-to-action (Shop, Learn, Get, Discover)",
            "3. Add primary and secondary keywords naturally",
            "4. Highlight unique value propositions",
        ],
        code_examples={
            "Before": '<meta name="description" content="Coffee store.">',
            "After": '<meta name="description" content="Shop premium organic coffee beans online. Free shipping, fresh roasted weekly, 100% satisfaction guaranteed. Order now!">',
        },
        cms_guides={"WordPress": "Edit page → Yoast/Rank Math → Expand the meta description"},
        verification_steps=["Count characters — should be 120-155", "Check it reads naturally"],
        priority="high",
    ),

    "Meta Description Too Long": FixGuide(
        issue_type="Meta Description Too Long",
        title="Meta Description Too Long",
        severity="WARNING",
        what_is_it="Your meta description exceeds 160 characters and will be truncated in search results.",
        why_it_matters="Truncated descriptions cut off mid-sentence, looking unprofessional and losing click-through rate.",
        how_to_fix=[
            "1. Shorten to 155 characters or fewer",
            "2. Put the most important information first",
            "3. Remove redundant words",
        ],
        code_examples={
            "Before": '<meta name="description" content="We are the best organic coffee store in the world with the freshest beans sourced from over 50 different countries around the globe and we ship free on orders over $30 to anywhere in the United States and Canada.">',
            "After": '<meta name="description" content="Shop premium organic coffee beans. Free shipping on orders over $30. Fresh roasted, ethically sourced from 50+ countries.">',
        },
        cms_guides={"WordPress": "Edit page → Yoast/Rank Math → Shorten meta description"},
        verification_steps=["Count characters — should be 155 or fewer"],
        priority="high",
    ),

    # =====================================================
    # CANONICAL URL
    # =====================================================
    "Missing Canonical URL": FixGuide(
        issue_type="Missing Canonical URL",
        title="Missing Canonical Tag",
        severity="CRITICAL",
        what_is_it="The page has no canonical link tag. Without it, search engines may index duplicate versions of this page.",
        why_it_matters="Canonical tags tell Google which version of a page to index. Without them, duplicate pages split your ranking signals, diluting your SEO authority.",
        how_to_fix=[
            "1. Add <link rel='canonical' href='URL'> in the <head> section",
            "2. The canonical URL should be the full absolute URL of this page",
            "3. Use HTTPS version as canonical",
            "4. Make sure it points to the same page (self-referencing)",
            "5. Ensure trailing slash consistency",
        ],
        code_examples={
            "HTML": """<head>
    <link rel="canonical" href="https://example.com/page-url">
</head>""",
            "WordPress Plugin": "Yoast SEO automatically adds canonical tags. Verify in SEO → Search Appearance.",
            "Redirects": "If page redirects, canonical should point to the final destination URL.",
        },
        cms_guides={
            "WordPress": [
                "1. Install Yoast SEO (auto-adds canonical)",
                "2. Or edit → Yoast → Advanced → Canonical URL",
            ],
            "Shopify": [
                "1. Shopify auto-adds canonical tags",
                "2. Verify in Online Store → Themes → Edit code → search 'canonical'",
            ],
            "Wix": [
                "1. Go to Pages → SEO → Advanced SEO",
                "2. Add canonical tag in the 'Additional Tags' field",
            ],
        },
        verification_steps=[
            "View page source — search for rel='canonical'",
            "Canonical URL should match the current page URL",
            "Use Ahrefs or Screaming Frog to verify",
        ],
        priority="critical",
    ),

    "Canonical Mismatch": FixGuide(
        issue_type="Canonical Mismatch",
        title="Canonical URL Mismatch",
        severity="WARNING",
        what_is_it="The canonical URL points to a different page than the current one. This may be intentional (cross-domain canonical) or an error.",
        why_it_matters="If the canonical points to the wrong page, Google may not index this page at all, or may give credit to the wrong URL.",
        how_to_fix=[
            "1. Verify the canonical target is correct",
            "2. If this is the primary page, change canonical to self-referencing",
            "3. If this is a duplicate, the cross-domain canonical may be correct",
            "4. Ensure canonical URL uses HTTPS and correct domain",
        ],
        code_examples={
            "Self-Referencing": '<link rel="canonical" href="https://example.com/current-page">',
            "Cross-Domain": '<link rel="canonical" href="https://www.example.com/current-page">',
        },
        cms_guides={"WordPress": "Edit page → Yoast → Advanced → Set correct canonical URL"},
        verification_steps=["Verify canonical URL matches the intended target", "Check for protocol mismatch"],
        priority="high",
    ),

    "Canonical Relative URL": FixGuide(
        issue_type="Canonical Relative URL",
        title="Canonical Uses Relative URL",
        severity="WARNING",
        what_is_it="The canonical href uses a relative path (/page) instead of an absolute URL (https://example.com/page).",
        why_it_matters="Relative URLs may be interpreted incorrectly by search engines, leading to wrong canonicalization.",
        how_to_fix=[
            "1. Change canonical href to use full absolute URL",
            "2. Include the protocol (https://) and domain",
        ],
        code_examples={
            "Before": '<link rel="canonical" href="/about">',
            "After": '<link rel="canonical" href="https://example.com/about">',
        },
        cms_guides={"WordPress": "Yoast SEO auto-generates absolute canonical URLs. Check Settings → General → WordPress Address."},
        verification_steps=["Canonical href should start with http:// or https://"],
        priority="high",
    ),

    "Canonical Protocol Mismatch": FixGuide(
        issue_type="Canonical Protocol Mismatch",
        title="HTTPS Canonical on HTTP Page",
        severity="WARNING",
        what_is_it="The page is served over HTTP but the canonical URL points to the HTTPS version.",
        why_it_matters="This can confuse search engines about which version to index.",
        how_to_fix=[
            "1. Set up proper HTTP to HTTPS redirects",
            "2. Ensure the page is served over HTTPS",
            "3. The canonical and page URL should use the same protocol",
        ],
        code_examples={"Fix": "Set up 301 redirect: HTTP → HTTPS, then canonical will match automatically."},
        cms_guides={"WordPress": "Install Really Simple SSL plugin to handle HTTP→HTTPS redirects automatically."},
        verification_steps=["Page should be served over HTTPS", "Canonical URL should use HTTPS"],
        priority="high",
    ),

    "Multiple Canonical Tags": FixGuide(
        issue_type="Multiple Canonical Tags",
        title="Multiple Canonical Tags Found",
        severity="CRITICAL",
        what_is_it="The page contains more than one <link rel='canonical'> tag. Search engines may ignore all of them.",
        why_it_matters="Multiple canonicals create confusion — Google doesn't know which one to trust and may ignore them entirely.",
        how_to_fix=[
            "1. Remove all duplicate canonical tags",
            "2. Keep only one canonical tag per page",
            "3. Ensure it's self-referencing (points to the current page)",
            "4. Check for plugins or templates adding extra canonicals",
        ],
        code_examples={"Correct": '<link rel="canonical" href="https://example.com/current-page">  <!-- Only ONE -->'},
        cms_guides={
            "WordPress": [
                "1. Check for conflicting SEO plugins (only use one)",
                "2. Disable canonical in theme if Yoast/Rank Math already adds it",
                "3. Check functions.php for manual canonical additions",
            ],
        },
        verification_steps=["View source — search for rel='canonical' — should find exactly 1"],
        priority="critical",
    ),

    # =====================================================
    # VIEWPORT & MOBILE
    # =====================================================
    "Missing Viewport Tag": FixGuide(
        issue_type="Missing Viewport Tag",
        title="Missing Viewport Meta Tag",
        severity="CRITICAL",
        what_is_it="The page is missing the viewport meta tag, making it non-responsive on mobile devices.",
        why_it_matters="Google uses mobile-first indexing. Without a viewport tag, your site won't render correctly on phones, leading to poor mobile rankings and high bounce rates.",
        how_to_fix=[
            "1. Add the viewport meta tag in the <head> section",
            "2. Use width=device-width, initial-scale=1.0",
            "3. Test on mobile devices and Google's Mobile-Friendly Test",
        ],
        code_examples={
            "HTML": '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "WordPress": "Most themes include this. Check header.php for the viewport tag.",
        },
        cms_guides={
            "WordPress": "Check Appearance → Theme Editor → header.php for viewport meta tag",
            "Shopify": "Shopify themes include this by default. Check theme.liquid",
            "Wix": "Wix sites are mobile-responsive by default",
            "Squarespace": "Squarespace sites are mobile-responsive by default",
        },
        verification_steps=[
            "View page source — search for viewport",
            "Test at https://search.google.com/test/mobile-friendly",
            "Resize browser window — page should adapt",
        ],
        priority="critical",
    ),

    "Viewport Missing Device Width": FixGuide(
        issue_type="Viewport Missing Device Width",
        title="Viewport Missing width=device-width",
        severity="WARNING",
        what_is_it="The viewport tag exists but doesn't include width=device-width, so the page won't properly adapt to screen sizes.",
        why_it_matters="Without device-width, the page renders at a fixed width (usually 980px) on mobile, requiring zooming and scrolling.",
        how_to_fix=[
            "1. Update the viewport content to include width=device-width",
            "2. Keep initial-scale=1.0",
        ],
        code_examples={
            "Before": '<meta name="viewport" content="width=980">',
            "After": '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        },
        cms_guides={"WordPress": "Edit header.php → Find and update the viewport meta tag"},
        verification_steps=["Viewport content should contain 'width=device-width'"],
        priority="high",
    ),

    "Viewport Blocks User Scaling": FixGuide(
        issue_type="Viewport Blocks User Scaling",
        title="Viewport Prevents User Scaling",
        severity="WARNING",
        what_is_it="The viewport tag includes user-scalable=no or maximum-scale=1, preventing users from zooming in.",
        why_it_matters="This hurts accessibility for visually impaired users and may violate WCAG guidelines. Google may penalize sites that block zooming.",
        how_to_fix=[
            "1. Remove user-scalable=no from viewport content",
            "2. Set maximum-scale to at least 2",
        ],
        code_examples={
            "Before": '<meta name="viewport" content="width=device-width, user-scalable=no">',
            "After": '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        },
        cms_guides={"WordPress": "Edit header.php → Remove user-scalable=no from viewport tag"},
        verification_steps=["Viewport should not contain user-scalable=no or maximum-scale=1"],
        priority="high",
    ),

    # =====================================================
    # HEADINGS
    # =====================================================
    "Missing H1 Heading": FixGuide(
        issue_type="Missing H1 Heading",
        title="Missing H1 Heading",
        severity="CRITICAL",
        what_is_it="The page has no H1 heading tag. Every page should have exactly one H1 that describes the main topic.",
        why_it_matters="H1 is the most important heading signal for search engines. It tells Google what the page is about. Pages without H1s rank lower.",
        how_to_fix=[
            "1. Add exactly one <h1> tag to the page",
            "2. Include the primary keyword in the H1",
            "3. Make it descriptive of the page's main topic",
            "4. Place it near the top of the content",
            "5. Ensure it's different from the title tag (but related)",
        ],
        code_examples={
            "HTML": """<body>
    <h1>Best Organic Coffee Beans for Home Brewing</h1>
    <p>Discover our premium selection...</p>
</body>""",
        },
        cms_guides={
            "WordPress": [
                "1. Edit the page/post",
                "2. The main heading in the editor is typically the H1",
                "3. Or add: <h1>Your Heading</h1> in the content",
            ],
            "Shopify": [
                "1. Edit the page",
                "2. The page title is usually the H1",
                "3. Check theme settings for heading structure",
            ],
            "Wix": [
                "1. Add a Heading element",
                "2. Set it to H1 style",
                "3. Place it at the top of the page content",
            ],
            "Squarespace": [
                "1. Add a Text block",
                "2. Select 'Heading 1' from the format dropdown",
                "3. Enter your heading text",
            ],
        },
        verification_steps=[
            "View page source — search for <h1>",
            "Use browser DevTools → search for h1",
            "Should find exactly ONE h1 tag per page",
        ],
        priority="critical",
    ),

    "Multiple H1 Headings": FixGuide(
        issue_type="Multiple H1 Headings",
        title="Multiple H1 Headings Found",
        severity="WARNING",
        what_is_it="The page has multiple <h1> tags. Best practice is exactly one H1 per page.",
        why_it_matters="Multiple H1s confuse search engines about the page's main topic. Each H1 dilutes the keyword focus.",
        how_to_fix=[
            "1. Keep only ONE H1 — the main topic heading",
            "2. Change other H1s to H2 or H3",
            "3. Maintain proper heading hierarchy: H1 > H2 > H3",
        ],
        code_examples={
            "Before": "<h1>Coffee</h1>...<h1>Beans</h1>",
            "After": "<h1>Best Organic Coffee Beans</h1>...<h2>Our Selection</h2>",
        },
        cms_guides={"WordPress": "Edit the page → Change extra H1 tags to H2 using the heading dropdown in the block editor"},
        verification_steps=["Should have exactly ONE <h1> per page"],
        priority="high",
    ),

    "Heading Hierarchy Skip": FixGuide(
        issue_type="Heading Hierarchy Skip",
        title="Heading Level Skipped",
        severity="INFO",
        what_is_it="The page skips heading levels (e.g., H1 directly to H3 without H2).",
        why_it_matters="Proper heading hierarchy helps screen readers and search engines understand content structure.",
        how_to_fix=[
            "1. Use heading levels sequentially: H1 > H2 > H3 > H4",
            "2. Don't skip levels (e.g., don't go from H1 to H3)",
        ],
        code_examples={
            "Before": "<h1>Title</h1>...<h3>Subsection</h3>",
            "After": "<h1>Title</h1>...<h2>Subsection</h2>",
        },
        cms_guides={"WordPress": "Edit the page → Use the block editor heading dropdown to set proper levels"},
        verification_steps=["Heading levels should follow sequential order"],
        priority="low",
    ),

    # =====================================================
    # FAVICON
    # =====================================================
    "Missing Favicon": FixGuide(
        issue_type="Missing Favicon",
        title="Missing Favicon",
        severity="WARNING",
        what_is_it="No favicon (website icon) is defined in the page header. This is the small icon shown in browser tabs.",
        why_it_matters="Favicons build brand recognition and trust. Missing favicons look unprofessional and browsers may show a generic icon.",
        how_to_fix=[
            "1. Create a favicon.ico file (16x16 or 32x32 pixels)",
            "2. Also create apple-touch-icon.png (180x180) for iOS",
            "3. Add link tags in the <head> section",
            "4. Place favicon files in the website root directory",
        ],
        code_examples={
            "HTML": """<head>
    <link rel="icon" href="/favicon.ico" sizes="32x32">
    <link rel="icon" href="/icon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
</head>""",
        },
        cms_guides={
            "WordPress": [
                "1. Go to Appearance → Customize → Site Identity",
                "2. Upload a Site Icon (favicon)",
            ],
            "Shopify": [
                "1. Go to Online Store → Themes → Customize",
                "2. Theme Settings → Favicon → Upload image",
            ],
            "Wix": [
                "1. Go to Settings → Favicon",
                "2. Upload your favicon image",
            ],
            "Squarespace": [
                "1. Go to Design → Browser Icon (Favicon)",
                "2. Upload your favicon image",
            ],
        },
        verification_steps=[
            "Check browser tab for the favicon",
            "View source — search for rel='icon'",
            "Verify favicon.ico is accessible at https://example.com/favicon.ico",
        ],
        priority="medium",
    ),

    # =====================================================
    # LANG ATTRIBUTE
    # =====================================================
    "Missing Lang Attribute": FixGuide(
        issue_type="Missing Lang Attribute",
        title="Missing HTML Lang Attribute",
        severity="WARNING",
        what_is_it="The <html> tag is missing the lang attribute. This tells search engines and screen readers what language the page is in.",
        why_it_matters="Lang attribute helps Google serve the right language version in search results. It's also critical for accessibility (screen readers).",
        how_to_fix=[
            "1. Add lang attribute to the <html> tag",
            "2. Use ISO 639-1 language codes (en, es, fr, de, etc.)",
            "3. Optionally add country code (en-US, en-GB, pt-BR)",
        ],
        code_examples={
            "Before": "<html>",
            "After": '<html lang="en">',
            "Spanish": '<html lang="es">',
            "Portuguese (Brazil)": '<html lang="pt-BR">',
        },
        cms_guides={
            "WordPress": [
                "1. Go to Settings → General → Site Language",
                "2. Or edit header.php → Add lang to <html> tag",
            ],
            "Shopify": "Shopify auto-adds lang attribute based on store language settings",
            "Wix": "Wix auto-adds lang attribute based on site language",
        },
        verification_steps=[
            "View page source — check <html> tag has lang attribute",
            "Should match the primary language of the page content",
        ],
        priority="medium",
    ),

    # =====================================================
    # OPEN GRAPH & TWITTER
    # =====================================================
    "Missing Open Graph Tags": FixGuide(
        issue_type="Missing Open Graph Tags",
        title="Missing Open Graph Tags",
        severity="WARNING",
        what_is_it="The page is missing Open Graph (og:) meta tags that control how it appears when shared on social media (Facebook, LinkedIn, etc.).",
        why_it_matters="Without OG tags, social media platforms auto-generate previews that may be wrong or unattractive, reducing social engagement.",
        how_to_fix=[
            "1. Add og:title, og:description, and og:image tags",
            "2. Add og:url (should match canonical URL)",
            "3. Add og:type (website, article, product, etc.)",
            "4. og:image should be at least 1200x630 pixels",
            "5. Use absolute URLs for all OG properties",
        ],
        code_examples={
            "HTML": """<head>
    <meta property="og:title" content="Best Organic Coffee Beans Online">
    <meta property="og:description" content="Shop premium organic coffee beans. Free shipping on orders over $30.">
    <meta property="og:image" content="https://example.com/images/og-image.jpg">
    <meta property="og:url" content="https://example.com/coffee-beans">
    <meta property="og:type" content="product">
    <meta property="og:site_name" content="FreshRoast Coffee">
</head>""",
        },
        cms_guides={
            "WordPress": [
                "1. Install Yoast SEO (auto-adds OG tags)",
                "2. Edit page → Yoast → Social → Set OG image",
            ],
            "Shopify": [
                "1. Edit the page/product",
                "2. Scroll to 'Search engine listing preview' → Add social sharing image",
            ],
        },
        verification_steps=[
            "Use Facebook Sharing Debugger: https://developers.facebook.com/tools/debug/",
            "Use LinkedIn Post Inspector: https://www.linkedin.com/post-inspector/",
            "View source — search for og:",
        ],
        priority="medium",
    ),

    "Missing Twitter Cards": FixGuide(
        issue_type="Missing Twitter Cards",
        title="Missing Twitter Card Tags",
        severity="WARNING",
        what_is_it="The page is missing Twitter Card meta tags (twitter:card, twitter:title) that control how it appears when shared on Twitter/X.",
        why_it_matters="Without Twitter cards, shared links appear as plain URLs without images or descriptions, reducing engagement on Twitter/X.",
        how_to_fix=[
            "1. Add twitter:card, twitter:title, twitter:description, twitter:image",
            "2. Use summary_large_image card type for best visibility",
            "3. Use absolute URLs for twitter:image",
        ],
        code_examples={
            "HTML": """<head>
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Best Organic Coffee Beans Online">
    <meta name="twitter:description" content="Shop premium organic coffee beans. Free shipping over $30.">
    <meta name="twitter:image" content="https://example.com/images/twitter-card.jpg">
</head>""",
        },
        cms_guides={"WordPress": "Install Yoast SEO → Social → Twitter tab → Enable Twitter card meta data"},
        verification_steps=["Use Twitter Card Validator: https://cards-dev.twitter.com/validator"],
        priority="medium",
    ),

    "OG URL Invalid": FixGuide(
        issue_type="OG URL Invalid",
        title="og:url is Not Absolute URL",
        severity="WARNING",
        what_is_it="The og:url property contains a relative URL instead of a full absolute URL.",
        why_it_matters="Social platforms require absolute URLs to properly attribute shares and track engagement.",
        how_to_fix=[
            "1. Change og:url to use the full absolute URL",
            "2. Include https:// protocol",
            "3. Match the canonical URL",
        ],
        code_examples={"Before": '<meta property="og:url" content="/about">', "After": '<meta property="og:url" content="https://example.com/about">'},
        cms_guides={"WordPress": "Yoast SEO auto-generates absolute og:url. Check Settings → General."},
        verification_steps=["og:url should start with https://"],
        priority="medium",
    ),

    # =====================================================
    # STRUCTURED DATA
    # =====================================================
    "Invalid JSON-LD": FixGuide(
        issue_type="Invalid JSON-LD",
        title="Invalid JSON-LD Structured Data",
        severity="CRITICAL",
        what_is_it="The page contains JSON-LD structured data with JSON syntax errors. Search engines cannot parse it.",
        why_it_matters="Invalid structured data means your page won't get rich results (stars, FAQs, recipes, etc.) in Google search.",
        how_to_fix=[
            "1. Find the JSON-LD script block in the page source",
            "2. Copy the JSON content and paste into a JSON validator",
            "3. Fix syntax errors (missing commas, quotes, brackets)",
            "4. Use Google Rich Results Test to validate",
            "5. Consider using a structured data plugin/generator",
        ],
        code_examples={
            "Invalid": """<script type="application/ld+json">
{
    "@context": "https://schema.org"
    "@type": "Article"  // Missing comma above
    "headline": "Title"
}
</script>""",
            "Valid": """<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Title"
}
</script>""",
        },
        cms_guides={
            "WordPress": [
                "1. Install 'Schema Pro' or 'Rank Math' plugin",
                "2. Go to the plugin settings to generate valid schema",
                "3. Test with Google Rich Results Test",
            ],
        },
        verification_steps=[
            "Validate at https://search.google.com/test/rich-results",
            "Validate at https://validator.schema.org/",
            "Check for JSON syntax errors in browser console",
        ],
        priority="critical",
    ),

    "Schema Missing Required Properties": FixGuide(
        issue_type="Schema Missing Required Properties",
        title="Schema Missing Required Properties",
        severity="WARNING",
        what_is_it="The structured data is valid JSON but missing required properties for the schema type to qualify for Google Rich Results.",
        why_it_matters="Without required properties, Google won't display rich results for your page even though the schema is technically valid.",
        how_to_fix=[
            "1. Check what properties are required for your schema type",
            "2. Add all required properties to the JSON-LD",
            "3. Also add recommended properties for better rich results",
            "4. Test with Google Rich Results Test",
        ],
        code_examples={
            "Article": """Required: headline, image
Recommended: author, datePublished, description

{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Article Title",
    "image": "https://example.com/image.jpg",
    "author": {"@type": "Organization", "name": "Brand"},
    "datePublished": "2024-01-01",
    "description": "Article description"
}""",
        },
        cms_guides={"WordPress": "Use Rank Math or Schema Pro plugin — they auto-add required properties."},
        verification_steps=["Test at https://search.google.com/test/rich-results"],
        priority="high",
    ),

    # =====================================================
    # IMAGES
    # =====================================================
    "Missing Alt Text": FixGuide(
        issue_type="Missing Alt Text",
        title="Image Missing Alt Text",
        severity="WARNING",
        what_is_it="An image on the page is missing the alt attribute or it's empty. Alt text describes the image for screen readers and search engines.",
        why_it_matters="Alt text is required for accessibility (ADA/WCAG compliance). Google uses alt text to understand images and rank them in image search. Missing alt text = missed image SEO traffic.",
        how_to_fix=[
            "1. Add descriptive alt text to every image",
            "2. Include relevant keywords naturally (don't keyword stuff)",
            "3. Keep alt text under 125 characters",
            "4. For decorative images, use alt='' (empty) with role='presentation'",
            "5. For complex images (charts), add longer description nearby",
        ],
        code_examples={
            "Before": '<img src="coffee-beans.jpg">',
            "After": '<img src="coffee-beans.jpg" alt="Organic Arabica coffee beans from Colombia">',
            "Decorative": '<img src="decorative-border.png" alt="" role="presentation">',
        },
        cms_guides={
            "WordPress": [
                "1. Edit the post/page",
                "2. Click on the image → Click the block settings (gear icon)",
                "3. Enter 'Alt Text' in the field",
            ],
            "Shopify": [
                "1. Edit the product/page",
                "2. Click on the image",
                "3. Enter 'Image alt text'",
            ],
            "Wix": [
                "1. Click on the image → Settings",
                "2. Enter 'Alt Text' field",
            ],
            "Squarespace": [
                "1. Click on the image → Edit",
                "2. Enter 'Alt Text'",
            ],
        },
        verification_steps=[
            "View page source — search for <img> without alt",
            "Use WAVE accessibility tool: https://wave.webaim.org/",
            "Run the audit again to verify",
        ],
        priority="high",
    ),

    "Image Missing Dimensions": FixGuide(
        issue_type="Image Missing Dimensions",
        title="Image Missing Width/Height (CLS)",
        severity="WARNING",
        what_is_it="Images don't have width and height attributes, causing Cumulative Layout Shift (CLS) as images load.",
        why_it_matters="CLS is a Core Web Vital metric. Layout shifts frustrate users and Google penalizes pages with high CLS in rankings.",
        how_to_fix=[
            "1. Add width and height attributes to all <img> tags",
            "2. Match the actual image dimensions",
            "3. Use CSS to set display dimensions if needed",
            "4. Consider using aspect-ratio CSS property",
        ],
        code_examples={
            "Before": '<img src="hero.jpg">',
            "After": '<img src="hero.jpg" width="1200" height="630">',
            "With CSS": '<img src="hero.jpg" width="1200" height="630" style="width:100%;height:auto">',
        },
        cms_guides={
            "WordPress": "Most modern themes add dimensions automatically. If not, install 'CLS Image Fix' plugin.",
            "Shopify": "Shopify themes typically include image dimensions. Check theme.liquid.",
        },
        verification_steps=["All <img> tags should have width and height attributes", "Test CLS at https://pagespeed.web.dev/"],
        priority="high",
    ),

    "Images Not Next-Gen Format": FixGuide(
        issue_type="Images Not Next-Gen Format",
        title="Images Not Using WebP/AVIF Format",
        severity="INFO",
        what_is_it="All images use legacy formats (JPEG, PNG) instead of modern formats like WebP or AVIF.",
        why_it_matters="WebP images are 25-35% smaller than JPEG/PNG at the same quality. AVIF is even smaller. Smaller images = faster pages = better rankings.",
        how_to_fix=[
            "1. Convert images to WebP format (preferred) or AVIF",
            "2. Use <picture> element for browser fallback",
            "3. Use CDNs that auto-convert images (Cloudflare, Imgix, Cloudinary)",
            "4. Install WordPress plugins for auto-conversion",
        ],
        code_examples={
            "HTML": """<picture>
    <source srcset="image.webp" type="image/webp">
    <source srcset="image.avif" type="image/avif">
    <img src="image.jpg" alt="Description">
</picture>""",
        },
        cms_guides={
            "WordPress": [
                "1. Install 'ShortPixel' or 'Imagify' plugin",
                "2. Enable WebP generation in settings",
                "3. Enable automatic <picture> tag output",
            ],
        },
        verification_steps=["Check images in browser DevTools → Network tab for format", "Use https://webpcheck.com/"],
        priority="medium",
    ),

    "Images Missing Lazy Loading": FixGuide(
        issue_type="Images Missing Lazy Loading",
        title="Images Missing Lazy Loading",
        severity="INFO",
        what_is_it="Below-the-fold images don't use lazy loading, causing them all to load immediately on page load.",
        why_it_matters="Lazy loading delays off-screen image loading, improving initial page load time and Core Web Vitals scores.",
        how_to_fix=[
            "1. Add loading='lazy' to below-the-fold images",
            "2. Don't lazy load above-the-fold (hero) images",
            "3. Consider using native browser lazy loading",
        ],
        code_examples={
            "Lazy Load": '<img src="image.jpg" loading="lazy" alt="Description">',
            "No Lazy (Above Fold)": '<img src="hero.jpg" loading="eager" alt="Hero Image">',
        },
        cms_guides={
            "WordPress": [
                "1. WordPress 5.5+ has native lazy loading",
                "2. For more control, use 'Lazy Load' plugin by WP Rocket",
            ],
        },
        verification_steps=["Below-fold images should have loading='lazy'", "Above-fold images should have loading='eager'"],
        priority="medium",
    ),

    # =====================================================
    # LINKS
    # =====================================================
    "Internal Nofollow Links": FixGuide(
        issue_type="Internal Nofollow Links",
        title="Internal Links Using Nofollow",
        severity="WARNING",
        what_is_it="Internal links use rel='nofollow', preventing PageRank from flowing to those pages.",
        why_it_matters="Internal nofollow wastes link equity. Unlike external links, internal links should pass authority to help your own pages rank.",
        how_to_fix=[
            "1. Remove rel='nofollow' from internal links",
            "2. Only use nofollow for login pages, admin areas, or paid links",
            "3. Use robots.txt to block pages you don't want crawled instead",
        ],
        code_examples={
            "Before": '<a href="/about" rel="nofollow">About Us</a>',
            "After": '<a href="/about">About Us</a>',
        },
        cms_guides={
            "WordPress": [
                "1. Check your SEO plugin settings — some add nofollow automatically",
                "2. Edit the post → Click the link → Edit → Remove nofollow",
            ],
        },
        verification_steps=["Internal links should not have rel='nofollow'"],
        priority="high",
    ),

    "Generic Anchor Text": FixGuide(
        issue_type="Generic Anchor Text",
        title="Generic Anchor Text Detected",
        severity="INFO",
        what_is_it="Links use generic anchor text like 'click here', 'read more', 'learn more' instead of descriptive text.",
        why_it_matters="Descriptive anchor text helps search engines understand the linked page's topic. Generic anchors miss keyword opportunities.",
        how_to_fix=[
            "1. Replace generic anchors with descriptive text",
            "2. Include keywords related to the destination page",
            "3. Make it clear what the user will find",
        ],
        code_examples={
            "Before": '<a href="/blog/coffee-tips">Click Here</a>',
            "After": '<a href="/blog/coffee-tips">Read our coffee brewing tips guide</a>',
        },
        cms_guides={"WordPress": "Edit the post → Select the link text → Change to descriptive text"},
        verification_steps=["All link text should describe the destination"],
        priority="medium",
    ),

    "Empty Anchor Text": FixGuide(
        issue_type="Empty Anchor Text",
        title="Links With No Anchor Text",
        severity="WARNING",
        what_is_it="Links have no visible text content. Screen readers and search engines can't determine the link's purpose.",
        why_it_matters="Empty links are an accessibility violation and provide no SEO value. Users can't tell where they lead.",
        how_to_fix=[
            "1. Add descriptive text between <a> and </a>",
            "2. If the link wraps an image, add alt text to the image",
            "3. For icon links, add aria-label",
        ],
        code_examples={
            "Text Link": '<a href="/about">About Our Company</a>',
            "Image Link": '<a href="/about"><img src="logo.png" alt="About Us"></a>',
            "Icon Link": '<a href="/cart" aria-label="Shopping Cart"><svg>...</svg></a>',
        },
        cms_guides={"WordPress": "Edit the post → Click on the link → Add text content"},
        verification_steps=["All links should have visible text or aria-label"],
        priority="high",
    ),

    "Links Missing noopener": FixGuide(
        issue_type="Links Missing noopener",
        title="Links Missing rel=noopener",
        severity="INFO",
        what_is_it="Links with target='_blank' don't include rel='noopener', creating a security vulnerability.",
        why_it_matters="Without noopener, the opened page can access the original page via window.opener, enabling phishing attacks.",
        how_to_fix=[
            "1. Add rel='noopener' to all target='_blank' links",
            "2. Or use rel='noopener noreferrer' for maximum security",
        ],
        code_examples={
            "Before": '<a href="https://external.com" target="_blank">Link</a>',
            "After": '<a href="https://external.com" target="_blank" rel="noopener noreferrer">Link</a>',
        },
        cms_guides={"WordPress": "Modern browsers add noopener automatically. For older browsers, use 'WP Security' plugin."},
        verification_steps=["All target='_blank' links should have rel='noopener'"],
        priority="low",
    ),

    # =====================================================
    # INDEXABILITY
    # =====================================================
    "Noindex Detected": FixGuide(
        issue_type="Noindex Detected",
        title="Page Has Noindex Directive",
        severity="WARNING",
        what_is_it="The page has a noindex directive (via meta robots or x-robots-tag header), telling search engines not to index it.",
        why_it_matters="Noindex pages won't appear in search results. This may be intentional (admin pages) or accidental (blocking important pages).",
        how_to_fix=[
            "1. If the page SHOULD be indexed: Remove the noindex directive",
            "2. If the page should NOT be indexed: noindex is correct",
            "3. Check both meta robots tag AND x-robots-tag header",
        ],
        code_examples={
            "Remove Noindex": 'Change <meta name="robots" content="noindex"> to <meta name="robots" content="index">',
        },
        cms_guides={
            "WordPress": [
                "1. Edit the page → Scroll to Yoast/Rank Math section",
                "2. Check 'Allow search engines to show this Post in search results'",
            ],
            "Shopify": [
                "1. Edit the page → Search engine listing preview",
                "2. Uncheck 'Page has a Noindex tag' if present",
            ],
        },
        verification_steps=["Check meta robots tag for 'noindex'", "Check X-Robots-Tag response header"],
        priority="high",
    ),

    "Nofollow Directive Detected": FixGuide(
        issue_type="Nofollow Directive Detected",
        title="Page Has Nofollow Directive",
        severity="WARNING",
        what_is_it="The page has a nofollow meta robots directive, preventing PageRank from flowing through any links on this page.",
        why_it_matters="Nofollow on the page level means ALL outgoing links on this page don't pass any link equity.",
        how_to_fix=[
            "1. Remove nofollow from meta robots unless specifically needed",
            "2. Use nofollow on individual links instead of page-wide",
        ],
        code_examples={"Remove": 'Change <meta name="robots" content="nofollow"> to remove or change to "follow"'},
        cms_guides={"WordPress": "Edit page → Yoast → Advanced → Remove nofollow from robots meta"},
        verification_steps=["Page should not have nofollow in meta robots"],
        priority="high",
    ),

    "Nosnippet Detected": FixGuide(
        issue_type="Nosnippet Detected",
        title="Page Has Nosnippet Directive",
        severity="INFO",
        what_is_it="The page has nosnippet directive, preventing Google from showing a snippet in search results.",
        why_it_matters="Without a snippet, search results show your page with no description, reducing click-through rate.",
        how_to_fix=[
            "1. Remove nosnippet from meta robots if you want Google to show a snippet",
            "2. Add a compelling meta description instead",
        ],
        code_examples={"Remove": 'Change <meta name="robots" content="nosnippet"> to remove it'},
        cms_guides={"WordPress": "Edit page → Yoast → Advanced → Remove nosnippet"},
        verification_steps=["Page should not have nosnippet in meta robots"],
        priority="medium",
    ),

    # =====================================================
    # PERFORMANCE
    # =====================================================
    "Slow Response Time": FixGuide(
        issue_type="Slow Response Time",
        title="Slow Server Response Time",
        severity="WARNING",
        what_is_it="The page took over 3 seconds to respond. Slow response times hurt user experience and rankings.",
        why_it_matters="Google uses page speed as a ranking factor. Every 1-second delay reduces conversions by 7%. Slow pages get fewer crawls from Googlebot.",
        how_to_fix=[
            "1. Enable server-side caching (Redis, Memcached, Varnish)",
            "2. Use a CDN (Cloudflare, AWS CloudFront, Fastly)",
            "3. Optimize database queries",
            "4. Upgrade hosting if on shared hosting",
            "5. Enable Gzip/Brotli compression",
            "6. Use PHP 8+ if on WordPress",
        ],
        code_examples={
            "Nginx Caching": """location ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}""",
            "Cloudflare": "Enable Caching Level: Standard, Browser Cache TTL: 1 month",
        },
        cms_guides={
            "WordPress": [
                "1. Install WP Rocket or W3 Total Cache plugin",
                "2. Enable page caching and browser caching",
                "3. Use a managed WordPress host (Kinsta, WP Engine, Cloudways)",
                "4. Install a CDN plugin",
            ],
        },
        verification_steps=["Test at https://pagespeed.web.dev/", "Check TTFB should be under 200ms"],
        priority="high",
    ),

    "High TTFB": FixGuide(
        issue_type="High TTFB",
        title="High Time To First Byte",
        severity="INFO",
        what_is_it="Time to First Byte is over 1 second. This measures how long the server takes to start sending data.",
        why_it_matters="High TTFB indicates server-side performance issues. Google recommends TTFB under 200ms.",
        how_to_fix=[
            "1. Enable server-side caching",
            "2. Use a CDN to serve content from edge locations",
            "3. Optimize server-side code and database",
            "4. Consider upgrading hosting infrastructure",
        ],
        code_examples={"General": "Enable OPcache for PHP, Redis for database caching, CDN for static assets"},
        cms_guides={"WordPress": "Install WP Rocket → Enable server-side caching. Consider switching to a faster host."},
        verification_steps=["TTFB should be under 200ms", "Test at https://web.dev/ttfb/"],
        priority="medium",
    ),

    "Large Page Size": FixGuide(
        issue_type="Large Page Size",
        title="HTML Page Size Too Large",
        severity="WARNING",
        what_is_it="The HTML page size exceeds 1MB, making it slow to download and parse.",
        why_it_matters="Large pages take longer to download, especially on mobile networks. This hurts Core Web Vitals and user experience.",
        how_to_fix=[
            "1. Minify HTML output",
            "2. Remove unnecessary comments and whitespace",
            "3. Reduce inline CSS and JavaScript",
            "4. Defer non-critical scripts",
            "5. Use server-side caching",
        ],
        code_examples={"Minify": "Enable HTML minification in your caching plugin or build pipeline"},
        cms_guides={"WordPress": "Install WP Rocket → Enable HTML minification. Remove unused plugins."},
        verification_steps=["HTML size should be under 1MB", "Check in browser DevTools → Network tab"],
        priority="high",
    ),

    # =====================================================
    # DEPTH & ARCHITECTURE
    # =====================================================
    "Deep Page Depth": FixGuide(
        issue_type="Deep Page Depth",
        title="Page Too Deep in Site Architecture",
        severity="WARNING",
        what_is_it="This page is more than 3 clicks from the homepage. Important pages should be easily accessible.",
        why_it_matters="Deep pages get crawled less frequently by Googlebot and receive less link equity from the homepage. Users also struggle to find deep content.",
        how_to_fix=[
            "1. Add internal links from higher-level pages",
            "2. Create a logical navigation structure (homepage > category > page)",
            "3. Add breadcrumbs for better navigation",
            "4. Include important pages in the main navigation",
            "5. Add related content links",
        ],
        code_examples={"Breadcrumbs": "<!-- Use BreadcrumbList schema -->\nHome > Category > Current Page"},
        cms_guides={
            "WordPress": [
                "1. Install 'Yoast SEO' for breadcrumb functionality",
                "2. Or use 'Flexible Breadcrumbs' plugin",
                "3. Add breadcrumbs to single.php or page.php template",
            ],
        },
        verification_steps=["Page should be reachable within 3 clicks from homepage", "Check with Screaming Frog crawl depth report"],
        priority="high",
    ),

    # =====================================================
    # REDIRECTS
    # =====================================================
    "Redirect Loop": FixGuide(
        issue_type="Redirect Loop",
        title="Redirect Loop Detected",
        severity="CRITICAL",
        what_is_it="The page is stuck in a circular redirect chain where URL A redirects to B, which redirects back to A.",
        why_it_matters="Redirect loops prevent users and search engines from accessing the page. Google will drop the page from its index.",
        how_to_fix=[
            "1. Identify the redirect chain using a redirect checker tool",
            "2. Remove the circular redirect",
            "3. Ensure redirects point to a final destination, not another redirect",
            "4. Check .htaccess, nginx config, and plugins for conflicting redirects",
        ],
        code_examples={"Check": "Use https://.redirect-checker.org/ to trace the full redirect chain"},
        cms_guides={
            "WordPress": [
                "1. Deactivate all plugins temporarily",
                "2. Check .htaccess for conflicting rules",
                "3. Go to Settings → Permalinks → Save (regenerates .htaccess)",
                "4. Re-enable plugins one by one to find the conflict",
            ],
        },
        verification_steps=["Redirect chain should not contain the same URL twice", "Final URL should return 200 status"],
        priority="critical",
    ),

    "Too Many Redirects": FixGuide(
        issue_type="Too Many Redirects",
        title="Too Many Redirects in Chain",
        severity="WARNING",
        what_is_it="The page has more than 3 redirects in the chain. Each redirect adds latency.",
        why_it_matters="Each redirect adds 100-300ms of latency. Long chains waste crawl budget and hurt user experience.",
        how_to_fix=[
            "1. Consolidate redirects to point directly to the final URL",
            "2. Update internal links to use the final URL",
            "3. Fix the source of the redirect chain",
        ],
        code_examples={"Before": "A → B → C → D (3 redirects)", "After": "A → D (1 redirect)"},
        cms_guides={"WordPress": "Use 'Redirection' plugin to manage and consolidate redirects"},
        verification_steps=["Keep redirect chains under 3 hops"],
        priority="high",
    ),

    # =====================================================
    # STATUS CODES
    # =====================================================
    "Soft 404 Detected": FixGuide(
        issue_type="Soft 404 Detected",
        title="Soft 404 Detected",
        severity="CRITICAL",
        what_is_it="The page returns HTTP 200 status but the content appears to be an error page (404-like content).",
        why_it_matters="Soft 404s waste Google's crawl budget and confuse search engines. They may index error pages as real content.",
        how_to_fix=[
            "1. If the page doesn't exist: Return proper 404 or 410 status code",
            "2. If the page exists: Remove error-related content",
            "3. Set up proper redirects for moved pages",
            "4. Check your custom 404 page configuration",
        ],
        code_examples={"Nginx": "location /old-page { return 410; }"},
        cms_guides={
            "WordPress": [
                "1. Check if the page truly exists in the database",
                "2. If deleted, ensure 404 template is working",
                "3. Install 'Redirection' plugin to set up proper redirects",
            ],
        },
        verification_steps=["Page should return correct status code", "Content should match the status code"],
        priority="critical",
    ),

    "Server Error": FixGuide(
        issue_type="Server Error",
        title="Server Error (5xx)",
        severity="CRITICAL",
        what_is_it="The page returned a 5xx server error (500, 502, 503, etc.). The server failed to process the request.",
        why_it_matters="5xx errors mean your page is completely unavailable. Google will eventually drop these pages from its index.",
        how_to_fix=[
            "1. Check server error logs for the specific error",
            "2. Check if PHP/database is working",
            "3. Increase PHP memory limit if needed",
            "4. Check for fatal errors in code",
            "5. Contact hosting provider if server is down",
        ],
        code_examples={"WordPress": "Add to wp-config.php: define('WP_DEBUG', true); define('WP_DEBUG_LOG', true);"},
        cms_guides={
            "WordPress": [
                "1. Check wp-content/debug.log for errors",
                "2. Increase memory: define('WP_MEMORY_LIMIT', '256M');",
                "3. Deactivate all plugins, re-enable one by one",
                "4. Switch to default theme temporarily",
            ],
        },
        verification_steps=["Page should return 200 status code", "Check server error logs"],
        priority="critical",
    ),

    "Page Not Found": FixGuide(
        issue_type="Page Not Found",
        title="404 Page Not Found",
        severity="CRITICAL",
        what_is_it="The page returns HTTP 404 — it doesn't exist on the server.",
        why_it_matters="404 pages provide no value to users or search engines. If other sites link to this URL, you're losing link equity.",
        how_to_fix=[
            "1. If the page moved: Set up a 301 redirect to the new URL",
            "2. If the page was deleted: Create a custom 404 page or 410 response",
            "3. Fix any broken internal links pointing to this URL",
            "4. Submit a sitemap update to Google Search Console",
        ],
        code_examples={"Redirect": "301 Redirect: Old URL → New URL"},
        cms_guides={
            "WordPress": [
                "1. Install 'Redirection' plugin",
                "2. Add redirect from old URL to new URL",
                "3. Set HTTP response code to 301",
            ],
        },
        verification_steps=["Page should return 200 status", "All internal links should point to valid pages"],
        priority="critical",
    ),

    "Access Forbidden": FixGuide(
        issue_type="Access Forbidden",
        title="403 Access Forbidden",
        severity="WARNING",
        what_is_it="The page returns HTTP 403 Forbidden — the server understands the request but refuses to authorize it.",
        why_it_matters="403 errors may block search engine crawlers from accessing your content.",
        how_to_fix=[
            "1. Check file permissions (should be 644 for files, 755 for directories)",
            "2. Check .htaccess for deny rules",
            "3. Check if IP blocking is enabled",
            "4. Verify the page is not password-protected",
        ],
        code_examples={"Permissions": "chmod 644 page.html\nchmod 755 directory/"},
        cms_guides={"WordPress": "Check .htaccess for 'Deny from all' rules. Verify file permissions in hosting control panel."},
        verification_steps=["Page should be accessible to crawlers", "Check robots.txt doesn't block the page"],
        priority="high",
    ),

    # =====================================================
    # ORPHAN PAGES
    # =====================================================
    "Orphan Pages": FixGuide(
        issue_type="Orphan Pages",
        title="Orphan Pages Detected",
        severity="WARNING",
        what_is_it="Pages found in sitemap.xml that have no internal links pointing to them from crawled pages.",
        why_it_matters="Orphan pages receive no link equity and are rarely crawled by search engines. They're essentially invisible to your site's link structure.",
        how_to_fix=[
            "1. Add internal links to orphan pages from relevant content",
            "2. Include orphan pages in navigation menus",
            "3. Add them to related content sections",
            "4. If pages are obsolete, remove from sitemap or redirect",
        ],
        code_examples={"Link": "Add contextual internal links within your content to the orphan pages"},
        cms_guides={
            "WordPress": [
                "1. Edit relevant posts/pages",
                "2. Add internal links to the orphan pages",
                "3. Consider adding a 'Related Pages' section",
            ],
        },
        verification_steps=["Every page in sitemap should have at least one internal link", "Check with Screaming Frog 'Orphan Pages' report"],
        priority="high",
    ),

    # =====================================================
    # DUPLICATE CONTENT
    # =====================================================
    "Duplicate Page Title": FixGuide(
        issue_type="Duplicate Page Title",
        title="Duplicate Page Titles",
        severity="WARNING",
        what_is_it="Multiple pages share the same title tag. This confuses search engines about which page to rank.",
        why_it_matters="Duplicate titles dilute your ranking potential. Google can't determine which page is most relevant for a given search.",
        how_to_fix=[
            "1. Write unique, descriptive titles for each page",
            "2. Include page-specific keywords in each title",
            "3. Add modifiers (guide, 2024, best, review) to differentiate",
        ],
        code_examples={"Before": "Both pages: 'Our Products'", "After": "Page 1: 'Organic Coffee Beans | Our Products'  Page 2: 'Coffee Brewing Equipment | Our Products'"},
        cms_guides={"WordPress": "Edit each page → Update the SEO title to be unique"},
        verification_steps=["Each page should have a unique title tag"],
        priority="high",
    ),

    "Duplicate Meta Description": FixGuide(
        issue_type="Duplicate Meta Description",
        title="Duplicate Meta Descriptions",
        severity="WARNING",
        what_is_it="Multiple pages share the same meta description.",
        why_it_matters="Duplicate descriptions mean missed opportunities to differentiate your pages in search results.",
        how_to_fix=[
            "1. Write unique meta descriptions for each page",
            "2. Each should summarize the specific page content",
            "3. Include different keywords per page",
        ],
        code_examples={"Rule": "Every indexable page needs a unique meta description"},
        cms_guides={"WordPress": "Edit each page → Update the meta description in Yoast/Rank Math"},
        verification_steps=["Each page should have a unique meta description"],
        priority="high",
    ),

    "Duplicate Page Content": FixGuide(
        issue_type="Duplicate Page Content",
        title="Duplicate Page Content",
        severity="WARNING",
        what_is_it="Multiple pages have identical or near-identical content based on title + meta description hash.",
        why_it_matters="Duplicate content splits ranking signals. Google may choose the wrong page to index.",
        how_to_fix=[
            "1. Create unique content for each page",
            "2. Set canonical tags pointing to the preferred version",
            "3. Use 301 redirects to consolidate duplicates",
            "4. Add noindex to pages that shouldn't be indexed",
        ],
        code_examples={"Canonical": '<link rel="canonical" href="https://example.com/preferred-version">'},
        cms_guides={"WordPress": "Use Yoast SEO → Set canonical URL on duplicate pages to point to the original"},
        verification_steps=["Each page should have unique content", "Canonical tags should point to preferred version"],
        priority="high",
    ),

    # =====================================================
    # JAVASCRIPT RENDERED
    # =====================================================
    "JavaScript Rendered Page": FixGuide(
        issue_type="JavaScript Rendered Page",
        title="JavaScript-Rendered Page Detected",
        severity="INFO",
        what_is_it="This page appears to be a Single Page Application (SPA) built with React, Vue, Angular, Next.js, etc. The crawler cannot execute JavaScript, so some metadata may be incomplete.",
        why_it_matters="Google can render JavaScript but with delays. Other search engines (Bing, Yandex) may not execute JS at all. Critical SEO elements must be in the initial HTML.",
        how_to_fix=[
            "1. Implement Server-Side Rendering (SSR) or Static Site Generation (SSG)",
            "2. For Next.js: Use getServerSideProps or getStaticProps",
            "3. For Nuxt: Use SSR mode or generate routes",
            "4. Add critical meta tags in the initial HTML response",
            "5. Use pre-rendering services for SPA content",
            "6. Implement dynamic rendering as a fallback",
        ],
        code_examples={
            "Next.js SSR": """// pages/about.js
export async function getServerSideProps() {
    return { props: { title: 'About Us' } };
}""",
            "Next.js SSG": """// pages/about.js
export async function getStaticProps() {
    return { props: { title: 'About Us' }, revalidate: 3600 };
}""",
            "Nuxt": """// nuxt.config.js
export default { ssr: true }""",
        },
        cms_guides={
            "Next.js": [
                "1. Ensure pages use getServerSideProps or getStaticProps",
                "2. Use app/layout.js for default metadata",
                "3. Test with 'View Source' to verify meta tags are in initial HTML",
            ],
            "React": [
                "1. Install react-helmet for client-side meta tags",
                "2. Implement SSR with Next.js or Gatsby",
                "3. Use prerender.io for dynamic rendering",
            ],
        },
        verification_steps=[
            "View page source (Ctrl+U) — verify meta tags are present in raw HTML",
            "If meta tags only appear after JS executes, SSR is needed",
            "Test with Google Search Console URL Inspection",
        ],
        priority="medium",
    ),
}


def get_fix_guide(issue_type: str) -> Optional[FixGuide]:
    """Get the fix guide for a specific issue type."""
    return FIX_GUIDES.get(issue_type)


def get_all_fix_guides() -> Dict[str, FixGuide]:
    """Get all available fix guides."""
    return FIX_GUIDES


def get_fix_guide_as_markdown(issue_type: str, cms: Optional[str] = None) -> str:
    """Get a fix guide formatted as Markdown for display.
    
    Args:
        issue_type: The type of issue to get the guide for
        cms: Optional CMS platform (wordpress, shopify, wix, squarespace) for CMS-specific instructions
    """
    guide = FIX_GUIDES.get(issue_type)
    if not guide:
        return f"No fix guide available for issue type: {issue_type}"

    md = f"## {guide.title}\n\n"
    md += f"**Severity:** {guide.severity} | **Priority:** {guide.priority}\n\n"
    md += f"### What is this issue?\n{guide.what_is_it}\n\n"
    md += f"### Why does it matter?\n{guide.why_it_matters}\n\n"
    md += f"### How to fix it\n"
    for step in guide.how_to_fix:
        md += f"{step}\n"
    md += "\n"

    if guide.code_examples:
        md += "### Code Examples\n"
        for name, code in guide.code_examples.items():
            md += f"\n**{name}:**\n```\n{code}\n```\n"
        md += "\n"

    # Show CMS-specific guide if provided, otherwise show all
    if cms and cms in guide.cms_guides:
        md += f"### CMS-Specific Instructions ({cms.title()})\n"
        for step in guide.cms_guides[cms]:
            md += f"- {step}\n"
        md += "\n"
    elif guide.cms_guides:
        md += "### CMS-Specific Instructions\n"
        for cms_name, steps in guide.cms_guides.items():
            md += f"\n**{cms_name.title()}:**\n"
            for step in steps:
                md += f"- {step}\n"
        md += "\n"

    if guide.verification_steps:
        md += "### How to Verify the Fix\n"
        for step in guide.verification_steps:
            md += f"- {step}\n"

    return md
