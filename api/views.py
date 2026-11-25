from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .decorators import api_role_required

User = get_user_model()


def ping(request):
    return JsonResponse({'ping': 'pong'})


@api_role_required([User.ROLE_MODERATOR])
def admin_stats(request):
    return JsonResponse({
        'users_total': User.objects.count(),
        'users_active': User.objects.filter(is_active=True).count(),
    })
