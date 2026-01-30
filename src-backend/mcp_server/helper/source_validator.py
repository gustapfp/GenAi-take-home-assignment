from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


class SourceValidator:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def normalize_url(self, url: str) -> str:
        """Removes query parameters (UTM, etc.) and fragments from the URL.

        Args:
            url (str): The URL to normalize.

        Returns:
            str: The normalized URL.
        """
        parsed = urlparse(url)
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        return clean_url

    def get_metadata(self, html_soup) -> dict:
        """Extracts author, date, and reference indicators from the HTML soup.

        Args:
            html_soup (BeautifulSoup): The HTML soup to extract metadata from.

        Returns:
            dict: The metadata.
        """
        meta = {"author": None, "date": None, "has_references": False}

        author_tag = html_soup.find("meta", {"name": "author"}) or html_soup.find(
            "meta", property="article:author"
        )
        if author_tag:
            meta["author"] = author_tag.get("content")

        date_tag = (
            html_soup.find("meta", {"name": "date"})
            or html_soup.find("meta", property="article:published_time")
            or html_soup.find("time")
        )
        if date_tag:
            meta["date"] = date_tag.get("content") or date_tag.get_text()

        headers = html_soup.find_all(["h1", "h2", "h3", "h4"])
        ref_keywords = ["references", "bibliography", "works cited", "sources"]
        for h in headers:
            if any(k in h.get_text().lower() for k in ref_keywords):
                meta["has_references"] = True
                break

        return meta

    def validate_url(self, url: str, tavily_confidence: float) -> dict:
        """Performs the full health check and scoring.
        Calculates a Hybrid Score with tavily confidence as the base points.
        Args:
            url (str): The URL to validate.

        Returns:
            dict: The validation result.
        """
        clean_url = self.normalize_url(url)
        base_points = tavily_confidence * 100
        result = {"url": clean_url, "status": "dead", "score": 0, "tier": "C", "details": {}}

        result = {"url": clean_url, "status": "dead", "score": 0, "tier": "C", "details": {}}

        try:
            # 1. Health Check
            response = requests.get(clean_url, headers=self.headers, timeout=5)
            if response.status_code != 200:
                result["details"]["error"] = f"Status {response.status_code}"
                return result

            result["status"] = "live"
            soup = BeautifulSoup(response.content, "html.parser")
            meta = self.get_metadata(soup)
            result["details"] = meta

            # 2. Score Calculation
            final_score = base_points

            if meta["author"]:
                final_score += 10
            if meta["date"]:
                final_score += 5

            # Bonuses for Domain Authority
            domain = urlparse(clean_url).netloc
            if domain.endswith((".edu", ".gov")):
                final_score += 15

            result["score"] = min(round(final_score, 2), 100)

            # 3. Tier Assignment
            if result["score"] >= 80:
                result["tier"] = "S"
            elif result["score"] >= 60:
                result["tier"] = "A"
            else:
                result["tier"] = "B"

        except Exception as e:
            result["details"]["error"] = str(e)

        return result

    def rank_sources(self, raw_results: list[dict]) -> list[dict]:
        """
        raw_results must include: {'url': '...', 'score': 0.81, ...}
        """
        ranked_results = []
        for item in raw_results:
            url = item.get("url", "")
            t_score = item.get("score", 0.5)  # Default to 0.5 if missing

            validation = self.validate_url(url, tavily_confidence=t_score)

            ranked_item = {**item, "validation": validation}
            ranked_results.append(ranked_item)

        # Sort by Final Score (High to Low)
        return sorted(ranked_results, key=lambda x: x["validation"]["score"], reverse=True)


source_validator = SourceValidator()
