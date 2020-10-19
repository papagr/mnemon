import unittest

import minimock
from minimock import Mock
from nose.plugins.attrib import attr
from pyramid import testing

from mnemon.web.views import HomePageView


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        minimock.restore()

    @attr('disabled')
    def test_home_view(self):
        request = testing.DummyRequest()
        request.db = Mock('db')
        request.db = {}
        request.db['articles'] = []
        home_view = HomePageView(request)
        result = home_view.get()
        self.assertFalse(result['contents'])
