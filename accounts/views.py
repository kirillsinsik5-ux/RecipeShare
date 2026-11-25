import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from recipes.services import create_reset_token, get_valid_token, reset_password

from .decorators import role_required
from .forms import (ForgotPasswordForm, LoginForm, ProfileForm, RegisterForm,
                    ResetPasswordForm)

User = get_user_model()
logger = logging.getLogger(__name__)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.ROLE_AUTHOR  # роль задаёт только сервер
            user.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна.')
            return redirect('accounts:profile')
        messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Вы вошли в систему.')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()},
                    require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('accounts:profile')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html',
                  {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    # защита от IDOR: свой профиль или модератор
    if request.user.pk != target.pk and not request.user.is_moderator:
        raise PermissionDenied('Вы можете редактировать только свой профиль')
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=target)
    return render(request, 'accounts/profile_edit.html',
                  {'form': form, 'target': target})


@role_required([User.ROLE_MODERATOR])
def moderation_dashboard_view(request):
    users = User.objects.order_by('id')
    return render(request, 'accounts/moderation_dashboard.html', {'users': users})


@role_required([User.ROLE_MODERATOR])
@require_POST
def toggle_active_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk or target.is_superuser:
        raise PermissionDenied('Нельзя блокировать себя или суперпользователя')
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    messages.success(request, 'Статус аккаунта изменён.')
    return redirect('accounts:moderation')


NEUTRAL_MESSAGE = 'Если аккаунт с таким email существует, письмо отправлено.'


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if user:
                raw_token = create_reset_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('accounts:reset_password', kwargs={'token': raw_token}))
                try:
                    send_mail(
                        'Восстановление пароля RecipeShare',
                        f'Для сброса пароля перейдите по ссылке (действует 30 минут):\n{reset_url}',
                        None, [user.email], fail_silently=False)
                except Exception:
                    # Ошибка почты пишется в лог, а пользователь видит тот же
                    # нейтральный ответ: иначе по реакции можно угадать, есть ли email в базе.
                    logger.exception('Не удалось отправить письмо восстановления')
            messages.success(request, NEUTRAL_MESSAGE)
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, token):
    reset_token = get_valid_token(token)
    if reset_token is None:
        messages.error(request, 'Ссылка недействительна или истек её срок действия.')
        return redirect('accounts:login')
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            reset_password(reset_token, form.cleaned_data['password'])
            messages.success(request, 'Пароль успешно изменён. Войдите с новым паролем.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm()
    return render(request, 'accounts/reset_password.html', {'form': form})
