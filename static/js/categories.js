document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.edit-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const row = document.getElementById(`row-${id}`);
            row.querySelectorAll('.view-mode').forEach(el => el.style.display = 'none');
            row.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'table-cell');
            this.style.display = 'none';
            row.querySelector('.save-row-btn').style.display = 'inline-block';
            row.querySelector('.cancel-row-btn').style.display = 'inline-block';
        });
    });

    document.querySelectorAll('.cancel-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            location.reload();
        });
    });

    document.querySelectorAll('.add-subcat-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('.new-subcat-input');
            const name = input.value.trim();
            if (!name) return;
            const list = this.closest('.edit-mode').querySelector('.subcats-list');
            const chip = document.createElement('div');
            chip.className = 'subcat-chip input-group input-group-sm mb-1';
            chip.innerHTML = `<span class="input-group-text">${name}</span><button class="btn btn-outline-danger remove-subcat-btn" type="button">&times;</button>`;
            list.appendChild(chip);
            input.value = '';
        });
    });

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-subcat-btn')) {
            e.target.closest('.subcat-chip').remove();
        }
    });

    document.querySelectorAll('.save-row-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const id = this.dataset.id;
            const row = document.getElementById(`row-${id}`);
            const newName = row.querySelector('.cat-name-input').value;
            const subcats = [];
            row.querySelectorAll('.subcat-chip .input-group-text').forEach(el => {
                subcats.push(el.textContent.trim());
            });
            const response = await fetch('/edit_full_category/' + id, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newName,
                    subcategories: subcats
                })
            });
            if (response.ok) {
                location.reload();
            } else {
                const result = await response.json();
                alert('Ошибка при сохранении: ' + JSON.stringify(result));
            }
        });
    });
});
