"""Unit tests for the AI suggestion engine module.
"""

from unittest.mock import patch, MagicMock
import pytest

from ai_seo_audit.ai_engine import (
    call_deepseek,
    get_title_suggestions,
    get_meta_desc_suggestions,
    get_h1_suggestions,
    get_content_quality_analysis,
    get_keyword_suggestions,
    get_faq_suggestions,
    get_geo_recommendations,
    get_tech_explanation
)


def test_ai_engine_mock_fallbacks():
    """Tests that AI helpers yield valid text blocks when no API key is set."""
    # Under empty API key, mock returns should trigger
    title_res = get_title_suggestions(None, "Original Title")
    assert "Original Title" in title_res
    assert "Comprehensive Guide" in title_res

    desc_res = get_meta_desc_suggestions("", "Awesome Domain", "Original Description")
    assert "Awesome Domain" in desc_res

    h1_res = get_h1_suggestions(None, "Home Page", ["Welcome Home"])
    assert "Welcome Home" in h1_res

    quality_res = get_content_quality_analysis(None, "This is page content.")
    assert "EEAT" in quality_res or "E-E-A-T" in quality_res

    kw_res = get_keyword_suggestions(None, "Manage DNS records here")
    assert "Keywords" in kw_res

    faq_res = get_faq_suggestions(None, "FAQ Title", "Sample body text")
    assert "FAQ Title" in faq_res

    geo_res = get_geo_recommendations(None, "AI Search optimization")
    assert "Generative Engine Optimization" in geo_res or "GEO" in geo_res

    tech_res = get_tech_explanation(None, "Viewport Check", "Description text")
    assert "Viewport Check" in tech_res


def test_call_deepseek_api_success():
    """Tests DeepSeek API requests validation mapping on 200 OK responses."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "DeepSeek Generated Text"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Execute
        res = call_deepseek("sk-fake-key-12345", "Test Prompt", "Test System Prompt")
        assert res == "DeepSeek Generated Text"
        
        # Verify it passed headers and standard model parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "deepseek-chat"
        assert "Bearer sk-fake-key-12345" in kwargs["headers"]["Authorization"]


def test_call_deepseek_api_failure():
    """Tests that call_deepseek handles connection issues or non-200 responses gracefully."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            call_deepseek("sk-key", "Prompt")
        
        assert "500" in str(exc_info.value)
