// ─── Global App JavaScript ──────────────────────────────────

// Toast notification system
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span><span class="toast-msg">${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function createToastContainer() {
    const c = document.createElement('div');
    c.id = 'toastContainer';
    c.className = 'toast-container';
    document.body.appendChild(c);
    return c;
}

// Socket.IO setup
let socket;
try {
    socket = io();
    socket.on('connect', () => console.log('🔌 Connected to QueueSmart'));
    socket.on('queue_update', () => {
        console.log('📢 Queue updated');
        document.dispatchEvent(new CustomEvent('queueUpdate'));
    });
    window.socket = socket;
} catch(e) {
    console.log('Socket.IO not available');
}
