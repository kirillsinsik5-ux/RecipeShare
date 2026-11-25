from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Recipe


def recipe_detail(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.select_related('category', 'author'), pk=pk, is_deleted=False)
    # неопубликованный рецепт видят только автор и модератор
    if recipe.status != Recipe.STATUS_PUBLISHED:
        user = request.user
        if not user.is_authenticated or (user.pk != recipe.author_id and not user.is_moderator):
            raise Http404
    items = recipe.recipe_ingredients.select_related('ingredient')
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe, 'items': items})
