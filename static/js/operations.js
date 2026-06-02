// ==================== ДОБАВЛЕНИЕ ОПЕРАЦИИ ====================
document.addEventListener('DOMContentLoaded', function() {
    const typeSelect = document.getElementById('type');
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');

    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            const type = this.value;
            categorySelect.innerHTML = '<option value="">Выберите категорию</option>';
            subcategorySelect.innerHTML = '<option value="">Выберите подкатегорию</option>';

            let categories = {};
            if (type === 'Доход') {
                categories = window.incomeCategories || {};
            } else if (type === 'Расход') {
                categories = window.expenseCategories || {};
            }

            for (let cat in categories) {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                categorySelect.appendChild(option);
            }
        });

        categorySelect.addEventListener('change', function() {
            const type = typeSelect.value;
            const category = this.value;
            subcategorySelect.innerHTML = '<option value="">Выберите подкатегорию</option>';

            let categories = {};
            if (type === 'Доход') {
                categories = window.incomeCategories || {};
            } else if (type === 'Расход') {
                categories = window.expenseCategories || {};
            }

            if (category && categories[category]) {
                categories[category].forEach(sub => {
                    if (sub) {
                        const option = document.createElement('option');
                        option.value = sub;
                        option.textContent = sub;
                        subcategorySelect.appendChild(option);
                    }
                });
            }
        });
    }

    // ==================== РЕДАКТИРОВАНИЕ ОПЕРАЦИЙ ====================

    // Находим модальное окно
    const editModalElement = document.getElementById('editModal');
    if (!editModalElement) {
        console.error('Модальное окно editModal не найдено!');
        return;
    }

    // Создаём объект модального окна
    let modal;
    try {
        modal = new bootstrap.Modal(editModalElement);
        console.log('Модальное окно создано');
    } catch (e) {
        console.error('Ошибка создания модального окна:', e);
        return;
    }

    // Обработчики кнопок редактирования
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const id = this.dataset.id;
            console.log('Редактируем операцию ID:', id);

            try {
                const response = await fetch(`/get_operation/${id}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                console.log('Полученные данные:', data);

                // Заполняем форму
                document.getElementById('edit_id').value = data.id;
                document.getElementById('edit_date').value = data.date;
                document.getElementById('edit_type').value = data.type;
                document.getElementById('edit_category').value = data.category;
                document.getElementById('edit_subcategory').value = data.subcategory || '';
                document.getElementById('edit_amount').value = data.amount;
                document.getElementById('edit_comment').value = data.comment || '';

                // Показываем модальное окно
                modal.show();
                console.log('Модальное окно показано');
            } catch (e) {
                console.error('Ошибка загрузки:', e);
                alert('Ошибка загрузки данных операции: ' + e.message);
            }
        });
    });

    // Обработчик отправки формы
    const editForm = document.getElementById('editForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const data = {
                id: document.getElementById('edit_id').value,
                date: document.getElementById('edit_date').value,
                type: document.getElementById('edit_type').value,
                category: document.getElementById('edit_category').value,
                subcategory: document.getElementById('edit_subcategory').value,
                amount: document.getElementById('edit_amount').value,
                comment: document.getElementById('edit_comment').value
            };

            try {
                const response = await fetch('/edit_operation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.success) {
                    location.reload();
                } else {
                    alert('Ошибка при сохранении');
                }
            } catch (e) {
                console.error('Ошибка сохранения:', e);
                alert('Ошибка при сохранении');
            }
        });
    }
});