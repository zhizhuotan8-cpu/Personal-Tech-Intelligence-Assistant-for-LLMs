"""Adapters for official engineering/tutorial catalogs without reliable RSS."""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from .parser import ParsedRSSItem

CATALOGS = {
    'https://www.anthropic.com/engineering': ('/engineering/', '/research/'),
    'https://haystack.deepset.ai/tutorials': ('/tutorials/',),
    'https://langfuse.com/guides/cookbook': ('/guides/cookbook/',),
}
PRACTICE_PREFIXES = ('https://www.langchain.com/blog/', 'https://weaviate.io/blog/',
                     'https://www.anthropic.com/engineering/', 'https://www.anthropic.com/research/',
                     'https://haystack.deepset.ai/tutorials/', 'https://langfuse.com/guides/cookbook/')


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    parent: object = None
    children: list = field(default_factory=list)

    def find(self, tags):
        for child in self.children:
            if isinstance(child, Node):
                if child.tag in tags:
                    yield child
                yield from child.find(tags)

    def text(self):
        if self.tag in ('script','style','svg'):
            return ''
        return ' '.join(c.text() if isinstance(c, Node) else c for c in self.children)


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node('root')
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.current)
        self.current.children.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag,dict(attrs),self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, text):
        self.current.children.append(text)


def article_date(anchor):
    node = anchor
    for _ in range(5):
        times = list(node.find({'time'}))
        if len(times) == 1:
            value = times[0].attrs.get('datetime') or ' '.join(times[0].text().split())
            for fmt in ('%Y-%m-%d','%b %d, %Y','%B %d, %Y'):
                try:
                    return datetime.strptime(value,fmt).date().isoformat()
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(value.replace('Z','+00:00')).isoformat()
            except ValueError:
                return ''
        if len(times) > 1 or node.parent is None:
            break
        node = node.parent
    return ''


def parse_catalog(content, url):
    parser = CatalogParser()
    parser.feed(content)
    items = {}
    for anchor in parser.root.find({'a'}):
        target = urljoin(url,anchor.attrs.get('href',''))
        parsed = urlsplit(target)
        if parsed.scheme != 'https' or parsed.netloc != urlsplit(url).netloc or parsed.query or parsed.fragment:
            continue
        if not any(parsed.path.startswith(prefix) and parsed.path.rstrip('/') != prefix.rstrip('/') for prefix in CATALOGS[url]):
            continue
        heads = list(anchor.find({'h2','h3','h4'}))
        title = ' '.join((heads[0].text() if heads else anchor.text()).split())
        if len(title) < 8 or title.lower().startswith(('next ', 'previous ')):
            continue
        target = target.rstrip('/')
        summary = ' '.join(anchor.text().split())[:500]
        item = ParsedRSSItem(title=title, url=target,published_at=article_date(anchor) or None,
                             summary='实践目录简介（非全文）：'+summary,guid=target)
        # Content cards are more informative than repeated sidebar links.
        if target not in items or len(summary) > len(items[target].summary.removeprefix('实践目录简介（非全文）：')):
            items[target] = item
    if not items:
        raise ValueError('实践目录未解析到文章，页面结构可能已变化')
    return list(items.values())


def save_catalog_snapshot(url, items, directory='output/catalogs'):
    path = Path(directory)/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    now = datetime.now(timezone.utc).isoformat()
    previous = {}
    try:
        previous = json.loads(path.read_text(encoding='utf-8')).get('articles',{})
    except (OSError,ValueError):
        pass
    articles = dict(previous)
    for item in items:
        old = previous.get(item.url,{})
        signature = hashlib.sha256((item.title+str(item.summary)).encode()).hexdigest()
        articles[item.url] = dict(title=item.title,published_at=item.published_at,
                                 first_seen=old.get('first_seen',now),last_seen=now,
                                 changed_at=old.get('changed_at',now) if old.get('signature')==signature else now,
                                 signature=signature)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(url=url,checked_at=now,articles=articles),ensure_ascii=False,indent=2),encoding='utf-8')
