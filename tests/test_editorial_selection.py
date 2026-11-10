from trendradar.preview import editorial_selection


def event(url, title='检索评测'):
    return dict(url=url, title=title, facts='使用标注数据评测检索', impact='影响', suggestion='验证')


def test_single_publisher_cannot_fill_report():
    events = [event(f'https://haystack.deepset.ai/tutorials/{i}', str(i)) for i in range(5)]
    kept, counts = editorial_selection(events, [])
    assert len(kept) == 2
    assert counts['source_limit'] == 3


def test_same_title_at_different_url_is_not_new_information():
    old = event('https://a.example/old')
    kept, counts = editorial_selection([event('https://b.example/new')], [old])
    assert kept == []
    assert counts['repeated_title'] == 1


def test_risk_notice_survives_editorial_limits():
    events = [event(f'https://a.example/{i}', f'API 下线迁移 {i}') for i in range(4)]
    kept, _ = editorial_selection(events, events)
    assert kept == events


def test_unrelated_sources_and_titles_survive():
    events = [event('https://a.example/1', '检索评测'), event('https://b.example/2', '部署排障')]
    assert editorial_selection(events, [])[0] == events


def test_github_publishers_are_independent_and_www_is_normalized():
    events = [event(f'https://github.com/owner{i}/repo/releases/1', str(i)) for i in range(4)]
    assert editorial_selection(events, [])[0] == events
    events = [event('https://www.example.com/1', 'a'), event('https://example.com/2', 'b'),
              event('https://www.example.com/3', 'c')]
    assert len(editorial_selection(events, [])[0]) == 2


def test_practice_label_and_punctuation_do_not_hide_repeat():
    kept, _ = editorial_selection([event('https://b.example/new', '实践阅读｜检索 评测！')],
                                  [event('https://a.example/old')])
    assert kept == []
