/**
 * dashboard.js
 * ============
 * Handles pages/admin/dashboard.html
 *   - Loads live stats into the four stats cards
 *   - Loads recent tickets into the Recent Tickets table
 *
 * Stats cards in order: Total Tickets / Pending / Translated Today / Approved
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  if (!document.title.includes('Dashboard')) return;

  if (!getToken()) {
    window.location.href = '../../pages/admin/login.html';
    return;
  }

  loadDashboardStats();
  loadRecentTickets();
});

// ── Stats cards ───────────────────────────────────────────────────────────────
async function loadDashboardStats() {
  try {
    const data  = await apiCall('/dashboard/stats');
    const stats = data.stats;
    const cards = document.querySelectorAll('.stats-card h2');

    // Cards in order: Total / Pending / Translated Today / Approved
    if (cards[0]) cards[0].textContent = stats.total_tickets.toLocaleString();
    if (cards[1]) cards[1].textContent = stats.pending.toLocaleString();
    if (cards[2]) cards[2].textContent = stats.translated_today.toLocaleString();
    if (cards[3]) cards[3].textContent = (stats.approved || 0).toLocaleString();

  } catch (err) {
    console.error('Failed to load dashboard stats:', err.message);
  }
}

// ── Recent tickets table ──────────────────────────────────────────────────────
async function loadRecentTickets() {
  try {
    const data  = await apiCall('/tickets/recent?limit=10');
    const tbody = document.querySelector('tbody');
    if (!tbody) return;

    if (!data.tickets.length) {
      tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#94a3b8;">No tickets yet.</td></tr>';
      return;
    }

    tbody.innerHTML = data.tickets.map(t => `
      <tr style="cursor:pointer;" onclick="window.location.href='history.html'">
        <td>#${t.id}</td>
        <td>${t.source_language.toUpperCase()}</td>
        <td>
          <span style="
            padding:3px 10px; border-radius:50px; font-size:.8rem; font-weight:600;
            background:${statusColor(t.status)}; color:#fff;
          ">${capitalise(t.status)}</span>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Failed to load recent tickets:', err.message);
  }
}

function statusColor(status) {
  return { pending: '#f59e0b', approved: '#22c55e', rejected: '#ef4444', translated: '#0284c7' }[status] || '#64748b';
}

function capitalise(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
