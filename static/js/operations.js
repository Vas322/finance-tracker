document.addEventListener('DOMContentLoaded', function() {
    const typeSelect = document.getElementById('type');
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');

    if (!typeSelect) return;

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
});