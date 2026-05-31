// ==================== ГРАФИКИ ====================

document.addEventListener('DOMContentLoaded', function() {
    const expenseData = window.expenseData || [];

    if (expenseData.length === 0) {
        return;
    }

    const categories = expenseData.map(item => item.category);
    const amounts = expenseData.map(item => item.total);

    const ctx = document.getElementById('expenseChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: [
                    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#1e8449'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = amounts.reduce((a, b) => a + b, 0);
                            const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value.toLocaleString('ru-RU')} ₽ (${percent}%)`;
                        }
                    }
                }
            }
        }
    });
});