function populateCategorySelect(categorySelect, type) {
    categorySelect.innerHTML = '<option value="">Выберите категорию</option>';
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
}

function populateSubcategorySelect(subcategorySelect, type, category) {
    subcategorySelect.innerHTML = '<option value="">-- Выберите --</option>';
    if (!category) return;
    let categories = {};
    if (type === 'Доход') {
        categories = window.incomeCategories || {};
    } else if (type === 'Расход') {
        categories = window.expenseCategories || {};
    }
    if (categories[category]) {
        categories[category].forEach(sub => {
            if (sub) {
                const option = document.createElement('option');
                option.value = sub;
                option.textContent = sub;
                subcategorySelect.appendChild(option);
            }
        });
    }
}

// ==================== ДОБАВЛЕНИЕ ОПЕРАЦИИ ====================
document.addEventListener('DOMContentLoaded', function() {
    const modalType = document.getElementById('modal_type');
    const modalCategory = document.getElementById('modal_category');
    const modalSubcategory = document.getElementById('modal_subcategory');

    if (modalType) {
        modalType.addEventListener('change', function() {
            populateCategorySelect(modalCategory, this.value);
            modalSubcategory.innerHTML = '<option value="">-- Выберите --</option>';
        });

        modalCategory.addEventListener('change', function() {
            populateSubcategorySelect(modalSubcategory, modalType.value, this.value);
        });
    }
});

// ==================== РЕДАКТИРОВАНИЕ ОПЕРАЦИЙ ====================
document.addEventListener('DOMContentLoaded', function() {
    const editModal = document.getElementById('editModal');
    if (!editModal) return;

    const bsModal = new bootstrap.Modal(editModal);
    const editType = document.getElementById('edit_type');
    const editCategory = document.getElementById('edit_category');
    const editSubcategory = document.getElementById('edit_subcategory');

    editType.addEventListener('change', function() {
        populateCategorySelect(editCategory, this.value);
        editSubcategory.innerHTML = '<option value="">-- Выберите --</option>';
    });

    editCategory.addEventListener('change', function() {
        populateSubcategorySelect(editSubcategory, editType.value, this.value);
    });

    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const id = this.dataset.id;

            try {
                const response = await fetch(`/get_operation/${id}`);
                const data = await response.json();

                document.getElementById('edit_id').value = data.id;
                document.getElementById('edit_date').value = data.date;

                editType.value = data.type;
                editType.dispatchEvent(new Event('change'));

                editCategory.value = data.category;
                editCategory.dispatchEvent(new Event('change'));

                if (data.subcategory && data.subcategory !== '') {
                    const subOptions = editSubcategory.options;
                    for (let i = 0; i < subOptions.length; i++) {
                        if (subOptions[i].value === data.subcategory) {
                            subOptions[i].selected = true;
                            break;
                        }
                    }
                }

                document.getElementById('edit_amount').value = data.amount;
                document.getElementById('edit_comment').value = data.comment || '';

                bsModal.show();
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
                type: editType.value,
                category: editCategory.value,
                subcategory: editSubcategory.value,
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
