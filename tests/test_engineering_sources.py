"""Source evidence passed to the engineering digest, without network or model calls."""

import os
import unittest
from unittest.mock import patch

with patch.dict(os.environ, {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}):
    from trendradar.ai.analyzer import AIAnalyzer


class EngineeringSourceTests(unittest.TestCase):
    def prepare(self, titles, limit=80, include_rss=True):
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.max_news = limit
        analyzer.include_rss = include_rss
        return analyzer._prepare_news_content([], [{"word": "Agent", "titles": titles}])

    def test_source_url_survives_analysis_preparation(self):
        url = "https://github.com/langchain-ai/langgraph/releases/tag/1.0"
        prepared = self.prepare([{
            "title": "Tool calling update", "source_name": "LangGraph",
            "url": url, "time_display": "19:00",
        }])
        self.assertIn(url, prepared.rss_content)
        self.assertIn("LangGraph", prepared.rss_content)
        self.assertIn("19:00", prepared.rss_content)
        self.assertEqual(prepared.rss_analyzed, 1)

    def test_missing_link_is_not_invented_and_limit_is_preserved(self):
        prepared = self.prepare([{"title": "No source"}, {
            "title": "Excluded", "url": "https://example.com/excluded",
        }], limit=1)
        self.assertNotIn("原文:", prepared.rss_content)
        self.assertNotIn("Excluded", prepared.rss_content)
        self.assertEqual(prepared.rss_analyzed, 1)

    def test_disabled_rss_does_not_expose_sources(self):
        prepared = self.prepare([{"title": "Hidden", "url": "https://example.com"}], include_rss=False)
        self.assertEqual(prepared.rss_content, "")


if __name__ == "__main__":
    unittest.main()
