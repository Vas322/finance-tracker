document.addEventListener('DOMContentLoaded', function() {
    const monthlyData = window.monthlyData || [];
    if (monthlyData.length === 0) return;

    const monthNames = ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек'];
    const months = monthlyData.map(d => d.month);
    const incomes = monthlyData.map(d => d.income);
    const expenses = monthlyData.map(d => d.expense);

    const formattedMonths = months.map(m => {
        const [y, mon] = m.split('-');
        return monthNames[parseInt(mon)-1] + ' ' + y;
    });

    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: formattedMonths,
            datasets: [
                { label: 'Доходы', data: incomes, borderColor: '#28a745', backgroundColor: 'rgba(40,167,69,0.1)', fill: true, tension: 0.3, pointRadius: 4, pointHoverRadius: 6 },
                { label: 'Расходы', data: expenses, borderColor: '#dc3545', backgroundColor: 'rgba(220,53,69,0.1)', fill: true, tension: 0.3, pointRadius: 4, pointHoverRadius: 6 }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            return ctx.dataset.label + ': ' + ctx.raw.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            }
        }
    });

    const expenseData = window.expenseData || [];
    if (expenseData.length === 0) return;

    const categories = expenseData.map(item => item.category);
    const amounts = expenseData.map(item => item.total);

    new Chart(document.getElementById('expenseChart'), {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#17a2b8', '#007bff', '#6f42c1', '#e83e8c'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const total = amounts.reduce((a, b) => a + b, 0);
                            const percent = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                            return ctx.label + ': ' + ctx.raw.toLocaleString('ru-RU') + ' ₽ (' + percent + '%)';
                        }
                    }
                }
            }
        }
    });
});
