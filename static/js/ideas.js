(function() {
    'use strict';

    const searchInput = document.getElementById('ideas-search');
    const statusFilter = document.getElementById('ideas-status-filter');
    const sortSelect = document.getElementById('ideas-sort');
    const table = document.getElementById('ideas-table');
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Скрываем строку "нет идей" если она есть — будет показана JS если все скрыты
    const noIdeasRow = document.getElementById('no-ideas-row');

    function filterAndSort() {
        const searchText = (searchInput ? searchInput.value.toLowerCase() : '');
        const statusVal = (statusFilter ? statusFilter.value : '');
        const sortVal = (sortSelect ? sortSelect.value : 'created_desc');

        // Фильтрация
        let visible = 0;
        rows.forEach(function(row) {
            // Пропускаем строку "нет идей"
            if (row.id === 'no-ideas-row') return;

            const searchData = (row.getAttribute('data-search') || '').toLowerCase();
            const rowStatus = row.getAttribute('data-status') || '';
            const statusMatch = !statusVal || rowStatus === statusVal;
            const searchMatch = !searchText || searchData.indexOf(searchText) !== -1;

            if (statusMatch && searchMatch) {
                row.style.display = '';
                visible++;
            } else {
                row.style.display = 'none';
            }
        });

        // Показывать/скрывать "нет идей"
        if (noIdeasRow) {
            noIdeasRow.style.display = (visible === 0) ? '' : 'none';
        }

        // Сортировка
        if (!sortVal) return;
        const sortParts = sortVal.split('_');
        const sortKey = sortParts[0];
        const sortDir = sortParts[1] || 'desc';

        // Извлекаем видимые строки
        const visibleRows = rows.filter(function(r) {
            return r.style.display !== 'none' && r.id !== 'no-ideas-row';
        });

        visibleRows.sort(function(a, b) {
            var valA, valB;

            switch (sortKey) {
                case 'created':
                    valA = a.getAttribute('data-created') || '';
                    valB = b.getAttribute('data-created') || '';
                    break;
                case 'updated':
                    valA = a.getAttribute('data-updated') || '';
                    valB = b.getAttribute('data-updated') || '';
                    break;
                case 'roi':
                    valA = parseInt(a.getAttribute('data-roi') || '0', 10);
                    valB = parseInt(b.getAttribute('data-roi') || '0', 10);
                    break;
                case 'complexity':
                    valA = parseInt(a.getAttribute('data-complexity') || '0', 10);
                    valB = parseInt(b.getAttribute('data-complexity') || '0', 10);
                    break;
                default:
                    valA = a.getAttribute('data-created') || '';
                    valB = b.getAttribute('data-created') || '';
            }

            if (typeof valA === 'string') {
                return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else {
                return sortDir === 'asc' ? valA - valB : valB - valA;
            }
        });

        // Перемещаем строки в новом порядке
        visibleRows.forEach(function(row) {
            tbody.appendChild(row);
        });
    }

    // События
    if (searchInput) searchInput.addEventListener('input', filterAndSort);
    if (statusFilter) statusFilter.addEventListener('change', filterAndSort);
    if (sortSelect) sortSelect.addEventListener('change', filterAndSort);
})();
