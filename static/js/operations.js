// ==================== ДОБАВЛЕНИЕ ОПЕРАЦИИ (ЗАВИСИМЫЕ СПИСКИ) ====================

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
});

// ==================== РЕДАКТИРОВАНИЕ ОПЕРАЦИЙ ====================

document.addEventListener('DOMContentLoaded', function() {
    const editModal = document.getElementById('editModal');
    if (!editModal) return;

    const modal = new bootstrap.Modal(editModal);

    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const id = this.dataset.id;

            try {
                const response = await fetch(`/get_operation/${id}`);
                const data = await response.json();

                document.getElementById('edit_id').value = data.id;
                document.getElementById('edit_date').value = data.date;
                document.getElementById('edit_type').value = data.type;
                document.getElementById('edit_category').value = data.category;
                document.getElementById('edit_subcategory').value = data.subcategory || '';
                document.getElementById('edit_amount').value = data.amount;
                document.getElementById('edit_comment').value = data.comment || '';

                modal.show();
            } catch (e) {
                console.error('Ошибка загрузки:', e);
                alert('Ошибка загрузки данных операции');
            }
        });
    });

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

// ==================== ДОБАВЛЕНИЕ ОПЕРАЦИИ (МОДАЛЬНОЕ ОКНО) ====================

document.addEventListener('DOMContentLoaded', function() {
    const modalType = document.getElementById('modal_type');
    const modalCategory = document.getElementById('modal_category');
    const modalSubcategory = document.getElementById('modal_subcategory');

    if (modalType && modalCategory && modalSubcategory) {
        modalType.addEventListener('change', function() {
            const type = this.value;
            modalCategory.innerHTML = '<option value="">Выберите категорию</option>';
            modalSubcategory.innerHTML = '<option value="">Выберите подкатегорию</option>';

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
                modalCategory.appendChild(option);
            }
        });

        modalCategory.addEventListener('change', function() {
            const type = modalType.value;
            const category = this.value;
            modalSubcategory.innerHTML = '<option value="">Выберите подкатегорию</option>';

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
                        modalSubcategory.appendChild(option);
                    }
                });
            }
        });
    }
});