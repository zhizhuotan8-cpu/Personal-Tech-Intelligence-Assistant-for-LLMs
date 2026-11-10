"""Response-boundary regressions: HTTP success may still contain no answer."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from trendradar.ai.client import AIClient


def response(content, finish='stop'):
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=content), finish_reason=finish)])


class AIClientResponseTests(unittest.TestCase):
    def test_transient_empty_answer_is_retried(self):
        with patch('trendradar.ai.client.completion', side_effect=[response(None), response('{"events":[]}')]) as call:
            answer = AIClient({'NUM_RETRIES': 1}).chat([{'role':'user','content':'test'}])
        self.assertEqual(answer, '{"events":[]}')
        self.assertEqual(call.call_count, 2)

    def test_persistent_empty_answer_is_an_explicit_error(self):
        with patch('trendradar.ai.client.completion', return_value=response('  ', 'length')) as call:
            with self.assertRaisesRegex(RuntimeError, '空响应.*length'):
                AIClient({'NUM_RETRIES': 1}).chat([])
        self.assertEqual(call.call_count, 2)

    def test_valid_answer_is_not_retried(self):
        with patch('trendradar.ai.client.completion', return_value=response('ok')) as call:
            self.assertEqual(AIClient({}).chat([]), 'ok')
        self.assertEqual(call.call_count, 1)

    def test_missing_choices_is_explicit_failure_without_retry_budget(self):
        with patch('trendradar.ai.client.completion', return_value=SimpleNamespace(choices=[])) as call:
            with self.assertRaisesRegex(RuntimeError, '空响应.*unknown'):
                AIClient({'NUM_RETRIES':0}).chat([])
        self.assertEqual(call.call_count, 1)

    def test_text_blocks_are_used_but_reasoning_is_not_an_answer(self):
        with patch('trendradar.ai.client.completion', return_value=response([
            {'type':'reasoning','reasoning':'private'}, {'type':'text','text':'answer'}])):
            self.assertEqual(AIClient({}).chat([]), 'answer')

    def test_filtered_response_is_not_retried(self):
        with patch('trendradar.ai.client.completion', return_value=response(None,'content_filter')) as call:
            with self.assertRaisesRegex(RuntimeError, 'content_filter'):
                AIClient({'NUM_RETRIES':2}).chat([])
        self.assertEqual(call.call_count, 1)
