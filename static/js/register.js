// Клиентская валидация формы регистрации.
// Ошибки выводятся рядом с полем (а не через alert) и озвучиваются скринридером.
// Серверная проверка остаётся обязательной.
(function () {
  var form = document.getElementById('register-form');
  if (!form) return;

  function field(name) { return form.querySelector('[name="' + name + '"]'); }

  function clearError(input) {
    input.removeAttribute('aria-invalid');
    var old = document.getElementById(input.id + '_jserror');
    if (old) old.remove();
  }

  function showError(input, text) {
    clearError(input);
    input.setAttribute('aria-invalid', 'true');
    var p = document.createElement('p');
    p.className = 'error-text';
    p.id = input.id + '_jserror';
    p.setAttribute('role', 'alert');
    p.textContent = text;
    input.setAttribute('aria-describedby', p.id);
    input.parentNode.appendChild(p);
  }

  form.addEventListener('submit', function (e) {
    var ok = true;
    var email = field('email');
    var pass1 = field('password1');
    var pass2 = field('password2');
    [email, pass1, pass2].forEach(clearError);

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
      showError(email, 'Введите корректный email'); ok = false;
    }
    if (pass1.value.length < 8) {
      showError(pass1, 'Пароль должен содержать не менее 8 символов'); ok = false;
    }
    if (pass1.value !== pass2.value) {
      showError(pass2, 'Пароли не совпадают'); ok = false;
    }
    if (!ok) {
      e.preventDefault();
      var firstInvalid = form.querySelector('[aria-invalid="true"]');
      if (firstInvalid) firstInvalid.focus();
    }
  });
})();
