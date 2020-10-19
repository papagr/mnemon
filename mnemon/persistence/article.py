import pymongo
from bson.binary import UUID

from mnemon.model import article as article_model
from mnemon.model.article import (
    ArticleRepository,
    ArticleID,
    ArticleSource,
    Content,
    ArticleFinder,
    ArticleCounter,
    Tag)
from mnemon.model.utils import past_datetime_by


class MongoDBArticleRepository(ArticleRepository):

    __collection_name = 'articles'
    __collection = None
    __db = None

    def __init__(self, db):
        self.__db = db
        self.__collection = self.__db[self.__collection_name]

    def get(self, article_id):
        doc = self.__collection.find_one({'_id': UUID(str(article_id))})
        if doc is not None:
            doc = self.__article_factory(doc)
        return doc

    @property
    def find(self):
        return MongoDBArticleFinder(self.__collection,
                                    self.__article_factory)

    @property
    def count(self):
        return MongoDBArticleCounter(self.__collection)

    def save(self, article):
        key, document = self.__document_factory(article)
        self.__collection.update(key, {'$set': document},
                                 upsert=True, safe=True)

    def purge(self, article_id):
        spec = {'type': 'DeletedArticle',
                '_id': UUID(str(article_id))}
        self.__collection.remove(spec)

    def purge_all(self):
        spec = {'type': 'DeletedArticle'}
        self.__collection.remove(spec)

    def purge_older_than(self, days):
        """
        See also Expire Data from Collections by Setting TTL
        at http://docs.mongodb.org/manual/tutorial/expire-data/
        """
        spec = {'type': 'DeletedArticle'}
        expire_date = past_datetime_by(days)
        spec.update({'transformed_on': {"$lt": expire_date}})
        self.__collection.remove(spec)

    def __article_factory(self, document):
        klass = getattr(article_model, document['type'])
        article_id = ArticleID(document['_id'])
        source = ArticleSource(document['source'])
        content = Content()
        content.__dict__ = document['content']
        article = klass(article_id, source, content)
        article._transformed_on = document['transformed_on']
        article._favorized_on = document['favorized_on']
        article._tags = set(Tag(name) for name in document['tags'])
        return article

    def __document_factory(self, article):
        key = dict(_id=article.id._unique_id)
        document = dict(
            type=article.__class__.__name__,
            transformed_on=article._transformed_on,
            favorized_on=article._favorized_on,
            source=str(article.source),
            content=article._content.__dict__,
            tags=[tag._name for tag in article.tags],
        )
        return key, document


class MongoDBArticleFinder(ArticleFinder):

    __collection = None
    __factory = None

    def __init__(self, collection, factory):
        self.__collection = collection
        self.__factory = factory

    def unread(self, skip=0, limit=0):
        spec = {'type': 'UnreadArticle'}
        fields = {'content.body': 0}
        cursor = self._sorted(self.__collection.find(spec, fields,
                                                     skip, limit))
        return list(map(self.__factory, cursor))

    def favorites(self, skip=0, limit=0):
        spec = {'type': {'$in': ['UnreadArticle', 'ArchivedArticle']},
                'favorized_on': {'$ne': None}}
        fields = {'content.body': 0}
        cursor = self._sorted_favorized(self.__collection.find(spec, fields,
                                                               skip, limit))
        return list(map(self.__factory, cursor))

    def archived(self, skip=0, limit=0):
        spec = {'type': 'ArchivedArticle'}
        fields = {'content.body': 0}
        cursor = self._sorted(self.__collection.find(spec, fields,
                                                     skip, limit))
        return list(map(self.__factory, cursor))

    def deleted(self, skip=0, limit=0):
        spec = {'type': 'DeletedArticle'}
        fields = {'content.body': 0}
        cursor = self._sorted(self.__collection.find(spec, fields,
                                                     skip, limit))
        return list(map(self.__factory, cursor))

    def annotated_by(self, tag, skip=0, limit=0):
        spec = {'type': {'$ne': 'DeletedArticle'},
                'tags': str(tag)}
        fields = {'content.body': 0}
        cursor = self._sorted(self.__collection.find(spec, fields,
                                                     skip, limit))
        return list(map(self.__factory, cursor))

    def search_by(self, query, skip=0, limit=0):
        db = self.__collection.database
        found = db.command('text', 'articles',
            search=query,
            filter={'type': {'$ne': 'DeletedArticle'}},
            project={'content.body': 0},
            )
        docs = [self.__factory(res['obj']) for res in found['results']]
        return docs

    def _sorted(self, cursor):
        return cursor.sort('transformed_on', pymongo.DESCENDING)

    def _sorted_favorized(self, cursor):
        return cursor.sort('favorized_on', pymongo.DESCENDING)


class MongoDBArticleCounter(ArticleCounter):

    __collection = None
    __factory = None

    def __init__(self, collection):
        self.__collection = collection

    def unread(self):
        spec = {'type': 'UnreadArticle'}
        return self.__collection.find(spec).count()

    def favorites(self):
        spec = {'type': {'$in': ['UnreadArticle', 'ArchivedArticle']},
                'favorized_on': {'$ne': None}}
        return self.__collection.find(spec).count()

    def archived(self):
        spec = {'type': 'ArchivedArticle'}
        return self.__collection.find(spec).count()

    def deleted(self):
        spec = {'type': 'DeletedArticle'}
        return self.__collection.find(spec).count()
