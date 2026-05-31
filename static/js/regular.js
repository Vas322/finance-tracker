// ==================== РЕГУЛЯРНЫЕ ПЛАТЕЖИ ====================

document.addEventListener('DOMContentLoaded', function() {
    const expenseCategories = window.expenseCategories || {};

    console.log('expenseCategories загружены:', expenseCategories);

    // Функция обновления подкатегорий
    function updateSubcategorySelect(categorySelect, subcategorySelect, currentSub = '') {
        const category = categorySelect.value;
        subcategorySelect.innerHTML = '<option value="">-- Выберите --</option>';
        if (category && expenseCategories[category]) {
            expenseCategories[category].forEach(sub => {
                const option = document.createElement('option');
                option.value = sub;
                option.textContent = sub;
                if (sub === currentSub) option.selected = true;
                subcategorySelect.appendChild(option);
            });
        }
    }

    // Для каждой строки таблицы: настройка подкатегорий при редактировании
    document.querySelectorAll('.category-select').forEach(select => {
        const id = select.dataset.id;
        const subcategorySelect = document.querySelector(`.subcategory-select[data-id="${id}"]`);
        const currentSub = subcategorySelect.getAttribute('data-current') || '';

        // Инициализация подкатегорий для этой строки
        updateSubcategorySelect(select, subcategorySelect, currentSub);

        // При изменении категории обновляем подкатегории
        select.addEventListener('change', function() {
            updateSubcategorySelect(select, subcategorySelect, '');
        });
    });

    // Режим редактирования строки
    document.querySelectorAll('.edit-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const row = document.getElementById(`row-${id}`);

            // Скрываем режим просмотра, показываем режим редактирования
            row.querySelectorAll('.view-mode .edit-mode').forEach(el => el.style.display = 'none');
            row.querySelectorAll('.view-mode span').forEach(el => el.style.display = 'none');
            row.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'inline-block');

            // Меняем кнопки
            this.style.display = 'none';
            row.querySelector('.save-row-btn').style.display = 'inline-block';
            row.querySelector('.cancel-row-btn').style.display = 'inline-block';
        });
    });

    // Отмена редактирования
    document.querySelectorAll('.cancel-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            location.reload();
        });
    });

    // Сохранение строки (отправка формы)
    document.querySelectorAll('.save-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.getElementById('mainForm').submit();
        });
    });

    // Для формы добавления нового платежа
    const addCategory = document.getElementById('add_category');
    const addSubcategory = document.getElementById('add_subcategory');

    if (addCategory && addSubcategory) {
        addCategory.addEventListener('change', function() {
            const category = addCategory.value;
            addSubcategory.innerHTML = '<option value="">-- Выберите --</option>';
            if (category && expenseCategories[category]) {
                expenseCategories[category].forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub;
                    option.textContent = sub;
                    addSubcategory.appendChild(option);
                });
            }
        });
    }
});