import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from trendradar.ai.evidence import ArticleParser, fetch_evidence

class EvidenceFetchTests(unittest.TestCase):
    def test_extract_and_cache(self):
        response=MagicMock()
        response.status_code=200
        response.headers={'Content-Type':'text/html'}
        response.encoding='utf-8'
        response.iter_content.return_value=[('<main><nav>noise</nav><article>'+('Useful change. '*20)+'<script>secret</script></article></main>').encode()]
        response.__enter__.return_value=response
        with tempfile.TemporaryDirectory() as folder, patch('trendradar.ai.evidence.requests.get',return_value=response) as get:
            result=fetch_evidence('https://github.com/org/repo/releases/tag/v1',folder)
            self.assertEqual(result['status'],'ok')
            self.assertNotIn('noise',result['text'])
            self.assertNotIn('secret',result['text'])
            self.assertEqual(fetch_evidence(result['url'],folder),result)
            get.assert_called_once()

    def test_redirect_to_private_address_is_rejected(self):
        response=MagicMock(status_code=302,headers={'Location':'http://127.0.0.1/'})
        response.__enter__.return_value=response
        with tempfile.TemporaryDirectory() as folder, patch('trendradar.ai.evidence.requests.get',return_value=response) as get:
            result=fetch_evidence('https://github.com/test',folder)
            self.assertEqual(result['status'],'failed')
            get.assert_called_once()

    def test_timeout_falls_back(self):
        import requests
        with tempfile.TemporaryDirectory() as folder, patch('trendradar.ai.evidence.requests.get',side_effect=requests.Timeout):
            result=fetch_evidence('https://openai.com/index/test',folder)
            self.assertEqual(result['text'],'')
            self.assertEqual(result['reason'],'Timeout')
