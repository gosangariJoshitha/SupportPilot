document.addEventListener('DOMContentLoaded', () => {
    // Dynamic greeting based on user's local time
    const greetingEl = document.getElementById('greeting-text');
    if (greetingEl) {
        const hour = new Date().getHours();
        let greeting = 'Good evening';
        if (hour < 12) greeting = 'Good morning';
        else if (hour < 17) greeting = 'Good afternoon';
        greetingEl.textContent = greeting;
    }

    // Only run dashboard init if we are on the dashboard
    if (document.getElementById('kpi-container')) {
        loadDashboardData();
    }

    // Modal form submission
    const ticketModalForm = document.getElementById('ticketModalForm');
    if (ticketModalForm) {
        ticketModalForm.addEventListener('submit', handleModalSubmit);
    }
});

let activityChartInstance = null;
let categoryChartInstance = null;

async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/summary');
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        
        const data = await response.json();
        
        // Update KPIs
        document.getElementById('kpi-total').textContent = data.total_tickets;
        document.getElementById('kpi-open').textContent = data.open_tickets;
        document.getElementById('kpi-resolved').textContent = data.resolved_tickets;

        let highPriorityCount = (data.priority_distribution.P1 || 0) + (data.priority_distribution.P2 || 0);
        document.getElementById('kpi-high-priority').textContent = highPriorityCount;

        const accuracyEl = document.getElementById('kpi-accuracy');
        if (accuracyEl) {
            const accuracyValue = data.classification_accuracy != null ? (data.classification_accuracy * 100).toFixed(1) : '—';
            accuracyEl.textContent = accuracyValue === '—' ? '—' : accuracyValue + '%';
        }

        const avgConfidenceEl = document.getElementById('kpi-avg-confidence');
        if (avgConfidenceEl) {
            avgConfidenceEl.textContent = data.avg_classification_confidence != null ? data.avg_classification_confidence.toFixed(1) + '%' : '—';
        }

        const avgResolutionEl = document.getElementById('kpi-avg-resolution');
        if (avgResolutionEl) {
            avgResolutionEl.textContent = data.avg_resolution_confidence != null ? data.avg_resolution_confidence.toFixed(1) + '%' : '—';
        }

        const aiRateEl = document.getElementById('kpi-ai-rate');
        if (aiRateEl) {
            aiRateEl.textContent = data.ai_resolution_rate != null ? data.ai_resolution_rate.toFixed(1) + '%' : '—';
        }

        // Update Charts
        renderActivityChart(data.ticket_activity);
        renderCategoryChart(data.category_distribution);
        
        // Update Severity & Priority Distribution
        renderDistribution('severity-container', data.severity_distribution, getSeverityColor);
        renderDistribution('priority-container', data.priority_distribution, getPriorityColor);
        
        // Update Recent Tickets
        renderRecentTickets(data.recent_tickets);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function renderDistribution(containerId, data, colorFn) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    
    if (total === 0) {
        container.innerHTML = '<div class="text-muted small">No data available</div>';
        return;
    }
    
    for (const [key, value] of Object.entries(data)) {
        if (value === 0) continue;
        const percentage = ((value / total) * 100).toFixed(1);
        const color = colorFn(key);
        
        const html = `
            <div class="light-card p-2 flex-grow-1 text-center" style="min-width: 90px;">
                <div class="small fw-semibold mb-1" style="color: ${color}">${key}</div>
                <div class="fs-3 fw-bold text-dark">${value}</div>
                <div class="text-muted mt-1" style="font-size: 0.75rem;">${percentage}%</div>
            </div>
        `;
        container.innerHTML += html;
    }
}

function getSeverityColor(sev) {
    switch(sev) {
        case 'Critical': return '#ef4444'; // var(--danger)
        case 'High': return '#f59e0b';     // var(--warning)
        case 'Medium': return '#0ea5e9';   // var(--info)
        case 'Low': return '#10b981';      // var(--success)
        default: return '#94a3b8';         // var(--text-secondary)
    }
}

function getPriorityColor(pri) {
    switch(pri) {
        case 'P1': return '#ef4444';
        case 'P2': return '#f59e0b';
        case 'P3': return '#0ea5e9';
        case 'P4': return '#10b981';
        default: return '#94a3b8';
    }
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'Open': return 'badge-soft-warning';
        case 'In Progress': return 'badge-soft-info';
        case 'Resolved': return 'badge-soft-success';
        case 'Closed': return 'badge-soft-secondary';
        default: return 'badge-soft-primary';
    }
}

function renderRecentTickets(tickets) {
    const tbody = document.getElementById('dashboard-recent-tickets');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!tickets || tickets.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted border-secondary">No recent tickets found.</td></tr>`;
        return;
    }
    
    tickets.forEach(ticket => {
        let badgeClass = getStatusBadgeClass(ticket.status);
        let sevColor = getSeverityColor(ticket.severity);
        let priColor = getPriorityColor(ticket.priority);
        
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.className = "hover-card";
        tr.onclick = () => window.location.href = `/ticket/${ticket.ticket_id}`;
        
        tr.innerHTML = `
            <td class="ps-4 border-secondary fw-medium text-muted py-3">#T-${ticket.ticket_id}</td>
            <td class="border-secondary fw-medium text-dark text-truncate py-3" style="max-width: 200px;">${ticket.title}</td>
            <td class="border-secondary py-3"><span class="badge badge-soft-info px-2">${ticket.category}</span></td>
            <td class="border-secondary fw-medium py-3" style="color: ${sevColor}">${ticket.severity}</td>
            <td class="border-secondary fw-medium py-3" style="color: ${priColor}">${ticket.priority}</td>
            <td class="border-secondary py-3">
                <span class="badge rounded-pill ${badgeClass} px-3 py-2">${ticket.status}</span>
            </td>
            <td class="text-end pe-4 border-secondary text-muted small py-3">${formatDate(ticket.created_at)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
}

function renderActivityChart(data) {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;
    
    if (activityChartInstance) activityChartInstance.destroy();
    
    Chart.defaults.color = '#64748b';
    Chart.defaults.font.family = 'Inter';
    
    activityChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates.length > 0 ? data.dates : ['No Data'],
            datasets: [{
                label: 'Tickets Created',
                data: data.counts.length > 0 ? data.counts : [0],
                borderColor: '#3b82f6', // primary blue
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#0f172a',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { precision: 0 }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    if (categoryChartInstance) categoryChartInstance.destroy();
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    if (values.length === 0) {
        labels.push("None");
        values.push(1);
    }
    
    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#3b82f6', // blue
                    '#10b981', // emerald
                    '#8b5cf6', // purple
                    '#f59e0b', // amber
                    '#ef4444', // red
                    '#06b6d4'  // cyan
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#475569',
                        usePointStyle: true,
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

async function handleModalSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('modalSubmitBtn');
    
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Analyzing...`;
    btn.disabled = true;

    const formData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        business_impact: document.getElementById('business_impact').value
    };

    try {
        const res = await fetch('/api/tickets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (res.ok) {
            const ticket = await res.json();
            
            // Show result state in modal
            document.getElementById('ticketModalForm').classList.add('d-none');
            document.getElementById('modal-result-state').classList.remove('d-none');
            
            document.getElementById('res-modal-cat').textContent = ticket.category;
            
            const sevEl = document.getElementById('res-modal-sev');
            sevEl.textContent = ticket.severity;
            sevEl.style.color = getSeverityColor(ticket.severity);
            
            const priEl = document.getElementById('res-modal-pri');
            priEl.textContent = ticket.priority;
            priEl.style.color = getPriorityColor(ticket.priority);
            
            document.getElementById('res-modal-conf').textContent = (ticket.confidence * 100).toFixed(1) + '%';
            
            // Re-fetch dashboard data in background
            loadDashboardData();
        } else {
            alert('Failed to submit ticket. Please try again.');
        }
    } catch (err) {
        console.error(err);
        alert('An error occurred.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function resetModalForm() {
    const form = document.getElementById('ticketModalForm');
    if (form) {
        form.reset();
        form.classList.remove('d-none');
        
        const resultState = document.getElementById('modal-result-state');
        if (resultState) {
            resultState.classList.add('d-none');
        }
    }
}
