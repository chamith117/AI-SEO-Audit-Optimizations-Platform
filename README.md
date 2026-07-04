# AI-Powered SEO Audit Platform

A professional website-scale crawler and technical SEO auditor featuring a modern Streamlit frontend and DeepSeek AI optimizations. It checks page metadata, technical protocols, social markup (Open Graph/Twitter Cards), Schemas validation, and computes site-wide quality scores. Generates visual charts, data filters, and downloadable reports in **HTML, PDF, CSV, and JSON** formats.

---

## Features

- **Multipage Site Crawler**: Crawls domains recursively up to limits (max pages/depth) respecting `robots.txt` permissions.
- **Visual SEO Dashboard**:
  - Radial score metrics and stats grids showing critical/warning counts.
  - Interactive tabular views with live text filters.
  - Plotly gauge charts visualizing SEO progress.
  - Direct browser downloads of all generated report formats.
- **DeepSeek AI Optimizations Hub**:
  - **Copywriting Rewriter**: Rewrites title tags and suggests hooking H1 headings.
  - **Meta Description Builder**: Generates optimized CTR-focused page descriptions.
  - **Semantic Analysis**: Proposes LSI search keywords and checks readability.
  - **FAQ Builder**: Automatically generates Q&A blocks based on page contents.
  - **GEO (Generative Engine Optimization)**: Actionable tips to improve visibility on LLM engines (Gemini, ChatGPT, Perplexity).
  - **Technical Explainer**: Translates warnings/errors into simple educational guides.
- **Technical SEO Validations**: Validates SSL routing, checks sitemap-crawled orphans, and lists redirect chains.
- **Broken Asset Checkers**: Inspects external link references and image sources in parallel.

---

## Local Run

1. Install requirements in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```
2. Start the Streamlit web application:
   ```bash
   streamlit run app.py
   ```
3. Open your browser at `http://localhost:8501`.

---

## Docker Deployment

Build and run in a local Docker container:

```bash
# Build image
docker build -t ai-seo-platform .

# Run container
docker run -p 8501:8501 ai-seo-platform
```

Access the dashboard at `http://localhost:8501`.

---

## Streamlit Community Cloud Deployment

To deploy this project to Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New App** and select your repository, branch, and set main file to `app.py`.
4. (Optional) In app settings, configure your secrets:
   ```toml
   DEEPSEEK_API_KEY = "your-api-key-here"
   ```
5. Click **Deploy**! Streamlit will automatically read `requirements.txt` and serve the dashboard.

---

## CLI Usage (Fallback)

The toolkit remains accessible from the command line:

```bash
# Run website crawl audit
seoaudit crawl https://example.com --max-pages 20

# Run single page audit
seoaudit audit https://example.com -o reports/single.json
```
