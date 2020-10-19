import os
import unittest
import uuid
import urllib

import minimock
from minimock import Mock

from mnemon.application.article import MemoriseArticleService
from mnemon.model.article import ArticleID

HERE = os.path.abspath(os.path.dirname(__file__))


class MemoriseArticleTests(unittest.TestCase):

    def setUp(self):
        self.created_article = None
        content_extractor = Mock('ContentExtractor')
        article_repository = Mock('ArticleRepository')
        self.article_id = ArticleID(uuid.uuid4())
        article_repository.next_identity.mock_returns = self.article_id
        article_repository.save = lambda a: setattr(self,
                                                    'created_article', a)
        self.service = MemoriseArticleService(content_extractor,
                                              article_repository)

    def tearDown(self):
        self.article_id = None
        self.service = None
        minimock.restore()

    def test_read_url_later(self):
        url = 'file://{}/data/dddwikipedia.html'.format(HERE)
        url = urllib.parse.quote(url, safe='/:')
        self.service.memorise(url)
        self.assertEqual(self.article_id, self.created_article.id,
                         'Article IDs differ')
