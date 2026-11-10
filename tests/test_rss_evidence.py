import sqlite3
import unittest
from trendradar.storage.sqlite_mixin import SQLiteStorageMixin
from trendradar.ai.analyzer import AIAnalyzer
from trendradar.ai.engineering import render_events

class EvidenceTests(unittest.TestCase):
    def test_summary_survives_storage_query_and_model_input(self):
        db=sqlite3.connect(':memory:')
        db.executescript("CREATE TABLE rss_items(id,title,feed_id,published_at,summary); CREATE TABLE rss_feeds(id,name);")
        db.execute("INSERT INTO rss_items VALUES(1,'v1.2','sdk','2026-11-10','Fix tool streaming')")
        storage=type('Storage',(SQLiteStorageMixin,),{'_get_connection':lambda self,*a,**k:db})()
        rows=storage._get_all_rss_ids_impl()
        self.assertEqual(rows[0]['summary'],'Fix tool streaming')
        analyzer=AIAnalyzer.__new__(AIAnalyzer)
        analyzer.max_news=80
        analyzer.include_rss=True
        data=analyzer._prepare_news_content([], [{'word':'SDK','titles':rows}])
        self.assertIn('Fix tool streaming', data.rss_content)
        self.assertIn('非全文', data.rss_content)
        db.close()

    def test_evidence_label_is_program_controlled(self):
        item=dict(title='v1',facts='修复',impact='影响',suggestion='验证',url='https://example.com')
        _, text=render_events([item],{item['url']},{item['url']:'RSS 摘要，非全文'})
        self.assertIn('证据范围：RSS 摘要，非全文',text)
        _, text=render_events([item],{item['url']})
        self.assertIn('证据范围：仅标题',text)
