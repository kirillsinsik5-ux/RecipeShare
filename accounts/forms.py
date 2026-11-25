from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class AccessibleFormMixin:
    """Добавляет полям CSS-класс и ARIA-атрибуты (a11y): invalid и связь с текстом ошибки."""

    def full_clean(self):
        super().full_clean()
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            attrs['class'] = (attrs.get('class', '') + ' form-control').strip()
            described = []
            if field.help_text:
                described.append(f'id_{name}_help')
            if self.is_bound and name in self.errors:
                attrs['aria-invalid'] = 'true'
                described.append(f'id_{name}_error')
            if described:
                attrs['aria-describedby'] = ' '.join(described)


class RegisterForm(AccessibleFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email', max_length=150)
    full_name = forms.CharField(label='Имя', max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        # поле role намеренно не входит в форму: роль нельзя выбрать при регистрации
        fields = ('email', 'username', 'full_name')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(AccessibleFormMixin, AuthenticationForm):
    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
        'inactive': 'Аккаунт заблокирован.',
    }

    username = forms.EmailField(label='Email')

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class ProfileForm(AccessibleFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'email')  # role, is_active, is_staff менять нельзя

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Этот email уже занят.')
        return email


class ForgotPasswordForm(AccessibleFormMixin, forms.Form):
    email = forms.EmailField(label='Введите ваш Email')


class ResetPasswordForm(AccessibleFormMixin, forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Новый пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput,
                                       label='Подтвердите пароль')

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned
