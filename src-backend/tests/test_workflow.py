from unittest.mock import AsyncMock, MagicMock, patch

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


class TestPlannerAgent:
    """Tests for PlannerAgent."""

    @pytest.mark.asyncio
    async def test_create_presentation_plan_success(self):
        """Test successful presentation plan creation."""
        from mcp_server.agents.planner.agent import PlannerAgent
        from mcp_server.agents.planner.schemas import (
            PresentationPayload,
            PresentationPlan,
            SlidePlan,
        )

        agent = PlannerAgent()

        mock_plan = PresentationPlan(
            topic="Test Topic",
            slides=[
                SlidePlan(
                    slide_number=i,
                    title=f"Slide {i}",
                    search_queries=[f"query{i}"],
                    content_goal=f"Goal {i}",
                )
                for i in range(3)
            ],
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(parsed=mock_plan))]

        with patch.object(
            agent.client.beta.chat.completions, "parse", new_callable=AsyncMock
        ) as mock_parse:
            mock_parse.return_value = mock_response

            payload = PresentationPayload(topic="Test Topic", num_slides=3)
            result = await agent.create_presentation_plan(payload)

            assert result.topic == "Test Topic"
            assert len(result.slides) == 3
            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_response_retries_on_none(self):
        """Test validation retries when response is None."""
        from mcp_server.agents.planner.agent import PlannerAgent
        from mcp_server.agents.planner.schemas import (
            PresentationPayload,
            PresentationPlan,
            SlidePlan,
        )

        agent = PlannerAgent()
        payload = PresentationPayload(topic="Test", num_slides=2)

        valid_plan = PresentationPlan(
            topic="Test",
            slides=[
                SlidePlan(
                    slide_number=i,
                    title=f"Slide {i}",
                    search_queries=["q"],
                    content_goal="Goal",
                )
                for i in range(2)
            ],
        )

        mock_responses = [
            MagicMock(choices=[MagicMock(message=MagicMock(parsed=None))]),
            MagicMock(choices=[MagicMock(message=MagicMock(parsed=valid_plan))]),
        ]

        with patch.object(
            agent.client.beta.chat.completions, "parse", new_callable=AsyncMock
        ) as mock_parse:
            mock_parse.side_effect = mock_responses

            result = await agent.create_presentation_plan(payload)
            assert result.topic == "Test"
            assert mock_parse.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
