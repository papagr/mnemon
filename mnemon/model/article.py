from abc import abstractmethod
from urllib.parse import urlparse
import uuid

import rfc3987

from mnemon.model.base import (
    ValueObject,
    Entity,
    Repository,
    Service,
    )
from mnemon.model.utils import now


class Content(ValueObject):

    def __init__(self, title=None, body=None, abstract=None, author=None,
                 published_on=None):
        self.title = title
        self.body = body
        self.abstract = abstract
        self.published_on = published_on
        self.author = author
        self.extracted_on = now()


class ContentExtractService(Service):
    """Abstract content extraction service

    Concrete implementation is expected in the infrastructure layer
    """

    @abstractmethod
    def extract_content(self, source):
        """Extract content from article source

        :param source: an article's source
        :type source: ArticleSource
        :return: Content
        """


class ArticleRepository(Repository):
    """Abstract article repository"""

    def next_identity(self):
        """Get the next ArticleID"""
        return ArticleID()

    @abstractmethod
    def get(self, article_id):
        """Get one article by ID

        Returned article's type depends on article status.
        """

    @property
    @abstractmethod
    def find(self):
        """Return an Article Finder"""

    @property
    @abstractmethod
    def count(self):
        """Return an Article Counter"""

    @abstractmethod
    def save(self, article):
        """Save a new article or article updates to repository"""

    @abstractmethod
    def purge(self, article):
        """Completely removes a deleted article from the repository"""

    @abstractmethod
    def purge_all(self):
        """Completely removes all deleted articles from the repository"""

    @abstractmethod
    def purge_older_than(self, days):
        """Completely removes articles older than the number of days"""


class ArticleFinder(object):
    """Abstract article finder"""

    @abstractmethod
    def unread(self, skip=0, limit=0):
        """Find all unread articles

        Returns ArticleView?
        """

    @abstractmethod
    def favorites(self, skip=0, limit=0):
        """Find all favorite articles that are unread or archived

        Returns ArticleView?
        """

    @abstractmethod
    def archived(self, skip=0, limit=0):
        """Find all archived articles

        Returns ArticleView?
        """

    @abstractmethod
    def deleted(self, skip=0, limit=0):
        """Find all deleted articles

        Returns ArticleView?
        """

    @abstractmethod
    def annotated_by(self, tag, skip=0, limit=0):
        """Find annotated articles by tag

        Returns ArticleView?

        Deleted articles are not part of the result.
        """

    def search_by(self, query, skip=0, limit=0):
        """Find articles by query string

        Returns ArticleView?

        Deleted articles are not part of the result.
        """


class ArticleCounter():
    """Counts articles"""

    @abstractmethod
    def unread(self):
        """Count all unread articles"""

    @abstractmethod
    def favorites(self):
        """Count all favorite articles that are unread or archived"""

    @abstractmethod
    def archived(self):
        """Count all archived articles"""

    @abstractmethod
    def deleted(self):
        """Count all deleted articles"""


class Article(Entity):
    """Abstract base Article"""

    def __init__(self, identity, source, content=None, tags=None,
                 favorized_on=None, transformed_on=None):
        self._id = identity
        self._source = source
        self._content = content
        self._favorized_on = favorized_on
        self._tags = tags if tags is not None else set()
        self._transformed_on = (transformed_on if transformed_on is not None
                                else now())

    @property
    def id(self):
        return self._id

    @property
    def source(self):
        return self._source

    @property
    def tags(self):
        return sorted(self._tags)

    @property
    def is_favorite(self):
        return self._favorized_on is not None

    @property
    def content(self):
        return self._content

    def _transform_to(self, klass):
        self._transformed_on = now()
        self.__class__ = klass

    def _set_tags(self, tag_list):
        self._tags = set(tag_list)

    def _make_favorite(self, boolean):
        self._favorized_on = now() if boolean else None


class NewArticle(Article):

    def __init__(self, identity, source, transformed_on=None):
        super().__init__(identity, source, transformed_on)

    def extract_content(self, content_extractor):
        """Extract article content using a content extractor

        :param content_extractor: the content extraction strategy
        :type content_extractor: ContentExtractService
        """
        self._content = content_extractor.extract_content(self._source)
        self._transform_to(UnreadArticle)


class UnreadArticle(Article):

    def __init__(self, identity, source, content=None, tags=None,
                 transformed_on=None):
        super().__init__(identity, source, content, tags, transformed_on)

    @property
    def created_on(self):
        return self._transformed_on

    @Article.tags.setter
    def tags(self, tag_list):
        self._set_tags(tag_list)

    @Article.is_favorite.setter
    def is_favorite(self, boolean):
        self._make_favorite(boolean)

    def archive(self):
        self._transform_to(ArchivedArticle)

    def delete(self):
        self._transform_to(DeletedArticle)


class ArchivedArticle(Article):

    def __init__(self, identity, source, content=None, tags=None,
                 transformed_on=None):
        super().__init__(identity, source, content, tags, transformed_on)

    @property
    def archived_on(self):
        return self._transformed_on

    @Article.tags.setter
    def tags(self, tag_list):
        self._set_tags(tag_list)

    @Article.is_favorite.setter
    def is_favorite(self, boolean):
        self._make_favorite(boolean)

    def restore(self):
        self._transform_to(UnreadArticle)

    def delete(self):
        self._transform_to(DeletedArticle)


class DeletedArticle(Article):

    @property
    def deleted_on(self):
        return self._transformed_on

    def restore(self):
        self._transform_to(UnreadArticle)


class ArticleSource(ValueObject):
    """A article's source

    An article's source is a value object and acts like an address.
    """

    def __init__(self, url):
        """Constructor

        :param url: the URL of the source
        :type url: str
        :raise ValueError: if not a valid URL
        """
        if not self._is_valid(url):
            raise ValueError('URL is invalid: {}'.format(url))
        self._url = urlparse(url)

    def __repr__(self):
        return '<{} url: {}>'.format(self.__class__.__name__, str(self._url))

    def __str__(self):
        return self._url.geturl()

    def _is_valid(self, url):
        """Check URL validity using RFC 3986 based regular expression"""
        # FIXME: disallow file:// scheme - security risk
        pattern = rfc3987.get_compiled_pattern('^%(URI)s$')
        return pattern.match(url) is not None


class ArticleID(ValueObject):
    """The article's ID"""

    def __init__(self, unique_id=None):
        """Constructs an ArticleID

        If no unique_id is provided then a new one is created.

        :param unique_id: a randomly created UUID or a string
        :type unique_id: UUID or str
        :raise ValueError: if the provided unique_id is not a valid UUID
        """
        if unique_id is None:
            unique_id = uuid.uuid4()
        elif isinstance(unique_id, str):
            unique_id = uuid.UUID(unique_id)
        self._unique_id = unique_id

    def __repr__(self):
        return '<{} uuid: {}>'.format(self.__class__.__name__, self._unique_id)

    def __str__(self):
        return str(self._unique_id)


class Tag(ValueObject):

    _MAX_LENGTH = 64

    def __init__(self, name):
        if not self._is_valid(name):
            raise ValueError('Tag "{}" is not valid'.format(name))
        self._name = name

    def __lt__(self, other):
        return self._name < other._name

    def __gt__(self, other):
        return self._name > other._name

    def __eq__(self, other):
        return self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return self._name

    def _is_valid(self, name):
        """Checks if a tag name is valid"""
        return isinstance(name, str) and len(name) <= self._MAX_LENGTH
