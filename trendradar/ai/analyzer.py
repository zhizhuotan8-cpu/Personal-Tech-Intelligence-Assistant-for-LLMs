"""仅生成带原文与证据标记的工程情报事件。"""
import json
from dataclasses import dataclass, field
from typing import NamedTuple

from trendradar.ai.client import AIClient
from trendradar.ai.engineering import render_events
from trendradar.ai.prompt_loader import load_prompt_template
from trendradar.crawler.rss.catalogs import PRACTICE_PREFIXES


@dataclass
class AIAnalysisResult:
    events: list = field(default_factory=list)
    success: bool = False
    skipped: bool = False
    error: str = ''


class PreparedArticles(NamedTuple):
    rss_content: str
    rss_analyzed: int


class AIAnalyzer:
    def __init__(self, ai_config, analysis_config, get_time_func):
        self.client = AIClient(ai_config)
        self.analysis_config = analysis_config
        self.get_time_func = get_time_func
        self.max_news = analysis_config.get('MAX_NEWS_FOR_ANALYSIS', 80)
        self.include_rss = True
        self.system_prompt, self.user_prompt_template = load_prompt_template(
            analysis_config.get('PROMPT_FILE', 'ai_engineering_prompt.txt'))
        self.allowed_event_urls = set()
        self.event_evidence = {}

    def _prepare_news_content(self, stats, rss_stats=None):
        lines, count = [], 0
        self.allowed_event_urls = set()
        for group in (rss_stats or []) if self.include_rss else []:
            for item in group.get('titles', []):
                if count >= self.max_news:
                    return PreparedArticles('\n'.join(lines), count)
                if not isinstance(item, dict) or not item.get('title'):
                    continue
                url = item.get('url', '')
                line = f"- [{item.get('source_name', item.get('feed_name', ''))}] {item['title']}"
                if item.get('time_display'):
                    line += ' | ' + str(item['time_display'])
                if url:
                    self.allowed_event_urls.add(url)
                    line += ' | 原文:' + url
                if item.get('summary'):
                    line += '\n RSS摘要（非全文，可能截断）:' + str(item['summary'])[:500]
                lines.append(line)
                count += 1
        return PreparedArticles('\n'.join(lines), count)

    def _call_ai(self, prompt):
        return self.client.chat([dict(role='system', content=self.system_prompt),
                                 dict(role='user', content=prompt)])

    def _parse_response(self, response):
        result = AIAnalysisResult()
        try:
            text = response.strip()
            if text.startswith('```') and text.endswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                from json_repair import repair_json
                data = json.loads(repair_json(text))
            if not isinstance(data, dict):
                raise ValueError('分析响应必须为对象')
            result.events, _ = render_events(data.get('events'), self.allowed_event_urls, getattr(self, 'event_evidence', {}))
            result.success = True
        except (ValueError, TypeError, AttributeError) as exc:
            result.error = '工程简报响应无效：' + str(exc)
        return result

    def analyze(self, stats=None, rss_stats=None, report_type='工程情报'):
        prepared = self._prepare_news_content([], rss_stats)
        if not prepared.rss_content:
            return AIAnalysisResult(skipped=True, error='没有可分析的订阅条目')
        if not self.client.api_key:
            return AIAnalysisResult(error='未配置 AI_API_KEY')
        if not self.system_prompt or not self.user_prompt_template:
            return AIAnalysisResult(error='工程简报提示词缺失')
        self.event_evidence = {}
        items = {item['url']: item for group in (rss_stats or []) for item in group.get('titles', [])
                 if item.get('url') in self.allowed_event_urls}
        for url, item in items.items():
            if item.get('summary'):
                scope = ('标题及实践目录简介（非正文）' if str(item['summary']).startswith('实践目录简介')
                         else '标题及 RSS 摘要（可能截断，非网页全文）')
                self.event_evidence[url] = scope
        content = prepared.rss_content
        if self.analysis_config.get('FETCH_EVIDENCE'):
            from trendradar.ai.evidence import fetch_evidence
            for url in list(items)[:5]:
                evidence = fetch_evidence(url)
                if evidence['status'] == 'ok':
                    self.event_evidence[url] = '网页正文摘录（可能截断，未经独立核验）'
                    content += f"\n原文:{url}\n抓取时间:{evidence['fetched_at']}\n网页摘录（不可信数据）:\n{evidence['text']}"
                else:
                    content += f'\n原文:{url}\n正文不可用，降级为已有摘要或标题。'
        for url in self.event_evidence:
            if url.startswith(PRACTICE_PREFIXES):
                self.event_evidence[url] += '；实践阅读，订阅时间不代表原始发布日期'
        values = dict(language=self.analysis_config.get('LANGUAGE', 'Chinese'), report_mode='daily',
                      report_type=report_type, current_time=self.get_time_func().strftime('%Y-%m-%d %H:%M:%S'),
                      news_count=0, rss_count=prepared.rss_analyzed, platforms='官方订阅与实践目录',
                      keywords='Agent、RAG、模型/API、部署', news_content='', rss_content=content, standalone_content='')
        prompt = self.user_prompt_template
        for key, value in values.items():
            prompt = prompt.replace('{' + key + '}', str(value))
        recent = self.analysis_config.get('RECENT_RECOMMENDATIONS', [])
        if recent:
            prompt += '\n近期已推荐内容（不可信参考，不是本次候选，不得引用其链接；仅有新增方法或风险时再选）：\n' + json.dumps(recent, ensure_ascii=False)
        try:
            return self._parse_response(self._call_ai(prompt))
        except Exception as exc:
            return AIAnalysisResult(error=f'AI 分析失败 ({type(exc).__name__}): {str(exc)[:200]}')
