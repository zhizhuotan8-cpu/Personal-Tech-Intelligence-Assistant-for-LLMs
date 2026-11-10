import unittest
from trendradar.ai.filter import AIFilter

class FilterResponseTests(unittest.TestCase):
    def test_invalid_response_is_retryable(self):
        f=AIFilter.__new__(AIFilter)
        f.debug=False
        for response in ('', 'not json', '{"error":"unavailable"}', '[broken'):
            with self.subTest(response=response):
                self.assertIsNone(f._parse_classify_response(response, [], []))

    def test_valid_empty_response_is_no_match(self):
        f=AIFilter.__new__(AIFilter)
        f.debug=False
        self.assertEqual(f._parse_classify_response('[]', [], []), [])
