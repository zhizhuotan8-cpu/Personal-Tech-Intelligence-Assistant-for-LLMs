import os
import json
from unittest.mock import patch

from trendradar.__main__ import main
from trendradar.core import load_config


def test_default_command_runs_real_preview():
    with patch('sys.argv', ['trendradar']), patch('trendradar.preview.run_preview', return_value=0) as run:
        assert main() == 0
        run.assert_called_once_with(False, False, False, 7)


def test_daily_command_uses_daily_completion_records():
    with patch('sys.argv', ['trendradar', '--daily']), patch('trendradar.daily.run_daily', return_value=1) as run:
        assert main() == 1
        run.assert_called_once_with()


def test_local_config_preserves_feeds_and_environment_override():
    with patch.dict(os.environ, {'AI_API_KEY': 'test-only', 'AI_MODEL': 'openai/test'}):
        config = load_config()
    assert config['AI']['API_KEY'] == 'test-only'
    assert config['AI']['MODEL'] == 'openai/test'
    assert len(config['RSS']['FEEDS']) == 24
    assert config['RSS']['FRESHNESS_FILTER']['MAX_AGE_DAYS'] == 3
    assert config['AI_ANALYSIS']['MAX_NEWS_FOR_ANALYSIS'] == 80
    assert 'SCHEDULE' not in config


def test_local_pipeline_uses_real_filter_and_analyzer(tmp_path):
    from trendradar.preview import collect_and_analyze
    from trendradar.storage.base import RSSData, RSSItem
    url = 'https://github.com/example/sdk/releases/tag/v1'
    item = RSSItem(title='Tool streaming fix', feed_id='sdk', feed_name='SDK', url=url,
                   summary='Fix tool streaming after reconnect')
    data = RSSData(date='2026-11-10', crawl_time='20:00', items={'sdk': [item]})
    event = dict(title='工具流式重连修复', facts='修复重连后的工具流式响应',
                 impact='可能影响异常恢复', suggestion='验证重连路径', url=url)
    with patch.dict(os.environ, {'AI_API_KEY': 'test-only'}):
        config = load_config()
    config['RSS']['FEEDS'] = [dict(id='sdk', name='SDK', url='https://github.com/example/sdk/releases.atom')]
    responses = [json.dumps([dict(id=1, tag_id=1, score=0.9)]),
                 json.dumps(dict(events=[event])), json.dumps(dict(events=[event]))]
    state = {}
    with patch('trendradar.preview.RSSFetcher') as fetcher, \
         patch('trendradar.ai.client.AIClient.chat', side_effect=responses) as chat, \
         patch('trendradar.ai.evidence.fetch_evidence', return_value=dict(
             status='ok', fetched_at='2026-11-10', text='Release notes: fix tool streaming after reconnect')):
        fetcher.return_value.fetch_all.return_value = data
        collect_and_analyze(config, state, tmp_path)
    assert state['status'] == '成功生成'
    assert state['events'] == [event]
    assert state['evidence'][url].startswith('网页正文摘录')
    assert chat.call_count == 3
