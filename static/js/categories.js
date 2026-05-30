// ==================== РЕДАКТИРОВАНИЕ КАТЕГОРИЙ ====================

// Редактирование основной категории
document.querySelectorAll('.edit-cat-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const id = this.dataset.id;
        const nameSpan = document.getElementById(`cat-name-${id}`);
        const editInput = document.getElementById(`edit-cat-${id}`);
        const saveBtn = document.querySelector(`.save-cat-btn[data-id="${id}"]`);

        nameSpan.style.display = 'none';
        editInput.style.display = 'inline-block';
        saveBtn.style.display = 'inline-block';
        this.style.display = 'none';
    });
});

document.querySelectorAll('.save-cat-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const id = this.dataset.id;
        const newName = document.getElementById(`edit-cat-${id}`).value;

        fetch('/edit_category/' + id, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'name=' + encodeURIComponent(newName)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) location.reload();
            else alert('Ошибка');
        });
    });
});

// ==================== РЕДАКТИРОВАНИЕ ПОДКАТЕГОРИЙ ====================

document.querySelectorAll('.edit-sub-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const id = this.dataset.id;
        const nameSpan = document.getElementById(`sub-name-${id}`);
        const editInput = document.getElementById(`edit-sub-${id}`);
        const saveBtn = document.querySelector(`.save-sub-btn[data-id="${id}"]`);

        nameSpan.style.display = 'none';
        editInput.style.display = 'inline-block';
        saveBtn.style.display = 'inline-block';
        this.style.display = 'none';
    });
});

document.querySelectorAll('.save-sub-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const id = this.dataset.id;
        const newName = document.getElementById(`edit-sub-${id}`).value;

        fetch('/edit_category/' + id, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'name=' + encodeURIComponent(newName)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) location.reload();
            else alert('Ошибка');
        });
    });
});