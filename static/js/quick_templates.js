(function() {
    'use strict';

    let templates = [];
    let debounceTimer = null;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const grid = document.getElementById('templates-grid');
    const empty = document.getElementById('templates-empty');
    const form = document.getElementById('templateForm');
    const modal = document.getElementById('templateModal');
    const modalTitle = document.getElementById('templateModalTitle');
    const deleteBtn = document.getElementById('tpl-delete-btn');
    const categorySelect = document.getElementById('tpl_category');
    const subcategorySelect = document.getElementById('tpl_subcategory');

    function init() {
        if (!grid) return;
        loadTemplates();
        setupCategoryListeners();
        setupFormListener();
        setupModalReset();
    }

    function loadTemplates() {
        fetch('/api/templates')
            .then(r => r.json())
            .then(data => {
                templates = data;
                render();
            });
    }

    function render() {
        grid.innerHTML = '';
        if (templates.length === 0) {
            empty.classList.remove('d-none');
            grid.classList.add('d-none');
            return;
        }
        empty.classList.add('d-none');
        grid.classList.remove('d-none');

        templates.forEach(function(tpl) {
            const btn = document.createElement('button');
            btn.className = 'btn btn-outline-danger btn-sm position-relative';
            btn.innerHTML = '<strong>' + escapeHtml(tpl.name) + '</strong><br><small>' + escapeHtml(tpl.category) + '</small><br><span class="fw-bold">' + formatMoney(tpl.amount) + ' ₽</span>';
            btn.title = tpl.category + (tpl.subcategory ? ' / ' + tpl.subcategory : '') + ' — ' + formatMoney(tpl.amount) + ' ₽';

            // Двойной клик — редактирование
            btn.addEventListener('dblclick', function(e) {
                e.preventDefault();
                if (debounceTimer) { clearTimeout(debounceTimer); debounceTimer = null; }
                editTemplate(tpl);
            });

            var clickTimer = null;
            btn.addEventListener('click', function() {
                if (clickTimer) {
                    clearTimeout(clickTimer);
                    clickTimer = null;
                    return;
                }
                clickTimer = setTimeout(function() {
                    clickTimer = null;
                    if (debounceTimer) return;
                    debounceTimer = setTimeout(function() { debounceTimer = null; }, 1000);
                    
                    btn.disabled = true;
                    fetch('/quick_add/' + tpl.id, { method: 'POST', headers: { 'X-CSRFToken': csrfToken } })
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (data.ok) {
                                showFeedback(btn, '✅ ' + data.message);
                                setTimeout(function() { location.reload(); }, 800);
                            } else {
                                showFeedback(btn, '❌ ' + (data.error || 'Ошибка'));
                                btn.disabled = false;
                            }
                        })
                        .catch(function() {
                            showFeedback(btn, '❌ Сеть');
                            btn.disabled = false;
                        });
                }, 250);
            });

            grid.appendChild(btn);
        });

        if (templates.length >= 8) {
            const more = document.createElement('small');
            more.className = 'text-muted w-100';
            more.textContent = 'Максимум 8 шаблонов';
            grid.appendChild(more);
        }
    }

    function showFeedback(btn, text) {
        const orig = btn.innerHTML;
        btn.innerHTML = '<small>' + text + '</small>';
        btn.classList.remove('btn-outline-danger');
        btn.classList.add('btn-success');
        setTimeout(function() {
            btn.innerHTML = orig;
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-danger');
        }, 1500);
    }

    function formatMoney(kopecks) {
        return (kopecks / 100).toLocaleString('ru-RU');
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function setupCategoryListeners() {
        if (!categorySelect) return;
        categorySelect.innerHTML = '<option value="">-- Выберите --</option>';
        var cats = window.expenseCategories || {};
        for (var catName in cats) {
            var opt = document.createElement('option');
            opt.value = catName;
            opt.textContent = catName;
            categorySelect.appendChild(opt);
        }

        categorySelect.addEventListener('change', function() {
            subcategorySelect.innerHTML = '<option value="">-- Не выбрана --</option>';
            var cat = categorySelect.value;
            if (!cat || !cats[cat]) return;
            cats[cat].forEach(function(sub) {
                var opt = document.createElement('option');
                opt.value = sub;
                opt.textContent = sub;
                subcategorySelect.appendChild(opt);
            });
        });
    }

    function setupFormListener() {
        if (!form) return;
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const id = document.getElementById('tpl_id').value;
            const data = {
                name: document.getElementById('tpl_name').value.trim(),
                category: categorySelect.value,
                subcategory: subcategorySelect.value,
                amount: Math.round(parseFloat(document.getElementById('tpl_amount').value) * 100) || 0
            };

            if (!data.name || !data.category) {
                alert('Название и категория обязательны');
                return;
            }

            const url = id ? '/api/templates/' + id : '/api/templates';
            const method = id ? 'PUT' : 'POST';

            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(function(resp) {
                if (resp.error) { alert(resp.error); return; }
                bootstrap.Modal.getInstance(modal).hide();
                loadTemplates();
            })
            .catch(function() {
                alert('Ошибка сети');
            });
        });
    }

    function setupModalReset() {
        if (!modal) return;
        modal.addEventListener('show.bs.modal', function(e) {
            const btn = e.relatedTarget;
            if (btn && btn.id === 'add-template-btn') {
                modalTitle.textContent = '➕ Новый шаблон';
                form.reset();
                document.getElementById('tpl_id').value = '';
                deleteBtn.classList.add('d-none');
            }
        });
    }

    function editTemplate(tpl) {
        modalTitle.textContent = '✏️ Редактировать шаблон';
        document.getElementById('tpl_id').value = tpl.id;
        document.getElementById('tpl_name').value = tpl.name;
        categorySelect.value = tpl.category;
        categorySelect.dispatchEvent(new Event('change'));
        setTimeout(function() {
            subcategorySelect.value = tpl.subcategory || '';
        }, 50);
        document.getElementById('tpl_amount').value = (tpl.amount / 100).toFixed(2);
        deleteBtn.classList.remove('d-none');
        new bootstrap.Modal(modal).show();
    }

    deleteBtn.addEventListener('click', function() {
        const id = document.getElementById('tpl_id').value;
        if (!id) return;
        if (!confirm('Удалить шаблон?')) return;
        fetch('/api/templates/' + id, { method: 'DELETE', headers: { 'X-CSRFToken': csrfToken } })
            .then(function() {
                bootstrap.Modal.getInstance(modal).hide();
                loadTemplates();
            })
            .catch(function() {
                alert('Ошибка сети');
            });
    });

    document.addEventListener('DOMContentLoaded', init);
})();