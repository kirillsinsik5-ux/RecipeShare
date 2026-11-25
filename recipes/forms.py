from decimal import Decimal, InvalidOperation
from django import forms
from .models import Recipe, Category


class RecipeCreateForm(forms.ModelForm):
    ingredient_lines = forms.CharField(
        label='Ингредиенты',
        help_text='Каждый ингредиент с новой строки в формате: количество, единица, название. Например: 200 г муки',
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': '200 г муки\n2 шт. яйца\n100 мл молока'}),
    )

    class Meta:
        model = Recipe
        fields = ('title', 'category', 'description', 'cooking_time_min', 'servings', 'ingredient_lines', 'instructions')
        labels = {
            'title': 'Название блюда', 'category': 'Категория', 'description': 'Краткое описание',
            'cooking_time_min': 'Время приготовления (мин)', 'servings': 'Количество порций',
            'instructions': 'Шаги приготовления',
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 3}), 'instructions': forms.Textarea(attrs={'rows': 7})}

    def clean_ingredient_lines(self):
        raw = self.cleaned_data['ingredient_lines'].strip()
        parsed = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            if len(parts) != 3:
                raise forms.ValidationError(f'Не удалось разобрать строку «{line}». Укажите количество, единицу и ингредиент.')
            try:
                qty = Decimal(parts[0].replace(',', '.'))
                if qty <= 0:
                    raise InvalidOperation
            except InvalidOperation:
                raise forms.ValidationError(f'Количество в строке «{line}» должно быть положительным числом.')
            if not parts[2].strip():
                raise forms.ValidationError(f'Не указано название ингредиента в строке «{line}».')
            parsed.append((qty, parts[1], parts[2].strip()))
        if not parsed:
            raise forms.ValidationError('Добавьте хотя бы один ингредиент.')
        return parsed
