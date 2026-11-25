from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Category, Ingredient, ModerationReview, PasswordResetToken,
                     Recipe, RecipeIngredient, User)


@admin.register(User)
class RecipeUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'full_name', 'role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (('RecipeShare', {'fields': ('full_name', 'role')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('RecipeShare', {'fields': ('email', 'full_name', 'role')}),)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 3                      # три пустые строки для новых ингредиентов
    autocomplete_fields = ['ingredient']
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Состав рецепта'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']       # нужно для autocomplete_fields


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title',)
    inlines = [RecipeIngredientInline]


admin.site.register(Category)
admin.site.register(ModerationReview)
admin.site.register(PasswordResetToken)