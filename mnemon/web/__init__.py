from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application.
    """
    # Initialize Authentication/Authorization
    authn_policy = AuthTktAuthenticationPolicy(settings['secret'])
    authz_policy = ACLAuthorizationPolicy()
    # Configure Pyramid
    config = Configurator(settings=settings,
                          root_factory='mnemon.web.views.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_default_permission('view')
    config.add_static_view('static', 'mnemon:web/static/',
                           cache_max_age=3600)

    # Include infrastructure related configuration
    config.include('mnemon.persistence')
    config.include('mnemon.services')
    config.include('mnemon.application')

    # Configure routes
    config.add_route('home', '/')
    config.add_route('unread', '/unread')
    config.add_route('favorites', '/favorites')
    config.add_route('favorite-article', '/favorites/{article_id}')
    config.add_route('archived', '/archived')
    config.add_route('deleted', '/deleted')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('counts', '/counts')
    config.add_route('search', '/search')
    config.add_route('tags-by-name', '/tags/{tag_name}')
    config.add_route('article', '/article/{article_id}')
    config.add_route('article-tags', '/article/{article_id}/tags')
    config.scan('mnemon.web.views')
    return config.make_wsgi_app()
