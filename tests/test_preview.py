import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from trendradar.preview import run_preview, render_report

class PreviewTests(unittest.TestCase):
    def test_recommendations_skip_duplicates_but_keep_risk_notices(self):
        from trendradar.preview import filter_recommended
        items = [dict(url='old',title='Tutorial'),
                 dict(url='risk',title='Breaking API migration'),
                 dict(url='new',title='New tutorial')]
        result = filter_recommended(items, {'old','risk'})
        self.assertEqual([item['url'] for item in result], ['risk','new'])
        self.assertTrue(result[0]['previously_recommended'])

    def test_only_successful_real_reports_seed_history(self):
        from trendradar.preview import previous_recommendations
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, status, demo in [('real','成功生成',False),('demo','成功生成',True),('failed','运行失败',False)]:
                directory = root/name
                directory.mkdir()
                (directory/'status.json').write_text(json.dumps(dict(status=status,demo=demo,events=[dict(url=name)])),encoding='utf-8')
            self.assertEqual(previous_recommendations(root/'next'), {'real'})

    def test_practice_is_not_presented_as_new_release(self):
        event = dict(title='检索方法', facts='事实', impact='推断', suggestion='建议', url='https://www.langchain.com/blog/test')
        text = render_report(dict(status='成功生成',generated_at='now',events=[event]))
        self.assertIn('实践阅读｜检索方法',text)
        self.assertIn('订阅时间不代表原始发布日期',text)

    def test_report_escapes_content(self):
        text=render_report(dict(status='运行失败',generated_at='now',message='<script>alert(1)</script>'))
        self.assertNotIn('<script>',text)
        self.assertIn('&lt;script&gt;',text)

    def test_demo_and_failure_are_distinct_and_overwrite_latest(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            fake=root/'trendradar'/'preview.py'
            fake.parent.mkdir()
            with patch('trendradar.preview.__file__',str(fake)), patch('trendradar.preview.load_user_environment'), patch('trendradar.preview.load_config',return_value={}), patch('trendradar.preview.collect_and_analyze',side_effect=RuntimeError('test model failure')):
                self.assertEqual(run_preview(demo=True,no_open=True),0)
                latest=root/'output'/'preview'/'latest.html'
                self.assertIn('样本演示',latest.read_text(encoding='utf-8'))
                self.assertEqual(run_preview(no_open=True),1)
                self.assertIn('运行失败',latest.read_text(encoding='utf-8'))
                self.assertNotIn('示例：框架',latest.read_text(encoding='utf-8'))
                self.assertEqual(len(list((root/'output'/'preview').glob('*/status.json'))),2)

class PreviewPipelineTests(unittest.TestCase):
    def run_pipeline(self, matches=None, analysis_success=True):
        from types import SimpleNamespace
        from trendradar.preview import collect_and_analyze
        item=SimpleNamespace(title='SDK update',feed_name='SDK',url='https://github.com/org/sdk/releases/tag/v1',summary='Tool streaming fix',published_at='2026-11-10')
        config={'AI':{'API_KEY':'test'},'RSS':{'ENABLED':True,'FEEDS':[{'id':'sdk','url':'https://github.com/feed'}],'FRESHNESS_FILTER':{'ENABLED':False}},'AI_ANALYSIS':{},'AI_FILTER':{'INTERESTS_FILE':None}}
        state={}
        with tempfile.TemporaryDirectory() as directory, patch('trendradar.preview.RSSFetcher') as fetch, patch('trendradar.preview.AIFilter') as selector, patch('trendradar.preview.AIAnalyzer') as analyzer, patch('trendradar.preview.asdict',return_value={'title':'SDK update'}):
            fetch.return_value.fetch_all.return_value=SimpleNamespace(items={'sdk':[item]},id_to_name={'sdk':'SDK'},failed_ids=[])
            selector.return_value.extract_tags.return_value=[{'tag':'Agent'}]
            selector.return_value.classify_batch.return_value=matches
            analyzer.return_value.analyze.return_value=SimpleNamespace(success=analysis_success,events=[{'title':'test'}],error='model timeout')
            analyzer.return_value.event_evidence={}
            collect_and_analyze(config,state,Path(directory))
            return state

    def test_valid_match_reaches_analysis(self):
        state=self.run_pipeline([{'news_item_id':1,'relevance_score':0.9}])
        self.assertEqual(state['status'],'成功生成')

    def test_no_match_is_not_failure(self):
        self.assertEqual(self.run_pipeline([])['status'],'本次无值得推荐的更新')

    def test_classifier_failure_is_not_no_updates(self):
        with self.assertRaisesRegex(RuntimeError,'筛选失败'):
            self.run_pipeline(None)

    def test_analysis_failure_is_not_no_updates(self):
        with self.assertRaisesRegex(RuntimeError,'简报生成失败'):
            self.run_pipeline([{'news_item_id':1,'relevance_score':0.9}],False)
