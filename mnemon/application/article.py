from abc import (
    ABCMeta,  # @UnusedImport
    abstractmethod,
    )
from mnemon.model.article import (
    NewArticle,
    ArticleSource,
    ArticleID,
    Tag,
    )


class ReadArticleService(object):

    def __init__(self, article_repository):
        self._article_repository = article_repository

    def read_article(self, article_id):
        try:
            article_id = ArticleID(article_id)
        except ValueError:
            article = None
        else:
            article = self._article_repository.get(article_id)
            if article is not None:
                article = FullArticle(article)
        return article

    def read_unread_articles(self, page_number=1):
        page = Page(page_number, self.count_unread_articles())
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.unread(page.skipped,
                                                              page.size),
            page,
            )

    def count_unread_articles(self):
        return self._article_repository.count.unread()

    def read_favorite_articles(self, page_number=1):
        page = Page(page_number, self.count_favorite_articles())
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.favorites(page.skipped,
                                                                 page.size),
            page,
            )

    def count_favorite_articles(self):
        return self._article_repository.count.favorites()

    def read_archived_articles(self, page_number=1):
        page = Page(page_number, self.count_archived_articles())
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.archived(page.skipped,
                                                                page.size),
            page,
            )

    def count_archived_articles(self):
        return self._article_repository.count.archived()

    def read_deleted_articles(self, page_number=1):
        page = Page(page_number, self.count_deleted_articles())
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.deleted(page.skipped,
                                                               page.size),
            page,
            )

    def count_deleted_articles(self):
        return self._article_repository.count.deleted()

    def follow(self, tag_name, page_number=1):
        page = Page(page_number, Page._SIZE)
        tag = Tag(tag_name)
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.annotated_by(tag,
                                                                  page.skipped,
                                                                  page.size),
            page,
            )

    def search(self, query, page_number=1):
        page = Page(page_number, Page._SIZE)
        return ArticleList(
            AbstractArticle,
            lambda page: self._article_repository.find.search_by(query,
                                                                 page.skipped,
                                                                 page.size),
            page,
            )


class MemoriseArticleService(object):

    def __init__(self, content_extractor, article_repository):
        self._content_extractor = content_extractor
        self._article_repository = article_repository

    def memorise(self, url):
        """Memorises an article

        :param url: the URL of the article
        :type url: str
        :raise ValueError: if not a valid URL
        """
        source = ArticleSource(url)
        article_id = self._article_repository.next_identity()
        article = NewArticle(article_id, source)
        article.extract_content(self._content_extractor)
        self._article_repository.save(article)


class ManageArticleService(object):

    def __init__(self, article_repository):
        self._article_repository = article_repository

    def favorise(self, article_id):
        """Adds an article to favorites

        :param id: the article's ID
        :type url: str
        """
        article = self._article_repository.get(ArticleID(article_id))
        article.is_favorite = True
        self._article_repository.save(article)

    def unfavorise(self, article_id):
        """Removes an article from favorites

        :param article_id: the article's ID
        :type article_id: str
        """
        article = self._article_repository.get(ArticleID(article_id))
        article.is_favorite = False
        self._article_repository.save(article)

    def archive(self, article_id):
        """Archives an article

        :param article_id: the article's ID
        :type article_id: str
        """
        article = self._article_repository.get(ArticleID(article_id))
        # FIXME: archived articles cannot be archived again. Raise proper error
        article.archive()
        self._article_repository.save(article)

    def restore(self, article_id):
        """Restores an article

        :param article_id: the article's ID
        :type article_id: str
        """
        article = self._article_repository.get(ArticleID(article_id))
        article.restore()
        self._article_repository.save(article)

    def delete(self, article_id):
        """Deleted an article

        :param article_id: the article's ID
        :type article_id: str
        """
        article = self._article_repository.get(ArticleID(article_id))
        article.delete()
        self._article_repository.save(article)

    def purge(self, article_id):
        """Purge a deleted article by its ID

        :param article_id: the article's ID
        :type article_id: str
        """
        self._article_repository.purge(ArticleID(article_id))

    def purge_older_than(self, days=30):
        """Purge articles deleted more that the specified number of days ago

        :param days: number of days
        :type days: integer
        """
        self._article_repository.purge_older_than(days=days)

    def purge_all(self):
        """Purge all deleted articles"""
        self._article_repository.purge_all()

    def tag(self, article_id, tags):
        """Annotates an article with tags

        :param article_id: the article's ID
        :type article_id: str
        :param tags: list of tag names
        :type tags: list of strings
        :raise ValueError: if tag names are not valid
        """
        article = self._article_repository.get(ArticleID(article_id))
        article.tags = map(Tag, tags)
        self._article_repository.save(article)


class Page(object):

    _SIZE = 25

    def __init__(self, page_number, item_count):
        """
        :param page_number: a positive page number
        :type page_number: int
        :param item_count: the total number of items used for calculating the
                           next and previous pages
        :type item_count: int
        """
        if page_number < 1:
            raise ValueError('Page number should be a positive integer')
        if item_count < 0:
            raise ValueError('Item count should be a positive integer or zero')
        self._item_count = item_count
        self._page_number = page_number

    @property
    def number(self):
        return self._page_number

    @property
    def size(self):
        return self._SIZE

    @property
    def skipped(self):
        return (self.number - 1) * self.size

    @property
    def total(self):
        """Returns total number of pages"""
        return ((self._item_count // self.size) +
                int(bool(self._item_count % self.size)))

    @property
    def next(self):
        next_page = self.number + 1
        if next_page > self.total:
            return None
        else:
            return Page(next_page, self._item_count)

    @property
    def previous(self):
        previous_page = self.number - 1
        if previous_page < 1:
            return None
        else:
            return Page(previous_page, self._item_count)


class ArticleList(list):
    """Collection of Article Representations

    It is returned to the caller and is required from the
    presentation model.
    """

    def __init__(self, repr_adaptor, article_generator, page):
        self._repr_adaptor = repr_adaptor
        self._article_generator = article_generator
        self._page = page
        self._populate_list()

    @property
    def older_page(self):
        return self._page.next

    @property
    def newer_page(self):
        return self._page.previous

    def _populate_list(self):
        for article in self._article_generator(self._page):
            self.append(self._repr_adaptor(article))


class ArticleRepresentation(metaclass=ABCMeta):
    """Base class for article presentation model adaptors"""

    def __init__(self, article):
        self._article = article

    @property
    def id(self):
        return str(self._article.id)

    @property
    def source(self):
        return str(self._article._source)

    @property
    def title(self):
        return str(self._article.content.title)

    @property
    @abstractmethod
    def content(self):
        """The article presentation content"""

    @property
    def memorised_on(self):
        return self._article.content.extracted_on

    @property
    def tags(self):
        return sorted([str(tag) for tag in self._article.tags])

    @property
    def is_unread(self):
        return not (self.is_archived or self.is_deleted)

    @property
    def is_favorite(self):
        return self._article.is_favorite

    @property
    def is_archived(self):
        return not hasattr(self._article, 'archive')

    @property
    def is_deleted(self):
        return not hasattr(self._article, 'delete')


class AbstractArticle(ArticleRepresentation):
    """An article presentation with an abstract of content"""

    @property
    def content(self):
        return str(self._article.content.abstract)


class FullArticle(ArticleRepresentation):
    """An article presentation with full content"""

    @property
    def content(self):
        return str(self._article.content.body)
