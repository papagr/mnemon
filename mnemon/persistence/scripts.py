import os
import sys
from urllib.parse import urlparse


import pymongo
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def init_mongodb(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    # Initialize DB connection
    db_url = urlparse(settings['mongodb.url'])
    db_conn = pymongo.MongoClient(db_url.hostname, db_url.port)
    db = db_conn[db_url.path[1:]]
    if db_url.username and db_url.password:
        db.authenticate(db_url.username, db_url.password)

    db.articles.create_index([('tags', 'text'),
                              ('content.title', 'text'),
                              ('content.body', 'text')],
                             weights={'content.title': 10,
                                      'tags': 5,
                                      'content.body': 1},
                             )
