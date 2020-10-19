import unittest

import minimock
from minimock import Mock
from nose.plugins.attrib import attr
from nose.tools import raises

from mnemon.model.article import ArticleSource


class TestArticleSource(unittest.TestCase):
    def setUp(self):
        self.valid_url = 'http://python.org/'
        self.valid_url_in_greek = ''  # TODO: test Greek URLs
        self.empty_url = ''
        self.invalid_url_scheme_file = 'file://tmp/data/dddwikipedia.html'
        self.content_extractor = Mock('ContentExtractService')
        self.demo_content = 'demo'
        self.content_extractor.extract_content.mock_returns = self.demo_content

    def tearDown(self):
        minimock.restore()

    def test_create_source_from_valid_url(self):
        source = ArticleSource(self.valid_url)
        self.assertEqual(self.valid_url, str(source))

    @raises(ValueError)
    def test_fail_create_source_from_empty_url(self):
        ArticleSource(self.empty_url)

    @attr('disabled')
    @raises(ValueError)
    def test_fail_create_source_from_invalid_url_file_scheme(self):
        ArticleSource(self.invalid_url_scheme_file)

    def test_content_extraction(self):
        source = ArticleSource(self.valid_url)
        extracted = source.extract_content(self.content_extractor)
        self.assertEqual(self.demo_content, extracted)