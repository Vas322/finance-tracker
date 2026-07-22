document.addEventListener('DOMContentLoaded', function() {
    const trendPeriods = window.trendData || [];
    if (trendPeriods.length === 0) return;

    const labels = trendPeriods.map(d => d.label);
    const incomes = trendPeriods.map(d => d.income);
    const expenses = trendPeriods.map(d => d.expense);

    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Доходы',
                    data: incomes,
                    borderColor: '#28a745',
                    backgroundColor: function(ctx) {
                        const chart = ctx.chart;
                        const {ctx: c, chartArea: a} = chart;
                        if (!a) return 'transparent';
                        const gradient = c.createLinearGradient(0, a.top, 0, a.bottom);
                        gradient.addColorStop(0, 'rgba(40,167,69,0.3)');
                        gradient.addColorStop(1, 'rgba(40,167,69,0.05)');
                        return gradient;
                    },
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Расходы',
                    data: expenses,
                    borderColor: '#dc3545',
                    backgroundColor: function(ctx) {
                        const chart = ctx.chart;
                        const {ctx: c, chartArea: a} = chart;
                        if (!a) return 'transparent';
                        const gradient = c.createLinearGradient(0, a.top, 0, a.bottom);
                        gradient.addColorStop(0, 'rgba(220,53,69,0.3)');
                        gradient.addColorStop(1, 'rgba(220,53,69,0.05)');
                        return gradient;
                    },
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
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
                        },
                        afterBody: function(ctx) {
                            const i = ctx[0].dataIndex;
                            const balance = trendPeriods[i].balance;
                            return 'Баланс: ' + balance.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                },
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
});