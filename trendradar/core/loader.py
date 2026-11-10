"""只加载本地工程情报流程实际使用的配置。"""
import os
from pathlib import Path
import yaml


def load_config(config_path=None):
    path = Path(config_path or os.environ.get('CONFIG_PATH', 'config/config.yaml'))
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('配置必须为 YAML 对象')
    def section(name):
        value = data.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(f'{name} 必须为对象')
        return {key.upper(): value for key, value in value.items()}
    ai = section('ai')
    for key in ('API_KEY', 'MODEL', 'API_BASE'):
        ai[key] = os.environ.get('AI_' + key) or ai.get(key, '')
    rss = section('rss')
    # Feed field names stay lowercase, as consumed by RSSFeedConfig.
    rss.setdefault('FEEDS', [])
    rss['FRESHNESS_FILTER'] = {k.upper(): v for k,v in rss.get('FRESHNESS_FILTER', {}).items()}
    return dict(TIMEZONE=data.get('app', {}).get('timezone', 'Asia/Shanghai'),
                AI=ai, RSS=rss, AI_FILTER=section('ai_filter'), AI_ANALYSIS=section('ai_analysis'))
