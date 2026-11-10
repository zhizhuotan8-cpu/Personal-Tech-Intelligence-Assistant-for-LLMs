import unittest
from unittest.mock import MagicMock
from trendradar.__main__ import NewsAnalyzer

class CollectionFlowTests(unittest.TestCase):
    def test_collection_switches(self):
        for hotlist, rss in ((False, True), (True, False), (True, True), (False, False)):
            with self.subTest(hotlist=hotlist, rss=rss):
                runner = NewsAnalyzer.__new__(NewsAnalyzer)
                runner.ctx = MagicMock()
                runner.ctx.config = {'ENABLE_CRAWLER': hotlist, 'ENABLE_NOTIFICATION': False, 'DEBUG': True}
                runner.ctx.rss_enabled = rss
                runner.report_mode = 'daily'
                runner._has_notification_configured = MagicMock(return_value=False)
                runner._crawl_data = MagicMock(return_value=({}, {}, []))
                runner._crawl_rss_data = MagicMock(return_value=([], [], [], set()))
                runner._execute_mode_strategy = MagicMock()
                runner.run()
                self.assertEqual(runner._crawl_data.call_count, int(hotlist))
                self.assertEqual(runner._execute_mode_strategy.call_count, int(hotlist or rss))
                if rss:
                    runner._crawl_rss_data.assert_called_once()
                runner.ctx.cleanup.assert_called_once()
