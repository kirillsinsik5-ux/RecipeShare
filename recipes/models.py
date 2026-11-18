# Create your models here.
# models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_AUTHOR = 'author'
    ROLE_MODERATOR = 'moderator'
    ROLE_CHOICES = [
        (ROLE_AUTHOR, 'Автор'),
        (ROLE_MODERATOR, 'Модератор'),
    ]

    email = models.EmailField('Email', max_length=150, unique=True)
    full_name = models.CharField('Имя', max_length=150)
    role = models.CharField('Роль', max_length=20,
                            choices=ROLE_CHOICES, default=ROLE_AUTHOR)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    class Meta:
        db_table = 'users'


class Category(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        db_table = 'ingredients'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_PUBLISHED = 'published'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_PENDING, 'На модерации'),
        (STATUS_PUBLISHED, 'Опубликован'),
        (STATUS_REJECTED, 'Отклонён'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='recipes')
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 related_name='recipes')
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    instructions = models.TextField('Шаги приготовления')
    cooking_time_min = models.PositiveIntegerField(
        'Время, мин', validators=[MinValueValidator(1)])
    servings = models.PositiveIntegerField(
        'Порции', default=2, validators=[MinValueValidator(1)])
    status = models.CharField('Статус', max_length=20,
                              choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_deleted = models.BooleanField(default=False)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient',
                                         related_name='recipes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['author']),
                   models.Index(fields=['category']),
                   models.Index(fields=['status'])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=['draft', 'pending', 'published', 'rejected']),
                name='ck_recipes_status'),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=20)

    class Meta:
        db_table = 'recipe_ingredients'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='uq_recipe_ingredient'),
        ]


class ModerationReview(models.Model):
    DECISION_CHOICES = [('approved', 'Одобрен'), ('rejected', 'Отклонён')]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='reviews')
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name='moderation_reviews')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'moderation_reviews'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_token'
        indexes = [models.Index(fields=['user']),
                   models.Index(fields=['expires_at'])]

    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()