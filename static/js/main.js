// ==================== ОБЩИЕ ФУНКЦИИ ====================

// Модальное окно для начального остатка
function showMoneyModal() {
    const modal = document.getElementById('moneyModal');
    if (modal) modal.style.display = 'block';
}

function closeMoneyModal() {
    const modal = document.getElementById('moneyModal');
    if (modal) modal.style.display = 'none';
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('moneyModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Форматирование числа с пробелами
function formatNumber(num) {
    return num.toLocaleString('ru-RU');
}