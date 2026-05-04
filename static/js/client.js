let selectedServiceId = null;

async function loadServices() {
    const res = await fetch('/api/services');
    const services = await res.json();
    document.getElementById('serviceCards').innerHTML = services.map(s => `
        <div class="service-card" onclick="selectService(${s.id}, this)" data-id="${s.id}">
            <span class="service-icon">${s.icon}</span>
            <span class="service-name">${s.name}</span>
            <span class="service-time">~${s.estimated_time} мин</span>
        </div>
    `).join('');
}

function selectService(id, el) {
    document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    selectedServiceId = id;
}

async function loadQueueStats() {
    try {
        const [qr, ar] = await Promise.all([fetch('/api/queue'), fetch('/api/analytics/today')]);
        const queue = await qr.json(), analytics = await ar.json();
        document.getElementById('miniWaiting').textContent = queue.total_waiting;
        document.getElementById('miniServing').textContent = queue.total_serving;
        document.getElementById('miniAvgWait').textContent = `~${analytics.avg_wait_time} мин`;
        const listEl = document.getElementById('queueListMini');
        if (queue.waiting.length === 0) {
            listEl.innerHTML = '<p class="text-muted text-center">Очередь пуста 🎉</p>';
        } else {
            listEl.innerHTML = queue.waiting.slice(0, 5).map(t => `
                <div class="queue-item-mini">
                    <span class="queue-item-num">${t.ticket_number}</span>
                    <span class="queue-item-name">${t.client_name}</span>
                    <span class="queue-item-service">${t.service_icon} ${t.service_name}</span>
                </div>
            `).join('');
        }
    } catch(e) { console.error(e); }
}

async function registerInQueue(e) {
    e.preventDefault();
    if (!selectedServiceId) { showToast('Выберите услугу', 'error'); return; }
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    try {
        const res = await fetch('/api/tickets', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({
                client_name: document.getElementById('clientName').value,
                client_phone: document.getElementById('clientPhone').value,
                service_id: selectedServiceId
            })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('registrationSection').classList.add('hidden');
            document.getElementById('ticketResult').classList.remove('hidden');
            document.getElementById('resultTicketNumber').textContent = data.ticket.ticket_number;
            document.getElementById('resultService').textContent = data.ticket.service_name;
            document.getElementById('resultPosition').textContent = `#${data.ticket.position}`;
            document.getElementById('resultWait').textContent = `~${data.ticket.position * 10} мин`;
            
            // Store current ticket ID for telegram linking
            window.currentTicketId = data.ticket.id;
            
            document.getElementById('trackingLink').innerHTML = `
                <input type="text" value="${data.token}" class="form-input" readonly onclick="this.select()">
                <div class="telegram-link-box" style="margin-top:1rem">
                    <button class="btn btn-sm btn-glass btn-block" onclick="promptTelegramLink()">
                        ✈️ Уведомить в Telegram
                    </button>
                </div>
            `;
            showToast('Вы успешно записаны!', 'success');
            if (window.socket) socket.emit('queue_updated');
        } else { showToast(data.error, 'error'); }
    } catch(e) { showToast('Ошибка сети', 'error'); }
    btn.disabled = false;
}

function showRegistration() {
    document.getElementById('registrationSection').classList.remove('hidden');
    document.getElementById('ticketResult').classList.add('hidden');
    document.getElementById('registerForm').reset();
    selectedServiceId = null;
    loadServices();
}

async function promptTelegramLink() {
    const chatId = prompt("Введите ваш Telegram Chat ID (можно узнать у бота @userinfobot):");
    if (!chatId) return;
    
    try {
        const res = await fetch(`/api/tickets/${window.currentTicketId}/link-telegram`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ chat_id: chatId })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Telegram успешно привязан!', 'success');
        } else {
            showToast(data.error, 'error');
        }
    } catch(e) {
        showToast('Ошибка привязки', 'error');
    }
}

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('token')) { document.getElementById('trackToken').value = urlParams.get('token'); trackTicket(); }

loadServices();
loadQueueStats();
setInterval(loadQueueStats, 5000);
