from urllib.parse import urlparse
from pymongo import MongoClient

from mnemon.persistence.article import MongoDBArticleRepository


def includeme(config):
    # Initialize DB connection
    db_url = urlparse(config.registry.settings['mongodb.url'])
    db_conn = MongoClient(db_url.hostname, db_url.port)
    config.registry.db_url = db_url
    config.registry.db_conn = db_conn

    def create_db(request):
        db = db_conn[db_url.path[1:]]
        if db_url.username and db_url.password:
            db.authenticate(db_url.username, db_url.password)
        return db

    config.add_request_method(create_db, 'db', reify=True)

    # Initialize article repository
    def create_article_repository(request):
        return MongoDBArticleRepository(request.db)
    config.add_request_method(create_article_repository,
                              'article_repository', reify=True)
