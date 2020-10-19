from mnemon.services.scheduler import init_scheduler
from mnemon.persistence.article import MongoDBArticleRepository
from mnemon.application.article import ManageArticleService
from mnemon.services.content import Arc90ContentExtractService, \
    FiveFiltersContentExtractService


def includeme(config):
    # Initialize and start scheduler for purging
    scheduler = init_scheduler()

    def create_db():
        db_conn = config.registry.db_conn
        db_url = config.registry.db_url
        db = db_conn[db_url.path[1:]]
        if db_url.username and db_url.password:
            db.authenticate(db_url.username, db_url.password)
        return db

    def purge_old():
        db = create_db()
        repository = MongoDBArticleRepository(db)
        service = ManageArticleService(repository)
        number_of_days = int(config.registry.settings['purge_deleted_after'])
        service.purge_older_than(days=number_of_days)
    scheduler.add_interval_job(purge_old, days=1)  # executed daily
    scheduler.start()

    # Initialize default content extractor
    extractor = config.registry.settings['extractor']
    if extractor == 'Arc90':
        def create_content_extractor(request):
            return Arc90ContentExtractService()
    elif extractor == 'FiveFilters':
        def create_content_extractor(request):
            service_url = config.registry.settings['fivefilters.url']
            apikey = config.registry.settings['fivefilters.apikey']
            return FiveFiltersContentExtractService(service_url, apikey)
    else:
        raise ValueError('Extractor "{}" not supported. '
                         'Check your configuration'.format(extractor))
    config.add_request_method(create_content_extractor,
                              'content_extractor', reify=True)
