import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from trendradar.ai.analyzer import AIAnalyzer


class EngineeringAnalysisTests(unittest.TestCase):
    def test_recent_recommendations_are_context_not_allowed_sources(self):
        from trendradar.core import load_config
        config = load_config()
        analysis = dict(config['AI_ANALYSIS'],STRUCTURED_EVENTS=True,FETCH_EVIDENCE=False,
                        RECENT_RECOMMENDATIONS=[dict(title='previous topic',facts='old method',url='https://example.com/old')])
        analyzer = AIAnalyzer(config['AI'], analysis, datetime.now)
        analyzer.client.api_key = 'test-only'
        event = dict(title='old',facts='fact',impact='impact',suggestion='test',url='https://example.com/old')
        with patch.object(analyzer,'_call_ai',return_value=json.dumps(dict(events=[event]))) as call:
            result = analyzer.analyze([],rss_stats=[dict(word='Agent',titles=[
                dict(title='new',url='https://example.com/new',summary='new method')])])
        self.assertIn('previous topic',call.call_args.args[0])
        self.assertNotIn('https://example.com/old',analyzer.allowed_event_urls)
        self.assertFalse(result.success)

    def test_invalid_or_empty_analysis_is_not_success(self):
        for response in ('', '{}', '[]', 'not json', '{"unknown": "text"}'):
            with self.subTest(response=response):
                result = AIAnalyzer.__new__(AIAnalyzer)._parse_response(response)
                self.assertFalse(result.success)
                self.assertTrue(result.error)

    def test_timeout_and_no_content_are_distinct(self):
        from trendradar.core import load_config
        config = load_config()
        analyzer = AIAnalyzer(config["AI"], config["AI_ANALYSIS"], datetime.now)
        analyzer.client = MagicMock()
        analyzer.client.api_key = "test-only"
        empty = analyzer.analyze([])
        self.assertTrue(empty.skipped)
        analyzer.client.chat.assert_not_called()
        with patch.object(analyzer, "_call_ai", side_effect=TimeoutError("test timeout")):
            failed = analyzer.analyze([], rss_stats=[{"word": "Agent", "titles": [
                {"title": "Tool calling update", "url": "https://example.com/update"}
            ]}])
        self.assertFalse(failed.success)
        self.assertFalse(failed.skipped)
        self.assertIn("test timeout", failed.error)
