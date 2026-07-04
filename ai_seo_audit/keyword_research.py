"""Keyword research engine: extracts, analyzes, and suggests keywords from crawled SEO data.
"""

import re
import math
from collections import Counter
from typing import List, Dict, Optional, Tuple

from ai_seo_audit.models import (
    WebsiteAuditReport,
    PageAuditReport,
    KeywordModel,
    ContentIdeaModel,
    KeywordResearchReport,
)

# Common English stop words to exclude from keyword extraction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used", "this", "that",
    "these", "those", "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "just", "don", "now", "here", "there", "then", "also", "about", "up",
    "out", "if", "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "again", "further", "once", "because", "until", "while",
    "although", "since", "unless", "however", "thus", "therefore", "moreover",
    "furthermore", "otherwise", "instead", "never", "always", "often", "sometimes",
    "still", "already", "yet", "even", "much", "many", "well", "back", "over",
    "down", "off", "against", "along", "among", "around", "behind", "beside",
    "beyond", "within", "without", "upon", "toward", "towards", "via", "per",
    "etc", "eg", "ie", "cf", "eg", "www", "com", "org", "net", "http", "https",
    "get", "set", "go", "make", "use", "find", "see", "look", "come", "take",
    "know", "think", "want", "give", "say", "tell", "ask", "try", "keep", "let",
    "begin", "show", "put", "mean", "call", "run", "move", "live", "believe",
    "feel", "leave", "bring", "write", "provide", "hold", "turn", "follow",
    "appear", "wait", "serve", "send", "expect", "allow", "add", "change",
    "work", "read", "learn", "help", "start", "open", "close", "build",
    "create", "delete", "remove", "edit", "update", "save", "load",
    "page", "site", "website", "web", "site", "new", "one", "two", "first",
    "last", "next", "previous", "click", "here", "home", "main", "menu",
    "copyright", "reserved", "rights", "privacy", "policy", "terms",
}

# Minimum word length for keyword extraction
MIN_WORD_LENGTH = 3
# Minimum phrase word count
MIN_PHRASE_WORDS = 2
# Maximum phrase word count
MAX_PHRASE_WORDS = 4


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words, removing punctuation and numbers."""
    text = text.lower()
    text = re.sub(r"[^a-z\s\-]", " ", text)
    words = text.split()
    return [w.strip("-") for w in words if len(w.strip("-")) >= MIN_WORD_LENGTH]


def _extract_phrases(tokens: List[str], min_words: int = 2, max_words: int = 3) -> List[str]:
    """Extract multi-word phrases from a token list."""
    phrases = []
    for n in range(min_words, max_words + 1):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i:i + n])
            if all(w not in STOP_WORDS for w in phrase.split()):
                phrases.append(phrase)
    return phrases


def _get_page_text(page: PageAuditReport) -> str:
    """Collect all extractable text from a page for keyword analysis."""
    parts = []
    meta = page.metadata
    if meta.title:
        parts.append(meta.title)
    if meta.meta_description:
        parts.append(meta.meta_description)
    for h in meta.headings:
        parts.append(h.text)
    for link in page.links:
        if link.text:
            parts.append(link.text)
    return " ".join(parts)


def _compute_density(count: int, total_words: int) -> float:
    """Compute keyword density as a percentage."""
    if total_words == 0:
        return 0.0
    return round((count / total_words) * 100, 2)


def extract_keywords_from_report(report: WebsiteAuditReport) -> KeywordResearchReport:
    """Extracts and analyzes all keywords from the crawled website audit report.

    This performs rule-based extraction: tokenizing page content, counting
    occurrences, computing density, and tracking keyword placement across
    titles, meta descriptions, headings, and URLs.
    """
    all_tokens: List[str] = []
    bigram_counter: Counter = Counter()
    trigram_counter: Counter = Counter()
    keyword_pages: Dict[str, set] = {}
    keyword_count: Dict[str, int] = {}

    # Per-keyword placement tracking
    in_title: Dict[str, bool] = {}
    in_meta: Dict[str, bool] = {}
    in_headings: Dict[str, bool] = {}
    in_url: Dict[str, bool] = {}

    for page in report.pages:
        text = _get_page_text(page)
        tokens = _tokenize(text)
        all_tokens.extend(tokens)

        # Single keywords
        for token in tokens:
            if token in STOP_WORDS:
                continue
            keyword_pages.setdefault(token, set()).add(page.url)
            keyword_count[token] = keyword_count.get(token, 0) + 1

            # Placement checks
            if page.metadata.title and token in page.metadata.title.lower():
                in_title[token] = True
            if page.metadata.meta_description and token in page.metadata.meta_description.lower():
                in_meta[token] = True
            for h in page.metadata.headings:
                if token in h.text.lower():
                    in_headings[token] = True
                    break
            if token in page.url.lower():
                in_url[token] = True

        # Bigrams
        phrases = _extract_phrases(tokens, 2, 2)
        for phrase in phrases:
            bigram_counter[phrase] += 1
            keyword_pages.setdefault(phrase, set()).add(page.url)
            keyword_count[phrase] = keyword_count.get(phrase, 0) + 1

        # Trigrams
        phrases3 = _extract_phrases(tokens, 3, 3)
        for phrase in phrases3:
            trigram_counter[phrase] += 1
            keyword_pages.setdefault(phrase, set()).add(page.url)
            keyword_count[phrase] = keyword_count.get(phrase, 0) + 1

    total_words = len(all_tokens)
    unique_words = len(set(all_tokens))

    # Build keyword models from single keywords
    keyword_models = []
    for kw, count in keyword_count.items():
        pages_found = sorted(keyword_pages.get(kw, set()))
        keyword_models.append(KeywordModel(
            keyword=kw,
            count=count,
            density=_compute_density(count, total_words),
            in_title=in_title.get(kw, False),
            in_meta_desc=in_meta.get(kw, False),
            in_headings=in_headings.get(kw, False),
            in_url=in_url.get(kw, False),
            pages=pages_found,
        ))

    # Sort by count descending
    keyword_models.sort(key=lambda k: k.count, reverse=True)

    # Split into primary (single top words) and secondary (phrases)
    primary = [k for k in keyword_models if " " not in k.keyword][:20]
    secondary = [k for k in keyword_models if " " in k.keyword][:20]

    # LSI keywords: top bigrams that aren't already in secondary
    lsi = []
    for phrase, count in bigram_counter.most_common(15):
        if not any(k.keyword == phrase for k in secondary):
            lsi.append(KeywordModel(
                keyword=phrase,
                count=count,
                density=_compute_density(count, total_words),
                pages=sorted(keyword_pages.get(phrase, set())),
            ))

    # Keyword gaps: common SEO terms NOT found in the site
    gap_candidates = [
        "guide", "tutorial", "best", "top", "review", "comparison",
        "how to", "what is", "benefits", "features", "pricing",
        "solution", "services", "professional", "expert", "trusted",
        "affordable", "quality", "premium", "custom", "free",
    ]
    existing_kws = {k.keyword.lower() for k in keyword_models}
    gaps = [g for g in gap_candidates if g not in existing_kws][:10]

    return KeywordResearchReport(
        primary_keywords=primary,
        secondary_keywords=secondary,
        lsi_keywords=lsi,
        recommended_keywords=[],  # Populated by AI engine
        content_ideas=[],  # Populated by AI engine
        keyword_gaps=gaps,
        total_words_analyzed=total_words,
        unique_words_found=unique_words,
    )


def get_page_text_content(page: PageAuditReport) -> str:
    """Returns concatenated text from page metadata for AI analysis."""
    meta = page.metadata
    parts = []
    if meta.title:
        parts.append(f"Title: {meta.title}")
    if meta.meta_description:
        parts.append(f"Description: {meta.meta_description}")
    for h in meta.headings:
        parts.append(f"H{h.level}: {h.text}")
    return " | ".join(parts)
