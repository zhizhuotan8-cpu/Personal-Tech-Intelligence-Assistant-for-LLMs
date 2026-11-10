import unittest
from trendradar.ai.analyzer import AIAnalyzer
from trendradar.ai.engineering import render_events

class EvidenceTests(unittest.TestCase):
    def test_summary_survives_model_input(self):
        rows=[dict(title='v1.2',url='https://example.com/release',summary='Fix tool streaming')]
        analyzer=AIAnalyzer.__new__(AIAnalyzer)
        analyzer.max_news=80
        analyzer.include_rss=True
        data=analyzer._prepare_news_content([], [{'word':'SDK','titles':rows}])
        self.assertIn('Fix tool streaming', data.rss_content)
        self.assertIn('非全文', data.rss_content)

    def test_evidence_label_is_program_controlled(self):
        item=dict(title='v1',facts='修复',impact='影响',suggestion='验证',url='https://example.com')
        _, text=render_events([item],{item['url']},{item['url']:'RSS 摘要，非全文'})
        self.assertIn('证据范围：RSS 摘要，非全文',text)
        _, text=render_events([item],{item['url']})
        self.assertIn('证据范围：仅标题',text)
