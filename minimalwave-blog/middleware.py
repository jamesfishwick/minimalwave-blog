from django.utils.cache import patch_response_headers

class CacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Don't cache admin pages
        if not request.path.startswith('/admin/'):
            if request.method == 'GET':
                # Cache public pages for 10 minutes
                patch_response_headers(response, cache_timeout=600)

                # Add cache control headers
                response['Cache-Control'] = 'public, max-age=600'

                # Add Vary header to respect mobile/desktop differences
                if 'Vary' in response:
                    response['Vary'] += ', User-Agent'
                else:
                    response['Vary'] = 'User-Agent'

        return response
