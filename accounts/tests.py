import hashlib
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from recipes.models import PasswordResetToken

User = get_user_model()
PASSWORD = 'Str0ng-Pass-2026'


def make_user(email, role=User.ROLE_AUTHOR, **kw):
    return User.objects.create_user(
        username=email.split('@')[0], email=email, password=PASSWORD,
        full_name='Тест', role=role, **kw)


class RegistrationLoginTests(TestCase):
    def test_register_creates_hashed_password_and_author_role(self):
        r = self.client.post(reverse('accounts:register'), {
            'email': 'new@example.com', 'username': 'new', 'full_name': 'Новый',
            'password1': PASSWORD, 'password2': PASSWORD,
            'role': 'moderator',  # попытка выбрать роль самому
        })
        self.assertRedirects(r, reverse('accounts:profile'))
        u = User.objects.get(email='new@example.com')
        self.assertEqual(u.role, 'author')
        self.assertNotEqual(u.password, PASSWORD)
        self.assertTrue(u.password.startswith(('pbkdf2_', 'argon2', 'bcrypt')))

    def test_duplicate_email_rejected(self):
        make_user('a@example.com')
        r = self.client.post(reverse('accounts:register'), {
            'email': 'A@example.com', 'username': 'x', 'full_name': 'X',
            'password1': PASSWORD, 'password2': PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_login_logout(self):
        make_user('a@example.com')
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'a@example.com', 'password': PASSWORD})
        self.assertRedirects(r, reverse('accounts:profile'))
        self.assertEqual(self.client.post(reverse('accounts:logout')).status_code, 302)
        self.assertRedirects(self.client.get(reverse('accounts:profile')),
                             reverse('accounts:login') + '?next=/accounts/profile/')

    def test_wrong_password(self):
        make_user('a@example.com')
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'a@example.com', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Неверный email или пароль')

    def test_open_redirect_blocked(self):
        make_user('a@example.com')
        r = self.client.post(reverse('accounts:login'), {
            'username': 'a@example.com', 'password': PASSWORD,
            'next': 'https://evil.example/'})
        self.assertRedirects(r, reverse('accounts:profile'))


class RoleTests(TestCase):
    def setUp(self):
        self.author = make_user('author@example.com')
        self.other = make_user('other@example.com')
        self.mod = make_user('mod@example.com', role=User.ROLE_MODERATOR)

    def test_author_gets_403_on_moderation(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(reverse('accounts:moderation')).status_code, 403)

    def test_anonymous_redirected_from_moderation(self):
        self.assertEqual(self.client.get(reverse('accounts:moderation')).status_code, 302)

    def test_moderator_sees_dashboard(self):
        self.client.force_login(self.mod)
        self.assertEqual(self.client.get(reverse('accounts:moderation')).status_code, 200)

    def test_idor_blocked_for_author(self):
        self.client.force_login(self.author)
        r = self.client.get(reverse('accounts:profile_edit', args=[self.other.id]))
        self.assertEqual(r.status_code, 403)
        r = self.client.post(reverse('accounts:profile_edit', args=[self.other.id]),
                             {'full_name': 'Hack', 'email': 'other@example.com'})
        self.assertEqual(r.status_code, 403)

    def test_author_edits_self_but_cannot_change_role(self):
        self.client.force_login(self.author)
        self.client.post(reverse('accounts:profile_edit', args=[self.author.id]),
                         {'full_name': 'Новое', 'email': 'author@example.com',
                          'role': 'moderator'})
        self.author.refresh_from_db()
        self.assertEqual(self.author.full_name, 'Новое')
        self.assertEqual(self.author.role, 'author')

    def test_moderator_can_edit_other(self):
        self.client.force_login(self.mod)
        r = self.client.get(reverse('accounts:profile_edit', args=[self.other.id]))
        self.assertEqual(r.status_code, 200)

    def test_toggle_active_requires_moderator_and_post(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(
            reverse('accounts:toggle_active', args=[self.other.id])).status_code, 403)
        self.client.force_login(self.mod)
        self.assertEqual(self.client.get(
            reverse('accounts:toggle_active', args=[self.other.id])).status_code, 405)
        self.client.post(reverse('accounts:toggle_active', args=[self.other.id]))
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_active)

    def test_nav_button_hidden_for_author(self):
        self.client.force_login(self.author)
        self.assertNotContains(self.client.get(reverse('accounts:profile')),
                               reverse('accounts:moderation'))
        self.client.force_login(self.mod)
        self.assertContains(self.client.get(reverse('accounts:profile')),
                            reverse('accounts:moderation'))

    def test_custom_403_template(self):
        self.client.force_login(self.author)
        r = self.client.get(reverse('accounts:moderation'))
        self.assertContains(r, '403 — доступ запрещён', status_code=403)


class ApiTests(TestCase):
    def test_ping(self):
        self.assertEqual(self.client.get('/api/ping/').json(), {'ping': 'pong'})

    def test_admin_api_json_errors(self):
        r = self.client.get('/api/admin/stats/')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['error'], 'Unauthorized')
        self.client.force_login(make_user('a@example.com'))
        r = self.client.get('/api/admin/stats/')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['error'], 'Forbidden')
        self.client.force_login(make_user('m@example.com', role=User.ROLE_MODERATOR))
        r = self.client.get('/api/admin/stats/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['users_total'], 2)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = make_user('user@example.com')

    def _request(self, email):
        return self.client.post(reverse('accounts:forgot_password'), {'email': email},
                                follow=True)

    def _link_from_mail(self):
        return re.search(r'http://testserver(/accounts/reset-password/[\w-]+/)',
                         mail.outbox[-1].body).group(1)

    def test_same_message_for_existing_and_unknown_email(self):
        known = self._request('user@example.com')
        unknown = self._request('nobody@example.com')
        text = 'Если аккаунт с таким email существует, письмо отправлено.'
        self.assertContains(known, text)
        self.assertContains(unknown, text)
        self.assertEqual(len(mail.outbox), 1)

    def test_only_hash_stored_and_full_flow(self):
        self._request('user@example.com')
        link = self._link_from_mail()
        raw = link.rstrip('/').split('/')[-1]
        tok = PasswordResetToken.objects.get()
        self.assertNotEqual(tok.token_hash, raw)
        self.assertEqual(tok.token_hash, hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(len(tok.token_hash), 64)

        self.assertEqual(self.client.get(link).status_code, 200)
        new = 'Another-Good-Pass-77'
        r = self.client.post(link, {'password': new, 'confirm_password': new})
        self.assertRedirects(r, reverse('accounts:login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new))
        # одноразовость
        r = self.client.get(link, follow=True)
        self.assertContains(r, 'Ссылка недействительна')

    def test_expired_token(self):
        self._request('user@example.com')
        link = self._link_from_mail()
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertContains(self.client.get(link, follow=True), 'Ссылка недействительна')

    def test_new_request_invalidates_old_link(self):
        self._request('user@example.com')
        old = self._link_from_mail()
        self._request('user@example.com')
        self.assertContains(self.client.get(old, follow=True), 'Ссылка недействительна')

    def test_password_mismatch_and_weak(self):
        self._request('user@example.com')
        link = self._link_from_mail()
        r = self.client.post(link, {'password': 'Aa1-long-enough-x', 'confirm_password': 'diff'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post(link, {'password': '12345', 'confirm_password': '12345'})
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_mail_failure_does_not_leak(self):
        from unittest import mock
        with mock.patch('accounts.views.send_mail', side_effect=OSError('smtp down')):
            r = self._request('user@example.com')
        self.assertContains(r, 'Если аккаунт с таким email существует')
