from unittest.mock import MagicMock, patch

import pytest


class TestSourceValidator:
    """Tests for SourceValidator helper."""

    def test_normalize_url_removes_query_params(self):
        """Test URL normalization removes query parameters."""
        from mcp_server.helper.source_validator import SourceValidator

        validator = SourceValidator()
        url = "https://example.com/article?utm_source=google&ref=123"
        normalized = validator.normalize_url(url)
        assert normalized == "https://example.com/article"

    def test_get_metadata_extracts_author(self):
        """Test metadata extraction for author."""
        from bs4 import BeautifulSoup

        from mcp_server.helper.source_validator import SourceValidator

        validator = SourceValidator()
        html = '<html><head><meta name="author" content="John Doe"></head></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = validator.get_metadata(soup)
        assert meta["author"] == "John Doe"

    def test_get_metadata_extracts_date(self):
        """Test metadata extraction for date."""
        from bs4 import BeautifulSoup

        from mcp_server.helper.source_validator import SourceValidator

        validator = SourceValidator()
        html = '<html><head><meta name="date" content="2026-01-30"></head><body><h2>References</h2><p>Source list</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = validator.get_metadata(soup)
        assert meta["date"] == "2026-01-30"
        assert meta["has_references"] is True

    @patch("mcp_server.helper.source_validator.requests.get")
    def test_validate_url_live_site(self, mock_get):
        """Test URL validation for a live site."""
        from mcp_server.helper.source_validator import SourceValidator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><head><meta name='author' content='Test'></head></html>"
        mock_get.return_value = mock_response

        validator = SourceValidator()
        result = validator.validate_url("https://example.com", tavily_confidence=0.8)

        assert result["status"] == "live"
        assert result["score"] > 0
        assert result["tier"] in ["S", "A", "B"]

    @patch("mcp_server.helper.source_validator.requests.get")
    def test_validate_url_dead_site(self, mock_get):
        """Test URL validation for a dead site."""
        from mcp_server.helper.source_validator import SourceValidator

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        validator = SourceValidator()
        result = validator.validate_url("https://example.com/404", tavily_confidence=0.8)

        assert result["status"] == "dead"
        assert result["tier"] == "C"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
