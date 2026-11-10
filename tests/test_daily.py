import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from trendradar.daily import RedactedLog, cleanup, daily_lock, run_daily


class DailyTests(unittest.TestCase):
    now = datetime(2026, 11, 10, 20, tzinfo=timezone(timedelta(hours=8)))

    def test_same_day_completion_skips_but_next_day_runs(self):
        with tempfile.TemporaryDirectory() as folder, patch('trendradar.preview.run_preview',return_value=0) as preview:
            root = Path(folder)
            self.assertEqual(run_daily(root,self.now),0)
            self.assertEqual(run_daily(root,self.now),0)
            self.assertEqual(preview.call_count,1)
            self.assertEqual(run_daily(root,self.now+timedelta(days=1)),0)
            self.assertEqual(preview.call_count,2)
            preview.assert_called_with(no_open=True,days=7)

    def test_failed_run_can_retry_then_completion_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder, patch('trendradar.preview.run_preview',side_effect=[1,0]) as preview:
            root = Path(folder)
            self.assertEqual(run_daily(root,self.now),1)
            record = json.loads((root/'output/daily/latest.json').read_text(encoding='utf-8'))
            self.assertFalse(record['completed'])
            self.assertEqual(record['status'],'failed')
            self.assertEqual(run_daily(root,self.now),0)
            self.assertEqual(run_daily(root,self.now),0)
            self.assertEqual(preview.call_count,2)

    def test_live_lock_blocks_and_abandoned_filename_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'run.lock'
            with daily_lock(path) as first:
                self.assertTrue(first)
                with daily_lock(path) as second:
                    self.assertFalse(second)
            with daily_lock(path) as retry:
                self.assertTrue(retry)

    def test_exception_is_logged_as_failure_and_stale_running_state_can_retry(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'AI_API_KEY':'test-secret'}), patch('trendradar.preview.run_preview',side_effect=RuntimeError('test-secret unavailable')) as preview:
            root = Path(folder)
            self.assertEqual(run_daily(root,self.now),1)
            path = root/'output/daily/runs/2026-11-10.json'
            record = json.loads(path.read_text(encoding='utf-8'))
            self.assertFalse(record['completed'])
            self.assertNotIn('test-secret',Path(record['log']).read_text(encoding='utf-8'))
            # Interrupted processes can leave running state but no live OS lock.
            record.update(status='running',completed=False)
            path.write_text(json.dumps(record),encoding='utf-8')
            preview.side_effect = None
            preview.return_value = 0
            self.assertEqual(run_daily(root,self.now),0)

    def test_log_redacts_credentials_across_writes(self):
        output = io.StringIO()
        with patch.dict(os.environ,{'AI_API_KEY':'secret-key','AI_API_BASE':'https://private.invalid'}):
            log = RedactedLog(output)
            log.write('secret-')
            log.write('key at https://private.invalid\nunfinished secret-key')
            log.finish()
        self.assertNotIn('secret-key',output.getvalue())
        self.assertNotIn('private.invalid',output.getvalue())
        self.assertEqual(output.getvalue().count('<REDACTED>'),3)

    def test_cleanup_expires_only_cache_and_logs_not_report_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = ['output/evidence/old.json','output/daily/logs/old.log','output/preview/history/status.json']
            for name in old + ['output/evidence/fresh.json']:
                path = root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('{}')
                if name in old:
                    os.utime(path,(1,1))
            self.assertEqual(cleanup(root),2)
            self.assertTrue((root/old[2]).exists())
            self.assertTrue((root/'output/evidence/fresh.json').exists())
