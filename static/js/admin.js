// ─── Admin Page JavaScript ───────────────────────────────────
let currentTab = 'waiting';

async function loadAdminStats() {
    try {
        const res = await fetch('/api/analytics/today');
        const d = await res.json();
        document.getElementById('statWaiting').textContent = d.total_waiting;
        document.getElementById('statServing').textContent = d.total_serving;
        document.getElementById('statServed').textContent = d.total_served;
        document.getElementById('statAvgWait').textContent = d.avg_wait_time;
    } catch(e) { console.error(e); }
}

async function loadWindows() {
    try {
        const res = await fetch('/api/windows');
        const windows = await res.json();
        const el = document.getElementById('windowsList');
        if (windows.length === 0) {
            el.innerHTML = '<p class="text-muted text-center">Нет окон обслуживания</p>';
            return;
        }
        el.innerHTML = windows.map(w => `
            <div class="window-card ${w.is_active ? 'active' : 'inactive'}">
                <div class="window-header">
                    <span class="window-name">${w.name}</span>
                    <span class="window-status ${w.is_active ? 'online' : 'offline'}">${w.is_active ? '●' : '○'}</span>
                </div>
                <div class="window-operator">${w.operator_name}</div>
                ${w.current_ticket ? `
                    <div class="window-current">
                        <span class="window-ticket-num">${w.current_ticket.ticket_number}</span>
                        <span class="window-ticket-name">${w.current_ticket.client_name}</span>
                    </div>
                    <div class="window-actions">
                        <button class="btn btn-sm btn-success" onclick="completeTicket(${w.current_ticket.id})">✅ Завершить</button>
                        <button class="btn btn-sm btn-warning" onclick="skipTicket(${w.current_ticket.id})">⏭ Пропустить</button>
                    </div>
                ` : `
                    <div class="window-empty">Свободно</div>
                    <button class="btn btn-sm btn-primary btn-block" onclick="callNext(${w.id})">📢 Вызвать следующего</button>
                `}
                <button class="btn btn-sm btn-ghost" onclick="toggleWindow(${w.id})">${w.is_active ? 'Деактивировать' : 'Активировать'}</button>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

async function loadQueue() {
    try {
        const serviceId = document.getElementById('filterService').value;
        const url = serviceId ? `/api/queue?service_id=${serviceId}` : '/api/queue';
        const res = await fetch(url);
        const data = await res.json();
        const el = document.getElementById('queueContent');
        const list = currentTab === 'waiting' ? data.waiting : data.serving;
        
        if (list.length === 0) {
            el.innerHTML = `<p class="text-muted text-center" style="padding:2rem">
                ${currentTab === 'waiting' ? 'Нет ожидающих' : 'Никто не обслуживается'}
            </p>`;
            return;
        }
        el.innerHTML = list.map(t => `
            <div class="queue-row">
                <div class="queue-row-num">${t.ticket_number}</div>
                <div class="queue-row-info">
                    <span class="queue-row-name">${t.client_name}</span>
                    <span class="queue-row-service">${t.service_icon} ${t.service_name}</span>
                </div>
                <div class="queue-row-time">${new Date(t.created_at).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'})}</div>
                <div class="queue-row-actions">
                    ${t.status === 'waiting' ? `<button class="btn btn-xs btn-danger" onclick="cancelTicket(${t.id})">✕</button>` : ''}
                    ${t.status === 'serving' || t.status === 'called' ? `<button class="btn btn-xs btn-success" onclick="completeTicket(${t.id})">✓</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

async function loadServicesList() {
    try {
        const res = await fetch('/api/services');
        const services = await res.json();
        const el = document.getElementById('servicesList');
        // Also populate filter
        const filter = document.getElementById('filterService');
        const currentVal = filter.value;
        filter.innerHTML = '<option value="">Все услуги</option>' + 
            services.map(s => `<option value="${s.id}">${s.icon} ${s.name}</option>`).join('');
        filter.value = currentVal;

        el.innerHTML = services.map(s => `
            <div class="service-row">
                <span class="service-row-icon">${s.icon}</span>
                <span class="service-row-name">${s.name}</span>
                <span class="service-row-desc">${s.description}</span>
                <span class="service-row-time">~${s.estimated_time} мин</span>
                <button class="btn btn-xs btn-danger" onclick="deleteService(${s.id})">✕</button>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

function switchTab(tab, btn) {
    currentTab = tab;
    document.querySelectorAll('.queue-tabs .tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    loadQueue();
}

async function callNext(windowId) {
    const serviceId = document.getElementById('filterService').value;
    const body = { window_id: windowId };
    if (serviceId) body.service_id = parseInt(serviceId);
    try {
        const res = await fetch('/api/queue/call-next', {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Вызван: ${data.ticket.ticket_number}`, 'success');
            refreshAll();
            if (window.socket) socket.emit('queue_updated');
        } else { showToast(data.error, 'error'); }
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function completeTicket(id) {
    try {
        const res = await fetch(`/api/tickets/${id}/complete`, { method: 'POST' });
        const data = await res.json();
        if (data.success) { showToast('Обслуживание завершено', 'success'); refreshAll(); if(window.socket) socket.emit('queue_updated'); }
        else showToast(data.error, 'error');
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function cancelTicket(id) {
    if (!confirm('Отменить талон?')) return;
    try {
        const res = await fetch(`/api/tickets/${id}/cancel`, { method: 'POST' });
        const data = await res.json();
        if (data.success) { showToast('Талон отменён', 'success'); refreshAll(); if(window.socket) socket.emit('queue_updated'); }
        else showToast(data.error, 'error');
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function skipTicket(id) {
    try {
        const res = await fetch(`/api/tickets/${id}/skip`, { method: 'POST' });
        const data = await res.json();
        if (data.success) { showToast('Пропущен', 'info'); refreshAll(); if(window.socket) socket.emit('queue_updated'); }
        else showToast(data.error, 'error');
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function toggleWindow(id) {
    try {
        await fetch(`/api/windows/${id}/toggle`, { method: 'POST' });
        refreshAll();
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function addWindow() {
    const name = prompt('Название окна:', `Окно ${Date.now() % 100}`);
    if (!name) return;
    const operator = prompt('Имя оператора:', 'Оператор');
    try {
        await fetch('/api/windows', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ name, operator_name: operator || 'Оператор' })
        });
        refreshAll();
        showToast('Окно добавлено', 'success');
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function addService() {
    const name = prompt('Название услуги:');
    if (!name) return;
    const icon = prompt('Иконка (emoji):', '📋');
    const time = prompt('Время обслуживания (мин):', '10');
    try {
        await fetch('/api/services', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ name, icon: icon || '📋', estimated_time: parseInt(time) || 10, description: '' })
        });
        refreshAll();
        showToast('Услуга добавлена', 'success');
    } catch(e) { showToast('Ошибка', 'error'); }
}

async function deleteService(id) {
    if (!confirm('Удалить услугу?')) return;
    try {
        await fetch(`/api/services/${id}`, { method: 'DELETE' });
        refreshAll();
        showToast('Услуга удалена', 'success');
    } catch(e) { showToast('Ошибка', 'error'); }
}

function refreshAll() {
    loadAdminStats();
    loadWindows();
    loadQueue();
    loadServicesList();
}

refreshAll();
setInterval(refreshAll, 5000);

try {
    const socket = io();
    socket.on('queue_update', () => refreshAll());
    window.socket = socket;
} catch(e) {}
