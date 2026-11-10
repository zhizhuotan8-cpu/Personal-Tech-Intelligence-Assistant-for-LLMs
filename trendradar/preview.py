"""Manual local preview: isolated from scheduled runs and notifications."""
import html
import json
import os
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from trendradar.ai.analyzer import AIAnalyzer
from trendradar.ai.filter import AIFilter
from trendradar.core import load_config
from trendradar.crawler.rss import RSSFetcher, RSSFeedConfig
from trendradar.utils.time import get_configured_time, is_within_days


def load_user_environment():
    if os.name != 'nt':
        return
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
            for name in ('AI_API_KEY', 'AI_MODEL', 'AI_API_BASE'):
                if not os.environ.get(name):
                    try:
                        value, kind = winreg.QueryValueEx(key, name)
                        if isinstance(value, str):
                            os.environ[name] = os.path.expandvars(value) if kind == winreg.REG_EXPAND_SZ else value
                    except FileNotFoundError:
                        pass
    except FileNotFoundError:
        pass


def render_report(state):
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for event in state.get('events', []):
        url = event['url']
        practical = url.startswith(('https://www.langchain.com/blog/', 'https://weaviate.io/blog/'))
        title = event['title']
        if practical and not title.startswith('实践阅读'):
            title = '实践阅读｜' + title
        scope = state.get('evidence', {}).get(url, '仅标题，待核验')
        if practical and '原始发布日期' not in scope:
            scope += '；订阅时间不代表原始发布日期'
        link = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">阅读原文 ↗</a>' if url.startswith(('https://', 'http://')) else ''
        cards.append(f'''<article><h2>{esc(title)}</h2>
<p><b>发生了什么</b><br>{esc(event['facts'])}</p>
<p><b>工程影响 · 推断</b><br>{esc(event['impact'])}</p>
<p><b>验证建议</b><br>{esc(event['suggestion'])}</p>
<small>{esc(scope)}</small><p>{link}</p></article>''')
    if not cards:
        cards.append(f'<article><h2>{esc(state["status"])}</h2><p>{esc(state.get("message", ""))}</p></article>')
    failures = state.get('failed_sources', [])
    warning = f'<p class="warning">部分来源失败：{esc("、".join(failures))}。本次结果可能不完整。</p>' if failures else ''
    demo = '<p class="warning">样本演示 · 固定样本日期 2026-11-10 · 内容为功能示意，未实时采集或核验。</p>' if state.get('demo') else ''
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>工程情报 · 本地预览</title><style>
body{{margin:0;background:#f4f6fa;color:#172438;font:16px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}}main{{max-width:920px;margin:48px auto;padding:0 24px}}header{{border-bottom:2px solid #28716b;padding-bottom:24px}}h1{{font-size:34px;margin:8px 0}}h2{{font-size:22px}}.label,small{{color:#557079}}article{{background:white;border:1px solid #dce4ec;border-radius:16px;padding:24px 30px;margin:22px 0;overflow-wrap:anywhere}}a{{color:#126a62}}.warning{{padding:14px;background:#fff0d6;border-radius:8px}}footer{{color:#637487;font-size:14px;margin:32px 0}}b{{color:#32615d}}p{{white-space:pre-wrap}}
</style><main><header><div class="label">LLM ENGINEERING RADAR / 本地预览</div><h1>近期值得关注的工程情报</h1><div>{esc(state['status'])} · {esc(state['generated_at'])}</div>
<div>来源成功 {state.get('source_success',0)} / 失败 {len(failures)} · 近 {state.get('days',3)} 天 · 精选 {len(state.get('events',[]))} 条 · 用时 {state.get('elapsed_seconds',0)} 秒</div></header>{demo}{warning}{''.join(cards)}
<footer>关注 Agent、RAG、模型/API 与部署。工程影响与建议供小规模验证，原文事实仍需核对。<br>此入口只生成本地预览，不发送通知。每次运行保留独立报告。</footer></main></html>'''


def collect_and_analyze(config, state, directory, full_evidence=False):
    ai = config['AI']
    if not ai.get('API_KEY'):
        raise RuntimeError('缺少 AI_API_KEY，请检查 Windows 用户环境变量，或运行 --demo 查看样本。')
    rss = config['RSS']
    if not rss.get('ENABLED'):
        raise RuntimeError('RSS 未启用，请检查 config/config.yaml。')
    feeds = [RSSFeedConfig(id=f['id'], name=f.get('name', f['id']), url=f['url'],
                           max_items=f.get('max_items',50), max_age_days=f.get('max_age_days'))
             for f in rss['FEEDS'] if f.get('enabled',True)]
    if not feeds:
        raise RuntimeError('没有启用的 RSS 来源。')
    print('[1/3] 正在采集 RSS 来源...', flush=True)
    fetcher = RSSFetcher(feeds, request_interval=rss.get('REQUEST_INTERVAL',1000),
                         timeout=rss.get('TIMEOUT',15), use_proxy=rss.get('USE_PROXY',False),
                         proxy_url=rss.get('PROXY_URL',''))
    try:
        data = fetcher.fetch_all()
    finally:
        fetcher.session.close()
    state['source_success'] = len(data.items)
    state['failed_sources'] = [data.id_to_name.get(i,i) for i in data.failed_ids]
    if not data.items:
        raise RuntimeError('所有来源采集失败，请检查网络后重试。')
    freshness = rss.get('FRESHNESS_FILTER',{})
    candidates = []
    for feed in feeds:
        days = feed.max_age_days if feed.max_age_days is not None else freshness.get('MAX_AGE_DAYS',3)
        for item in data.items.get(feed.id,[]):
            if freshness.get('ENABLED',True) and days > 0 and item.published_at and not is_within_days(item.published_at,days,config.get('TIMEZONE','Asia/Shanghai')):
                continue
            candidates.append(dict(title=item.title, source=item.feed_name, source_name=item.feed_name,
                                   url=item.url, summary=item.summary, time_display=item.published_at))
    limit = config['AI_ANALYSIS'].get('MAX_NEWS_FOR_ANALYSIS',80)
    candidates = list({item['url']:item for item in candidates if item['url']}.values())[:limit]
    for index,item in enumerate(candidates,1):
        item['id'] = index
    (directory/'sources.json').write_text(json.dumps([asdict(item) for items in data.items.values() for item in items],ensure_ascii=False,indent=2),encoding='utf-8')
    state['candidate_count'] = len(candidates)
    if not candidates:
        state.update(status='本次无值得推荐的更新',message='新鲜度范围内暂无可分析条目，可稍后重新运行。')
        return
    print(f'[2/3] AI 筛选 {len(candidates)} 条近期内容...',flush=True)
    interests = Path('config',(config['AI_FILTER'].get('INTERESTS_FILE') or 'ai_interests.txt')).read_text(encoding='utf-8')
    selector = AIFilter(ai,config['AI_FILTER'],datetime.now)
    tags = [
        dict(id=1,tag='Agent',description='Agent 编排、工具调用、LangChain、LangGraph、Deep Agents 与可靠性实践'),
        dict(id=2,tag='RAG',description='文档解析、检索、Embedding、重排、引用与评测'),
        dict(id=3,tag='模型/API',description='模型能力、API 兼容、弃用、成本、限流与结构化输出'),
        dict(id=4,tag='部署',description='推理部署、延迟吞吐与应用运行兼容性'),
    ]
    matches = selector.classify_batch(candidates,tags,interests)
    if matches is None:
        raise RuntimeError('AI 筛选失败，未生成新的简报，请稍后重试。')
    ids = {m['news_item_id'] for m in matches if m['relevance_score'] >= config['AI_FILTER'].get('MIN_SCORE',0.7)}
    selected = [item for item in candidates if item['id'] in ids]
    if not selected:
        state.update(status='本次无值得推荐的更新',message=f'已分析 {len(candidates)} 条近期内容，本次没有满足兴趣与质量要求的更新。')
        return
    print(f'[3/3] 为 {len(selected)} 条候选生成工程简报...',flush=True)
    analysis_config = dict(config['AI_ANALYSIS'],STRUCTURED_EVENTS=True,FETCH_EVIDENCE=full_evidence)
    analyzer = AIAnalyzer(ai,analysis_config,lambda:get_configured_time(config.get('TIMEZONE','Asia/Shanghai')))
    result = analyzer.analyze([],rss_stats=[dict(word='工程情报',titles=selected)],report_type='手动真实预览')
    if not result.success:
        raise RuntimeError('AI 简报生成失败：'+result.error)
    state.update(events=result.events,evidence=analyzer.event_evidence,status='成功生成' if result.events else '本次无值得推荐的更新',message='模型未选出值得推荐的事件。')


def run_preview(demo=False, no_open=False, full_evidence=False, days=None):
    started = time.monotonic()
    load_user_environment()
    root = Path(__file__).resolve().parents[1]
    previous = Path.cwd()
    os.chdir(root)
    directory = root/'output'/'preview'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    directory.mkdir(parents=True)
    state = dict(generated_at=get_configured_time('Asia/Shanghai').strftime('%Y-%m-%d %H:%M:%S 北京时间'),status='正在运行',events=[],demo=demo)
    code = 0
    try:
        if demo:
            state.update(status='样本演示',events=[dict(title='示例：框架工具调用更新的阅读方式',facts='这是界面演示数据，不代表今日发布了功能。',impact='关注工具参数、流式响应与兼容性变化。',suggestion='在测试分支对现有工具调用用例做回归。',url='https://github.com/langchain-ai/langgraph/releases')])
        else:
            config = load_config()
            if days is not None:
                config['RSS']['FRESHNESS_FILTER'] = dict(ENABLED=True,MAX_AGE_DAYS=days)
                config['RSS']['FEEDS'] = [dict(feed,max_age_days=days) for feed in config['RSS']['FEEDS']]
            state['days'] = config['RSS'].get('FRESHNESS_FILTER',{}).get('MAX_AGE_DAYS',3)
            collect_and_analyze(config,state,directory,full_evidence)
    except Exception as exc:
        # Errors may contain provider request details: redact configured credentials.
        message = str(exc)
        for name in ('AI_API_KEY','AI_API_BASE'):
            if os.environ.get(name):
                message = message.replace(os.environ[name],'[已隐藏]')
        state.update(status='运行失败',message=message,events=[])
        code = 1
    finally:
        state['elapsed_seconds'] = round(time.monotonic()-started,1)
        report = directory/'report.html'
        report.write_text(render_report(state),encoding='utf-8')
        (directory/'status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        (root/'output'/'preview'/'latest.html').write_text(render_report(state),encoding='utf-8')
        os.chdir(previous)
    print(f"{state['status']}：{report}",flush=True)
    if not no_open:
        webbrowser.open(report.as_uri())
    return code
