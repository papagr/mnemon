import logging
from abc import ABCMeta
from collections import namedtuple

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    HTTPUnauthorized,
    )
from pyramid.response import Response
from pyramid.view import (
    view_config,
    view_defaults,
    forbidden_view_config,
    notfound_view_config,
    )
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Everyone,
    Authenticated,
    remember,
    forget,
    authenticated_userid,
    )


from mnemon.web.utils import get_security_token
from webob.exc import HTTPBadRequest

log = logging.getLogger(__name__)

ArticleCounts = namedtuple('ArticleCounts',
                           'unread favorites archived deleted')
NavigationTab = namedtuple('NavigationTab', 'name title')


class RootFactory(object):
    __acl__ = [(Allow, Everyone, 'authenticate'),
               (Allow, Everyone, 'memorize'),
               (Allow, Authenticated, ALL_PERMISSIONS)]

    def __init__(self, request):
        pass


class NavigationTabs(object):
    UNREAD = NavigationTab('UNREAD', 'Reading List')
    ARCHIVED = NavigationTab('ARCHIVED', 'Archived')
    FAVORITES = NavigationTab('FAVORITES', 'Favorites')
    DELETED = NavigationTab('DELETED', 'Deleted')
    ALL = (UNREAD, FAVORITES, ARCHIVED, DELETED)

    def __init__(self, active=None):
        self.active = active


class PageView(object):

    __metaclass__ = ABCMeta

    def __init__(self, request):
        self.request = request


class ArticleListPageView(PageView):

    def __init__(self, request):
        super().__init__(request)
        self.tabs = NavigationTabs()

    @property
    def counts(self):
        """Returns a named tuple of article counts

        This function is used during rendering the templates
        """
        service = self.request.read_article_service
        return ArticleCounts(service.count_unread_articles(),
                             service.count_favorite_articles(),
                             service.count_archived_articles(),
                             service.count_deleted_articles())


@view_defaults(route_name='home')
class HomePageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET')
    def get(self):
        return HTTPFound(location=self.request.route_url('unread'))

    @view_config(request_method='POST', permission='memorize')
    def post(self):
        token = self.request.POST.get('token', None)
        if token != get_security_token(self.request):
            log.debug('Token %s not recognized!', token)
            return HTTPUnauthorized('Token not recognized!')

        url = self.request.POST['url']
        if url.startswith(self.request.route_url('home')):
            return Response('Skipping %s' % url)
        else:
            self.request.memorise_article_service.memorise(url)
            return Response('Downloaded %s' % url)


@view_defaults(route_name='unread')
class UnreadPageView(ArticleListPageView):

    def __init__(self, request):
        super().__init__(request)
        self.tabs.active = NavigationTabs.UNREAD

    @view_config(request_method='GET', renderer='templates/unread.pt')
    def get(self):
        page_number = int(self.request.GET.get('page', 1))
        service = self.request.read_article_service
        items = service.read_unread_articles(page_number)
        return {'contents': items}

    @view_config(request_method='POST')
    def post(self):
        article_id = self.request.POST['article_id']
        service = self.request.manage_article_service
        service.restore(article_id)
        return Response('Restored %s' % article_id)


@view_defaults(route_name='favorites')
class FavoritesPageView(ArticleListPageView):

    def __init__(self, request):
        super().__init__(request)
        self.tabs.active = NavigationTabs.FAVORITES

    @view_config(request_method='GET', renderer='templates/favorites.pt')
    def get(self):
        page_number = int(self.request.GET.get('page', 1))
        service = self.request.read_article_service
        items = service.read_favorite_articles(page_number)
        return {'contents': items}

    @view_config(request_method='POST')
    def post(self):
        article_id = self.request.POST['article_id']
        service = self.request.manage_article_service
        service.favorise(article_id)
        return Response('Favorised %s' % article_id)


@view_defaults(route_name='archived')
class ArchivedPageView(ArticleListPageView):
    def __init__(self, request):
        super().__init__(request)
        self.tabs.active = NavigationTabs.ARCHIVED

    @view_config(request_method='GET', renderer='templates/archived.pt')
    def get(self):
        page_number = int(self.request.GET.get('page', 1))
        service = self.request.read_article_service
        items = service.read_archived_articles(page_number)
        return {'contents': items}

    @view_config(request_method='POST')
    def post(self):
        article_id = self.request.POST['article_id']
        service = self.request.manage_article_service
        service.archive(article_id)
        return Response('Archived %s' % article_id)


@view_defaults(route_name='deleted')
class DeletedPageView(ArticleListPageView):

    def __init__(self, request):
        super().__init__(request)
        self.tabs.active = NavigationTabs.DELETED

    @view_config(request_method='GET', renderer='templates/deleted.pt')
    def get(self):
        page_number = int(self.request.GET.get('page', 1))
        service = self.request.read_article_service
        items = service.read_deleted_articles(page_number)
        return {'contents': items}

    @view_config(request_method='POST')
    def post(self):
        article_id = self.request.POST['article_id']
        service = self.request.manage_article_service
        service.delete(article_id)
        return Response('Deleted %s' % article_id)

    @view_config(request_method='DELETE')
    def delete(self):
        service = self.request.manage_article_service
        service.purge_all()
        return Response('Purged All')


@view_defaults(route_name='favorite-article')
class FavoriteArticlePageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='DELETE')
    def delete(self):
        article_id = self.request.matchdict['article_id']
        service = self.request.manage_article_service
        service.unfavorise(article_id)
        return Response('Unfavorised %s' % article_id)


@view_defaults(route_name='article')
class ReadArticlePageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET', renderer='templates/article.pt')
    def get(self):
        service = self.request.read_article_service
        article_id = self.request.matchdict['article_id']
        item = service.read_article(article_id)
        if item is None:
            raise HTTPNotFound('Article with ID {} not found!'.format(
                                                                article_id))
        return {'item': item}

    @view_config(request_method='DELETE')
    def delete(self):
        article_id = self.request.matchdict['article_id']
        service = self.request.manage_article_service
        service.purge(article_id)
        return Response('Purged %s' % article_id)


@view_defaults(route_name='counts')
class CountsPageView(ArticleListPageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET', renderer='json')
    def get(self):
        counts = self.counts
        return {'unread': counts.unread,
                'favorites': counts.favorites,
                'archived': counts.archived,
                'deleted': counts.deleted}


@view_defaults(route_name='tags-by-name')
class BrowseByTagNamePageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET', renderer='templates/tagname.pt')
    def get(self):
        service = self.request.read_article_service
        page_number = int(self.request.GET.get('page', 1))
        tag_name = self.request.matchdict['tag_name']
        items = service.follow(tag_name, page_number)
        return {'contents': items, 'tag': tag_name}


@view_defaults(route_name='article-tags')
class ArticleTagsPageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='POST')
    def post(self):
        article_id = self.request.POST['article_id']
        tag_names = [tag.strip()
                     for tag in self.request.POST['tags'].split(',')]
        service = self.request.manage_article_service
        try:
            service.tag(article_id, tag_names)
        except ValueError as error:
            response = HTTPBadRequest(error)
            response.text = str(error)
            response.content_type = 'application/text'
            return response
        else:
            return Response('Tagged %s' % article_id)


@view_defaults(route_name='search')
class SearchArticlePageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET', renderer='templates/search-results.pt')
    def get(self):
        service = self.request.read_article_service
        page_number = int(self.request.GET.get('page', 1))
        query = self.request.GET.get('query', None)
        if query is not None:
            items = service.search(query, page_number)
        else:
            items = []
        return {'contents': items, 'query': query}


@view_defaults(route_name='login')
class LoginPageView(PageView):

    def __init__(self, request):
        super().__init__(request)

    @view_config(request_method='GET', renderer='templates/login.pt',
                 permission='authenticate')
    @forbidden_view_config(renderer='templates/login.pt')
    def get(self):
        login_path = self.request.route_path('login')
        came_from_url = (self.request.route_url('home')
                         if self.request.path == login_path
                         else self.request.url)
        return dict(message='', came_from=came_from_url)

    @view_config(request_method='POST', permission='authenticate',
                 renderer='templates/login.pt')
    def post(self):
        came_from_url = self.request.params.get('came_from',
                                                self.request.route_url('home'))
        valid_username = self.request.registry.settings['username']
        valid_password = self.request.registry.settings['password']
        username = self.request.params['username']
        password = self.request.params['password']
        if username == valid_username and password == valid_password:
            headers = remember(self.request, username)
            return HTTPFound(location=came_from_url, headers=headers)
        else:
            return dict(
                message='Failed to login! Please, try again.',
                came_from=came_from_url,
                )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('home'), headers=headers)


@notfound_view_config(renderer='templates/notfound.pt')
def notfound(request):
    if authenticated_userid(request) is None:
        return HTTPFound(location='/')
    return {}
