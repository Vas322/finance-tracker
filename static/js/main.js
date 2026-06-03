// ==================== ОБЩИЕ ФУНКЦИИ ====================

// Форматирование числа с пробелами
function formatNumber(num) {
    return num.toLocaleString('ru-RU');
}

// Обработчик формы начального остатка (для Bootstrap)
document.addEventListener('DOMContentLoaded', function() {
    const moneyForm = document.getElementById('moneyForm');
    if (moneyForm) {
        moneyForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(moneyForm);
            const response = await fetch('/update_money', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Закрываем модальное окно Bootstrap
                const modalEl = document.getElementById('moneyModal');
                if (modalEl) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) {
                        modal.hide();
                    }
                }
                // Перезагружаем страницу
                location.reload();
            } else {
                alert('Ошибка при сохранении');
            }
        });
    }
});

// Функция для открытия модального окна (вызывается из onclick)
function showMoneyModal() {
    const modalEl = document.getElementById('moneyModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}