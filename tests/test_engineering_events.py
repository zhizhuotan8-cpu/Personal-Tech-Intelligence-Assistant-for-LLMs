import unittest
from trendradar.ai.engineering import render_events

class EngineeringEventTests(unittest.TestCase):
    def event(self, i):
        return dict(title=f'事件{i}', facts='事实', impact='推断', suggestion='建议', url=f'https://example.com/{i}')

    def test_limit_and_duplicate(self):
        items=[self.event(0), self.event(0)]+[self.event(i) for i in range(1,9)]
        events, text=render_events(items, {e['url'] for e in items})
        self.assertEqual(len(events),5)
        self.assertEqual(len({e['url'] for e in events}),5)
        self.assertNotIn('事件5',text)

    def test_unknown_link_and_invalid_structure_fail(self):
        for items in ({}, [None], [{}], [self.event(0)]):
            with self.subTest(items=items), self.assertRaises(ValueError):
                render_events(items,set())

    def test_empty_is_explicit(self):
        events,text=render_events([],set())
        self.assertEqual(events,[])
        self.assertIn('暂无',text)

    def test_analyzer_uses_only_validated_events(self):
        import json
        from trendradar.ai.analyzer import AIAnalyzer
        a=AIAnalyzer.__new__(AIAnalyzer)
        a.structured_events=True
        a.allowed_event_urls={'https://example.com/0'}
        result=a._parse_response(json.dumps({'events':[self.event(0)],'signals':'额外事件'}))
        self.assertTrue(result.success)
        self.assertFalse(hasattr(result, 'signals'))
        self.assertEqual(len(result.events),1)
        self.assertFalse(a._parse_response('{"core_trends":"旧结构"}').success)
