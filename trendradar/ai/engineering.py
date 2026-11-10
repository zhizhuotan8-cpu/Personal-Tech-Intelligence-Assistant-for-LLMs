"""Validate engineering events before rendering legacy report sections."""
from urllib.parse import urlsplit, urlunsplit


def render_events(events, allowed_urls, evidence=None):
    if not isinstance(events, list):
        raise ValueError("events 必须为数组")
    selected, seen_urls, seen_titles = [], set(), set()
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("事件必须为对象")
        fields = ('title', 'facts', 'impact', 'suggestion', 'url')
        if any(not isinstance(event.get(k), str) or not event[k].strip() for k in fields):
            raise ValueError("事件缺少标题、事实、影响、建议或原文链接")
        url = event['url'].strip()
        if url not in allowed_urls:
            raise ValueError("事件引用不在分析输入中")
        parts = urlsplit(url)
        identity = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), parts.query, ''))
        title = ''.join(event['title'].lower().split())
        if identity in seen_urls or title in seen_titles:
            continue
        seen_urls.add(identity)
        seen_titles.add(title)
        selected.append({k: event[k].strip() for k in fields})
        if len(selected) == 5:
            break
    blocks = []
    for i, event in enumerate(selected, 1):
        scope = (evidence or {}).get(event["url"], "仅标题，细节待原文核验")
        blocks.append(f"{i}）{event['title']}\n事实：{event['facts']}\n工程影响（推断）：{event['impact']}\n验证建议：{event['suggestion']}\n证据范围：{scope}\n原始出处：{event['url']}")
    return selected, '\n\n'.join(blocks) or '暂无值得推荐的更新。'
