import math
import re
import operator
import datetime

from bs4 import (
    BeautifulSoup,
    Comment,
    )
import requests

from mnemon.model.article import ContentExtractService, Content


class Arc90ContentExtractService(ContentExtractService):
    """Simple implementation of a service"""

    def extract_content(self, source):
        html = requests.get(str(source))
        return html_to_content(html.text)


class FiveFiltersContentExtractService(ContentExtractService):
    """FiveFilters implementation of ContentExtractService"""

    def __init__(self, service_url, apikey):
        self._service_url = service_url
        self._apikey = apikey

    def extract_content(self, source):
        rss_feed = requests.get(self._service_url,
                                params={'url': str(source),
                                        'key': self._apikey,
                                        'summary': 1,
                                        'max': 1})
        return rss_to_content(rss_feed.text)


class Arc90ContentTranslator(object):
    """Simple implementation of Arc90's Readability algorithm

    For the original code in JavaScript see:
    http://code.google.com/p/arc90labs-readability/source/browse/trunk/js/readability.js

    1. Remove HTML elements that are known to not contain text e.g. SCRIPT,
       STYLE, etc.
    2. Read all paragraphs in the HTML page and for each paragraph:
       a) Calculate a weight for each paragraph based on a set of rules on
          how likely it is to contain the article's text. E.g.:
          * If the parent element has a positive class/id attribute
            (e.g. content, text, etc.), increase the weight.
          * If the parent element has a negative class/id attribute
            (e.g. comment, footer, etc.), decrease the weight.
       b) Find the parent element of the paragraph and associate the weight
       c) Find the grand parent element of the paragraph and associate half of
          parent element's weight.
    3. Retrieve all weighted elements, find the one with the highest weight
       and use it as the article's main body.

    Regular expressions and logic has been adopted by the original code.
    """
    ABSTRACT_LENGTH = 200

    # CONSTANTS used in weighting
    POSITIVE_WEIGHT = 25
    NEGATIVE_WEIGHT = 25

    REMOVE_ELEMENTS = ('code', 'style', 'script', 'link', 'nav')
    REPLACE_ELEMENTS = (('font', 'span'),)
    REPLACE_BREAKS = re.compile(r'(<br[^>]*>[ \n\r\t]*){2,}', re.IGNORECASE)
    KILL_BREAKS = re.compile(r'(<br\s*\/?>(\s|&nbsp;?)*){1,}', re.IGNORECASE)
    POSITIVE_SCORE = re.compile(
        r'article|body|content|entry|hentry|main|page|pagination|post|text'
        r'|blog|story',
        re.IGNORECASE)
    NEGATIVE_SCORE = re.compile(
        r'combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta'
        r'|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping'
        r'|tags|tool|widget',
        re.IGNORECASE)
    UNLIKELY_CLASS_OR_IDS = re.compile(
        r'nav-|comment|xoxo|download',
        re.IGNORECASE)
    UNLIKELY_ELEMENTS = re.compile(
        r'!(a|blockquote|dl|div|img|ol|p|pre|table|ul)',
        re.IGNORECASE)

    def __call__(self, html_text):
        # pre-process the text
        html_text = self._treat_breaks(html_text)
        # create the parser
        soup = BeautifulSoup(html_text)
        # initial cleaning of the document
        self._clean_document(soup)
        # weight elements
        self._weight_elements(soup)
        # find element with highest weight
        candidate = max(soup.find_all(weight=True),
                        key=operator.itemgetter('weight'))
        # clean candidate
        self._clean_candidate(candidate)
        # create and return Content
        title = self._get_title(soup)
        body = candidate.prettify()
        abstract = candidate.get_text()[:self.ABSTRACT_LENGTH]

        return Content(title, body, abstract)

    def _treat_breaks(self, html_text):
        html_text = re.sub(self.KILL_BREAKS, '<br />', html_text)
        html_text = re.sub(self.REPLACE_BREAKS, '</p><p>', html_text)
        return html_text

    def _clean_document(self, soup):
        for from_elem, to_elem in self.REPLACE_ELEMENTS:
            self._replace_element(soup, from_elem, to_elem)

        for element in self.REMOVE_ELEMENTS:
            self._remove_element(soup, element)

        self._remove_comments(soup)

    def _clean_candidate(self, candidate):
        for attr in ('class', 'id'):
            for element in candidate.find_all(
                                     attrs={attr: self.UNLIKELY_CLASS_OR_IDS}):
                element.extract()
        for element in candidate.find_all(
                                         attrs={attr: self.UNLIKELY_ELEMENTS}):
            if not element.get_text().strip():
                element.extract()

    def _weight_elements(self, soup):
        """For each paragraph, calculate a weight and assign the weight to
        the parent element.
        """

        for p in soup.find_all('p'):
            parent = self._get_parent(p)
            grandparent = self._get_parent(parent)
            content_text = p.get_text().strip()

            content_weight = 1
            # add scores for each comma
            content_weight += len(content_text.split(','))
            # for every 100 characters in this paragraph, add another point but
            # up to 3 points only
            content_weight += min(math.floor(len(content_text) / 100), 3)

            parent['weight'] += content_weight
            grandparent['weight'] += int(content_weight / 2)

    def _get_parent(self, element):
        parent = element.parent
        if parent is None:
            parent = {'weight': 0}  # sometimes there is no parent
        elif not parent.has_attr('weight'):
            self._initialize_weight(parent)
        return parent

    def _remove_element(self, soup, element):
        for element in soup.find_all(element):
            element.extract()

    def _remove_comments(self, soup):
        comments = soup.find_all(text=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

    def _replace_element(self, soup, from_element, to_element):
        for element in soup.find_all(from_element):
            element.name = to_element
            element.attrs = {}

    def _get_title(self, soup):
        title = None
        if soup.title:
            title = soup.title.get_text()
        return title

    def _initialize_weight(self, element):
        element['weight'] = 0
        if element.name == 'div':
            element['weight'] += 5
        elif element['weight'] in ('pre', 'td', 'blockquote'):
            element['weight'] += 3
        elif element['weight'] in ('address', 'ol', 'ul', 'dl', 'dd', 'dt',
                                   'li', 'form'):
            element['weight'] -= 3
        elif element['weight'] in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th'):
            element['weight'] -= 5
        element['weight'] += self._get_class_weight(element)

    def _get_class_weight(self, element):
        weight = 0
        for attr in ('class', 'id'):
            if element.has_attr(attr):
                if self.NEGATIVE_SCORE.match(str(element[attr])):
                    weight -= self.NEGATIVE_WEIGHT
                elif self.POSITIVE_SCORE.match(str(element[attr])):
                    weight += self.POSITIVE_WEIGHT
        return weight


def rss_to_content(rss_text):
    soup = BeautifulSoup(rss_text)
    item = soup.find_all('item')[0]
    title = item.title.text
    body = item.find('content:encoded').text
    abstract = item.description.text
    try:
        author = item.find('dc:creator').text
    except AttributeError:
        author = None
    try:
        published_on = datetime.datetime.strptime(item.pubdate.text,
                                                  '%a, %d %b %Y %H:%M:%S %z')
    except AttributeError:
        published_on = None
    return Content(title, body, abstract, author, published_on)


html_to_content = Arc90ContentTranslator()
