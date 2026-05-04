// ─── Analytics Page JavaScript ─────────────────────────────
const chartColors = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
    gradientStart: 'rgba(99, 102, 241, 0.3)',
    gradientEnd: 'rgba(99, 102, 241, 0.01)',
    palette: ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#10b981','#3b82f6','#ef4444','#14b8a6']
};

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.1)';
Chart.defaults.font.family = 'Inter, sans-serif';

let hourlyChart, serviceChart, weeklyChart;

async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics/today');
        const d = await res.json();
        document.getElementById('anServed').textContent = d.total_served;
        document.getElementById('anCancelled').textContent = d.total_cancelled;
        document.getElementById('anWait').textContent = d.avg_wait_time;
        document.getElementById('anServiceTime').textContent = d.avg_service_time;
    } catch(e) { console.error(e); }
}

async function loadHourlyChart() {
    try {
        const res = await fetch('/api/analytics/hourly');
        const d = await res.json();
        const ctx = document.getElementById('hourlyChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, chartColors.gradientStart);
        gradient.addColorStop(1, chartColors.gradientEnd);

        if (hourlyChart) hourlyChart.destroy();
        hourlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Клиенты',
                    data: d.data,
                    backgroundColor: chartColors.primary,
                    borderColor: chartColors.primary,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.08)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    } catch(e) { console.error(e); }
}

async function loadServiceChart() {
    try {
        const res = await fetch('/api/analytics/services');
        const d = await res.json();
        const ctx = document.getElementById('serviceChart').getContext('2d');

        if (serviceChart) serviceChart.destroy();
        serviceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: d.labels.length ? d.labels : ['Нет данных'],
                datasets: [{
                    data: d.data.length ? d.data : [1],
                    backgroundColor: d.data.length ? chartColors.palette.slice(0, d.labels.length) : ['#334155'],
                    borderWidth: 0,
                    spacing: 4
                }]
            },
            options: {
                responsive: true,
                cutout: '65%',
                plugins: { legend: { position: 'bottom' } }
            }
        });
    } catch(e) { console.error(e); }
}

async function loadWeeklyChart() {
    try {
        const res = await fetch('/api/analytics/weekly');
        const d = await res.json();
        const ctx = document.getElementById('weeklyChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, chartColors.gradientStart);
        gradient.addColorStop(1, chartColors.gradientEnd);

        if (weeklyChart) weeklyChart.destroy();
        weeklyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Обслужено',
                    data: d.served,
                    borderColor: chartColors.primary,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: chartColors.primary
                },{
                    label: 'Ср. ожидание (мин)',
                    data: d.avg_wait,
                    borderColor: chartColors.warning,
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: chartColors.warning
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.08)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    } catch(e) { console.error(e); }
}

loadAnalytics();
loadHourlyChart();
loadServiceChart();
loadWeeklyChart();
setInterval(loadAnalytics, 10000);
