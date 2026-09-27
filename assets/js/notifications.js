document.addEventListener('DOMContentLoaded', () => {
    // Dropdowns are handled by Bootstrap 5
    const notifBtn = document.getElementById('notif-btn');
    if (notifBtn) {
        notifBtn.addEventListener('click', (e) => {
            // Load notifications whenever the bell is clicked
            loadNotifications();
        });
    }

    // Notifications logic
    // Notifications logic
    const notifBadge = document.querySelector('.notification-badge');
    const notifList = document.getElementById('notif-list');
    const markAllReadBtn = document.getElementById('mark-all-read-btn');

    async function loadUnreadCount() {
        try {
            const res = await fetch('/api/notifications/unread-count');
            if (res.ok) {
                const data = await res.json();
                if (data.count > 0) {
                    if (notifBadge) {
                        notifBadge.textContent = data.count > 99 ? '99+' : data.count;
                        notifBadge.style.display = 'flex';
                    }
                } else {
                    if (notifBadge) notifBadge.style.display = 'none';
                }
            }
        } catch (e) { console.error(e); }
    }

    async function loadNotifications() {
        if (!notifList) return;
        notifList.innerHTML = '<div class="dropdown-item py-3 px-3 small text-muted text-center">Loading...</div>';
        try {
            const res = await fetch('/api/notifications');
            if (res.ok) {
                const data = await res.json();
                renderNotifications(data);
            }
        } catch (e) { console.error(e); }
    }

    function renderNotifications(notifs) {
        if (!notifList) return;
        const unreadNotifs = notifs.filter(n => !n.is_read);
        if (unreadNotifs.length === 0) {
            notifList.innerHTML = '<div class="dropdown-item py-3 px-3 small text-muted text-center">No new notifications</div>';
            return;
        }

        notifList.innerHTML = unreadNotifs.map(n => `
            <div class="dropdown-item notif-item unread py-2 px-3 border-bottom" data-id="${n.notification_id}" data-ticket="${n.ticket_id || ''}" style="cursor:pointer; white-space: normal;">
                <p class="notif-title fw-semibold text-dark mb-1 small">${n.title}</p>
                <p class="notif-msg text-muted mb-0" style="font-size: 0.75rem;">${n.message}</p>
            </div>
        `).join('');

        notifList.querySelectorAll('.notif-item').forEach(item => {
            item.addEventListener('click', async () => {
                const id = item.getAttribute('data-id');
                const ticketId = item.getAttribute('data-ticket');
                
                // Mark read
                await fetch(`/api/notifications/${id}/read`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': window.CSRF_TOKEN || '' }
                });
                
                if (ticketId && ticketId !== "null") {
                    window.location.href = `/ticket/${ticketId}`;
                } else {
                    item.remove();
                    if (notifList.children.length === 0) {
                        notifList.innerHTML = '<div class="dropdown-item py-3 px-3 small text-muted text-center">No new notifications</div>';
                    }
                    loadUnreadCount();
                }
            });
        });
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', async () => {
            await fetch('/api/notifications/read-all', {
                method: 'POST',
                headers: { 'X-CSRFToken': window.CSRF_TOKEN || '' }
            });
            loadNotifications();
            loadUnreadCount();
            if (window.toast) window.toast.show('Success', 'All notifications marked as read', 'success');
        });
    }

    const clearAllBtn = document.getElementById('clear-all-notif-btn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', async () => {
            await fetch('/api/notifications/clear-all', {
                method: 'POST',
                headers: { 'X-CSRFToken': window.CSRF_TOKEN || '' }
            });
            loadNotifications();
            loadUnreadCount();
            if (window.toast) window.toast.show('Success', 'All notifications cleared', 'success');
        });
    }

    // Initial load
    loadUnreadCount();
    setInterval(loadUnreadCount, 30000);

    // Global Search
    const searchInput = document.getElementById('global-search-input');
    const searchDropdown = document.getElementById('search-dropdown');
    let searchTimeout = null;

    if (searchInput && searchDropdown) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                searchDropdown.classList.add('hidden');
                return;
            }
            
            if (searchTimeout) clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        });

        searchInput.addEventListener('click', (e) => {
            e.stopPropagation();
            if (searchInput.value.trim().length >= 2) {
                searchDropdown.classList.remove('hidden');
                searchDropdown.style.display = 'block';
            }
        });

        document.addEventListener('click', (e) => {
            if (!searchDropdown.contains(e.target) && e.target !== searchInput) {
                searchDropdown.style.display = 'none';
            }
        });
    }

    async function performSearch(query) {
        try {
            const res = await fetch('/api/tickets');
            if (res.ok) {
                const tickets = await res.json();
                const q = query.toLowerCase();
                const results = tickets.filter(t => 
                    String(t.ticket_id).includes(q) ||
                    (t.title && t.title.toLowerCase().includes(q)) ||
                    (t.description && t.description.toLowerCase().includes(q)) ||
                    (t.category && t.category.toLowerCase().includes(q))
                ).slice(0, 5);
                
                if (results.length > 0) {
                    searchDropdown.innerHTML = results.map(t => `
                        <a href="/ticket/${t.ticket_id}" class="search-result-item">
                            <div class="search-result-title">#${t.ticket_id} - ${t.title}</div>
                            <div class="search-result-sub">${t.category || 'No Category'} &middot; ${t.status}</div>
                        </a>
                    `).join('');
                } else {
                    searchDropdown.innerHTML = '<div class="p-3 text-muted text-center small">No tickets found.</div>';
                }
                searchDropdown.classList.remove('hidden');
                searchDropdown.style.display = 'block';
            }
        } catch (e) {
            console.error(e);
        }
    }
});
