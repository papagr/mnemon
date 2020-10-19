from mnemon.application.article import (
    MemoriseArticleService,
    ReadArticleService,
    ManageArticleService,
    )


def includeme(config):
    # Memorise Service
    def create_memorise_article_service(request):
        return MemoriseArticleService(request.content_extractor,
                                      request.article_repository)
    config.add_request_method(create_memorise_article_service,
                              'memorise_article_service', reify=True)

    # Read Article Service
    def create_read_article_service(request):
        return ReadArticleService(request.article_repository)
    config.add_request_method(create_read_article_service,
                              'read_article_service', reify=True)

    # Manage Article Service
    def create_manage_article_service(request):
        return ManageArticleService(request.article_repository)
    config.add_request_method(create_manage_article_service,
                              'manage_article_service', reify=True)
