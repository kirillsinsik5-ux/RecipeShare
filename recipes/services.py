# services.py
import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import PasswordResetToken

TOKEN_TTL_MINUTES = 30


def _hash(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_reset_token(user):
    raw_token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token_hash=_hash(raw_token),
        expires_at=timezone.now() + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return raw_token  # отправляется письмом, в базе не хранится


def get_valid_token(raw_token):
    token = PasswordResetToken.objects.filter(token_hash=_hash(raw_token)).first()
    return token if token and token.is_valid() else None


def reset_password(raw_token, new_password):
    token = get_valid_token(raw_token)
    if token is None:
        return False
    user = token.user
    user.set_password(new_password)  # сохраняется только хеш
    user.save()
    token.used_at = timezone.now()   # токен становится одноразовым
    token.save()
    return True