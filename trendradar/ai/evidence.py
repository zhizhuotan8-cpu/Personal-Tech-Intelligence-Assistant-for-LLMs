"""Bounded, public-source article excerpts with auditable local snapshots."""
import hashlib
import json
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin

import requests

HOSTS = {'github.com', 'openai.com', 'huggingface.co', 'qwenlm.github.io', 'www.langchain.com', 'weaviate.io', 'www.anthropic.com', 'haystack.deepset.ai', 'langfuse.com'}


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in {'br', 'img', 'meta', 'link', 'input', 'hr', 'source', 'wbr'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data):
        if any(t in self.stack for t in ('article', 'main')) and not any(
            t in self.stack for t in ('script', 'style', 'nav', 'header', 'footer', 'aside')):
            text = ' '.join(data.split())
            if text:
                self.parts.append(text)


def allowed(url):
    p = urlsplit(url)
    return p.scheme == 'https' and p.hostname in HOSTS and not p.username and not p.password and p.port in (None, 443)


def fetch_evidence(url, directory='output/evidence'):
    """Return a bounded excerpt or an explicit fallback status; never execute page content."""
    record = {'url': url, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'status': 'failed', 'text': ''}
    try:
        if not allowed(url):
            raise ValueError('unsupported_source')
        path = Path(directory) / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if path.exists() and time.time() - path.stat().st_mtime < 86400:
            cached = json.loads(path.read_text(encoding='utf-8'))
            if cached.get('url') == url and cached.get('status') == 'ok':
                return cached
        current = url
        started = time.monotonic()
        for _ in range(4):
            if not allowed(current):
                raise ValueError('unsupported_redirect')
            with requests.get(current, timeout=(5, 10), stream=True, allow_redirects=False,
                              headers={'User-Agent': 'TrendRadar-Evidence/1.0'}) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    current = urljoin(current, response.headers.get('Location', ''))
                    continue
                response.raise_for_status()
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    raise ValueError('unsupported_content_type')
                body = bytearray()
                for chunk in response.iter_content(16384):
                    body.extend(chunk)
                    if len(body) > 2_000_000 or time.monotonic() - started > 25:
                        raise ValueError('fetch_limit')
                parser = ArticleParser()
                parser.feed(bytes(body).decode(response.encoding or 'utf-8', errors='replace'))
                text = '\n'.join(parser.parts)
                if len(text) < 100:
                    raise ValueError('article_not_found')
                record.update(status='ok', text=text[:6000], truncated=len(text) > 6000,
                              final_url=current, content_sha256=hashlib.sha256(body).hexdigest())
                break
        else:
            raise ValueError('redirect_limit')
    except (requests.RequestException, ValueError, OSError) as exc:
        record['reason'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    try:
        path = Path(directory) / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        pass
    return record
