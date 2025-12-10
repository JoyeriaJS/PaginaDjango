from django.http import HttpResponseForbidden

ALLOWED_IPS = [
    "181.42.163.131",
]

class AllowOnlySpecificIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or request.META.get("REMOTE_ADDR")

        if ip not in ALLOWED_IPS:
            return HttpResponseForbidden("403 Forbidden - Acceso restringido")

        return self.get_response(request)
