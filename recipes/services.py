"""Сервисные функции восстановления пароля (Тема 7)."""
import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import PasswordResetToken

TOKEN_TTL_MINUTES = 30


def _hash(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_reset_token(user):
    """Создаёт токен и возвращает его исходное значение (в БД хранится только хеш)."""
    # инвалидируем все ранее выданные неиспользованные токены пользователя
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now())
    raw_token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token_hash=_hash(raw_token),
        expires_at=timezone.now() + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return raw_token  # уходит в письмо, в базе не хранится


def get_valid_token(raw_token):
    """Возвращает действующий токен или None (не найден / использован / просрочен)."""
    token = PasswordResetToken.objects.select_related('user').filter(
        token_hash=_hash(raw_token)).first()
    return token if token and token.is_valid() else None


def reset_password(token, new_password):
    """Устанавливает новый пароль (хеш создаёт Django) и гасит токен."""
    user = token.user
    user.set_password(new_password)
    user.save(update_fields=['password'])
    token.used_at = timezone.now()
    token.save(update_fields=['used_at'])
