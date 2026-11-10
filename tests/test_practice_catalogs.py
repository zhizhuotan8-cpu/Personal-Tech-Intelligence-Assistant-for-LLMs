import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from trendradar.crawler.rss.catalogs import parse_catalog, save_catalog_snapshot, CATALOGS
from trendradar.crawler.rss.fetcher import RSSFetcher, RSSFeedConfig

class PracticeCatalogTests(unittest.TestCase):
    def test_anthropic_dates_and_no_external_links(self):
        content='''<main><article><time datetime="2026-11-06">Nov 6, 2026</time><a href="/research/example"><h2>Agent Memory Example</h2></a></article><a href="https://evil.example/research/fake">Fake article</a><a href="/engineering">Engineering</a></main>'''
        items=parse_catalog(content,'https://www.anthropic.com/engineering')
        self.assertEqual(len(items),1)
        self.assertEqual(items[0].published_at,'2026-11-06')

    def test_undated_tutorial_and_cookbook_are_not_today(self):
        for url,path in [('https://haystack.deepset.ai/tutorials','/tutorials/55_example'),('https://langfuse.com/guides/cookbook','/guides/cookbook/example')]:
            with self.subTest(url=url):
                items=parse_catalog(f'<a href="{path}"><h3>Example Practical Tutorial</h3><p>Steps and evaluation</p></a><a href="{path}">Example Tutorial</a>',url)
                self.assertEqual(len(items),1)
                self.assertIsNone(items[0].published_at)
                self.assertIn('Steps',items[0].summary)

    def test_broken_catalog_does_not_succeed_empty(self):
        with self.assertRaises(ValueError):
            parse_catalog('<html>Access denied</html>',next(iter(CATALOGS)))

    def test_fetcher_integrates_catalog_and_snapshot(self):
        feed=RSSFeedConfig('test','test','https://langfuse.com/guides/cookbook')
        fetcher=RSSFetcher([feed])
        response=MagicMock(text='<a href="/guides/cookbook/example">Example Eval Tutorial</a>')
        with patch.object(fetcher.session,'get',return_value=response), patch('trendradar.crawler.rss.catalogs.save_catalog_snapshot') as save:
            items,error=fetcher.fetch_feed(feed)
        self.assertIsNone(error)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0].published_at,'')
        save.assert_called_once()
        fetcher.session.close()

    def test_first_seen_is_not_reset(self):
        url='https://langfuse.com/guides/cookbook'
        items=parse_catalog('<a href="/guides/cookbook/example">Example Eval Tutorial</a>',url)
        with tempfile.TemporaryDirectory() as directory:
            save_catalog_snapshot(url,items,directory)
            path=next(Path(directory).glob('*.json'))
            old=json.loads(path.read_text(encoding='utf-8'))
            save_catalog_snapshot(url,items,directory)
            new=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(old['articles'][items[0].url]['first_seen'],new['articles'][items[0].url]['first_seen'])
            self.assertIsNone(new['articles'][items[0].url]['published_at'])

    def test_source_balance_prevents_catalog_starvation(self):
        from trendradar.preview import balanced_candidates
        items=[dict(url=f'https://a/{i}',source='A') for i in range(100)]+[dict(url='https://b/1',source='B')]
        selected=balanced_candidates(items,4)
        self.assertEqual(len(selected),4)
        self.assertIn('B',[item['source'] for item in selected])

class CatalogEvidenceLabelTests(unittest.TestCase):
    def test_directory_description_is_not_labeled_as_article_body(self):
        import json
        from datetime import datetime
        from trendradar.ai.analyzer import AIAnalyzer
        analyzer=AIAnalyzer({'MODEL':'test','API_KEY':'test-key'},{'STRUCTURED_EVENTS':True},datetime.now)
        url='https://langfuse.com/guides/cookbook/example'
        payload=json.dumps({'events':[dict(title='评测实践',facts='目录介绍评测',impact='待核验',suggestion='先阅读方法',url=url)]})
        with patch.object(analyzer,'_call_ai',return_value=payload):
            result=analyzer.analyze([],rss_stats=[dict(word='实践',titles=[dict(title='Evaluation Tutorial',url=url,summary='实践目录简介（非全文）：Evaluation steps')])])
        self.assertTrue(result.success)
        self.assertIn('实践目录简介（非正文）',analyzer.event_evidence[url])
        self.assertIn('原始发布日期',analyzer.event_evidence[url])
