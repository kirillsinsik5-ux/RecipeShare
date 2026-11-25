from functools import wraps

from django.http import JsonResponse


def api_role_required(allowed_roles):
    """Для JSON-эндпоинтов: вместо HTML-страницы возвращает JSON с кодом 401/403."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Unauthorized',
                                     'message': 'Требуется вход в систему'}, status=401)
            if request.user.role not in allowed_roles:
                return JsonResponse({'error': 'Forbidden',
                                     'message': 'Недостаточно прав'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
