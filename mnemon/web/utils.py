import urllib
import hashlib

from pkg_resources import resource_string  # @UnresolvedImport


def get_security_token(request):
    if get_security_token._cached_token is None:
        username = request.registry.settings['username']
        password = request.registry.settings['password']
        token = hashlib.sha1()
        token.update((username + password).encode('utf-8'))
        get_security_token._cached_token = token.hexdigest()
    return get_security_token._cached_token

get_security_token._cached_token = None


def bookmarklet_minified(request):
    if bookmarklet_minified._cached_bookmarklet is None:
        home_url = request.route_url('home')
        security_token = get_security_token(request)
        jquery_url = request.static_url('mnemon:web/static/js/jquery.min.js')
        bookmarklet_js = resource_string('mnemon',
                                         'web/static/js/bookmarklet.js'
                                         ).decode() % locals()
        href = 'javascript:{0}'.format(urllib.parse.quote(bookmarklet_js,
                                                          safe=',:;/()$!='))
        bookmarklet_minified._cached_bookmarklet = href
    return bookmarklet_minified._cached_bookmarklet

bookmarklet_minified._cached_bookmarklet = None
