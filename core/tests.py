from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from recipes.models import Category, Recipe

User = get_user_model()


class CatalogTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='a', email='a@example.com', password='Str0ng-Pass-2026', full_name='Автор')
        self.other = User.objects.create_user(
            username='o', email='o@example.com', password='Str0ng-Pass-2026', full_name='Другой')
        self.mod = User.objects.create_user(
            username='m', email='m@example.com', password='Str0ng-Pass-2026',
            full_name='Модер', role=User.ROLE_MODERATOR)
        self.cat = Category.objects.create(name='Супы')
        make = lambda title, status: Recipe.objects.create(
            author=self.author, category=self.cat, title=title, instructions='Шаг 1\nШаг 2',
            cooking_time_min=20, status=status)
        self.pub = make('Борщ', Recipe.STATUS_PUBLISHED)
        self.draft = make('Черновик супа', Recipe.STATUS_DRAFT)

    def test_index_semantics_and_published_only(self):
        r = self.client.get(reverse('core:index'))
        self.assertContains(r, 'Борщ')
        self.assertNotContains(r, 'Черновик супа')
        for tag in ('<header', '<nav', '<main', '<footer', 'lang="ru"', 'skip-link'):
            self.assertContains(r, tag)

    def test_search_and_filter(self):
        self.assertContains(self.client.get(reverse('core:index'), {'q': 'орщ'}), 'Борщ')
        self.assertNotContains(self.client.get(reverse('core:index'), {'q': 'пицца'}), 'Борщ')
        self.assertContains(self.client.get(reverse('core:index'), {'category': self.cat.id}), 'Борщ')

    def test_bad_category_param_does_not_crash(self):
        self.assertEqual(self.client.get(reverse('core:index'), {'category': 'abc', 'page': 'x'}).status_code, 200)

    def test_detail_visibility(self):
        self.assertEqual(self.client.get(reverse('recipes:detail', args=[self.pub.id])).status_code, 200)
        url = reverse('recipes:detail', args=[self.draft.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.mod)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_forms_have_labels_and_aria_invalid(self):
        r = self.client.post(reverse('accounts:register'), {
            'email': 'bad', 'username': 'x', 'full_name': 'X', 'password1': '1', 'password2': '2'})
        self.assertContains(r, '<label for="id_email">')
        self.assertContains(r, 'aria-invalid="true"')
        self.assertContains(r, 'role="alert"')

    def test_health(self):
        self.assertEqual(self.client.get('/health/').json()['status'], 'ok')
