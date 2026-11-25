(function () {
  const form = document.getElementById('recipe-form');
  if (!form) return;
  form.addEventListener('submit', function (event) {
    const title = form.querySelector('[name="title"]');
    const ingredientLines = form.querySelector('[name="ingredient_lines"]');
    const instructions = form.querySelector('[name="instructions"]');
    const errors = [];
    if (title && !title.value.trim()) errors.push('Введите название рецепта.');
    if (ingredientLines && !ingredientLines.value.trim()) errors.push('Добавьте ингредиенты, каждый с новой строки.');
    if (instructions && !instructions.value.trim()) errors.push('Опишите приготовление.');
    form.querySelector('.js-errors')?.remove();
    if (!errors.length) return;
    event.preventDefault();
    const list = document.createElement('ul'); list.className = 'errorlist js-errors'; list.setAttribute('role', 'alert');
    errors.forEach(function (text) { const li = document.createElement('li'); li.textContent = text; list.appendChild(li); });
    form.prepend(list);
    list.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
})();
