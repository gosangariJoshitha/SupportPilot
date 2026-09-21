document.addEventListener('DOMContentLoaded', () => {
    // Dropdown toggles
    const userBtn = document.getElementById('user-dropdown-btn');
    const userDropdown = document.getElementById('user-dropdown');
    const notifBtn = document.getElementById('notif-btn');
    const notifDropdown = document.getElementById('notif-dropdown');
    
    function closeAllDropdowns() {
        if(userDropdown) userDropdown.classList.add('hidden');
        if(notifDropdown) notifDropdown.classList.add('hidden');
        const searchDropdown = document.getElementById('search-dropdown');
        if(searchDropdown) searchDropdown.classList.add('hidden');
    }

    if (userBtn && userDropdown) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = userDropdown.classList.contains('hidden');
            closeAllDropdowns();
            if (isHidden) userDropdown.classList.remove('hidden');
        });
    }

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = notifDropdown.classList.contains('hidden');
            closeAllDropdowns();
            if (isHidden) {
                notifDropdown.classList.remove('hidden');
                loadNotifications();
            }
        });
    }

    document.addEventListener('click', () => {
        closeAllDropdowns();
    });

    if (userDropdown) userDropdown.addEventListener('click', (e) => e.stopPropagation());
    if (notifDropdown) notifDropdown.addEventListener('click', (e) => e.stopPropagation());

    // Notifications logic
    const notifBadge = document.getElementById('notif-badge');
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
                        notifBadge.classList.remove('hidden');
                    }
                } else {
                    if (notifBadge) notifBadge.classList.add('hidden');
                }
            }
        } catch (e) { console.error(e); }
    }

    async function loadNotifications() {
        if (!notifList) return;
        notifList.innerHTML = '<div class="notif-empty">Loading...</div>';
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
            notifList.innerHTML = '<div class="notif-empty">No new notifications</div>';
            return;
        }

        notifList.innerHTML = unreadNotifs.map(n => `
            <div class="notif-item unread" data-id="${n.notification_id}" data-ticket="${n.ticket_id || ''}">
                <p class="notif-title">${n.title}</p>
                <p class="notif-msg">${n.message}</p>
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
                        notifList.innerHTML = '<div class="notif-empty">No new notifications</div>';
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
    if (notifBtn) {
        loadUnreadCount();
        setInterval(loadUnreadCount, 30000);
    }

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
                closeAllDropdowns();
                searchDropdown.classList.remove('hidden');
            }
        });

        searchDropdown.addEventListener('click', (e) => e.stopPropagation());
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
            }
        } catch (e) {
            console.error(e);
        }
    }
});
