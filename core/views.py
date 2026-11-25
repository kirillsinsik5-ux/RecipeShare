from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

from recipes.models import Category, Recipe


def index(request):
    """Главная: каталог опубликованных рецептов с поиском и фильтром по категории."""
    recipes = (Recipe.objects
               .filter(status=Recipe.STATUS_PUBLISHED, is_deleted=False)
               .select_related('category', 'author'))
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    if query:
        recipes = recipes.filter(title__icontains=query)
    if category_id.isdigit():
        recipes = recipes.filter(category_id=int(category_id))

    page = Paginator(recipes, 9).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'core/index.html', {
        'page': page,
        'categories': Category.objects.order_by('name'),
        'query': query,
        'category_id': category_id,
        'querystring': params.urlencode(),
    })


def health(request):
    return JsonResponse({'status': 'ok', 'service': 'web'})
