/**
 * translation.js
 * ==============
 * Handles pages/client/submit-ticket.html
 *   - Collects Subject, Language (dropdown), Message (textarea)
 *   - Calls POST /api/tickets/submit
 *   - Displays the full AI analysis result inline
 *
 * Also handles pages/admin/translation-center.html
 *   - Loads the next pending ticket from GET /api/tickets/pending
 *   - Approve / Reject buttons call the matching endpoints
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  const page = document.title;

  if (page.includes('Submit Ticket')) {
    initSubmitPage();
  } else if (page.includes('Translation Center')) {
    initTranslationCenter();
  }
});

// ══════════════════════════════════════════════════════════════════════════════
// SUBMIT TICKET PAGE
// ══════════════════════════════════════════════════════════════════════════════
function initSubmitPage() {
  const submitBtn = document.querySelector('.btn-primary');
  if (!submitBtn) return;

  submitBtn.addEventListener('click', async () => {

    // Read all three form fields
    const inputs   = document.querySelectorAll('.form-control');
    const subject  = inputs[0]?.value.trim();
    const language = inputs[1]?.value;          // <select> value
    const message  = inputs[2]?.value.trim();   // <textarea>

    if (!subject || !message) {
      showAlert('Subject and Message are required.', 'error');
      return;
    }

    submitBtn.textContent = '⏳ Analysing…';
    submitBtn.disabled    = true;

    // Remove any old result panel
    document.getElementById('ticket-result')?.remove();

    try {
      const data = await apiCall('/tickets/submit', {
        method: 'POST',
        body:   JSON.stringify({ subject, language, message }),
      });

      const t = data.ticket;
      renderTicketResult(t);
      showAlert('Ticket submitted successfully!', 'success');

      // Reset form
      inputs[0].value = '';
      inputs[2].value = '';

    } catch (err) {
      showAlert(err.message || 'Submission failed.', 'error');
    } finally {
      submitBtn.textContent = 'Submit Ticket';
      submitBtn.disabled    = false;
    }
  });
}

/**
 * Renders the AI analysis result card below the submit form.
 * Maps every field returned by /api/tickets/submit.
 */
function renderTicketResult(t) {
  const priorityColors = {
    Critical: '#7c3aed', High: '#dc2626', Medium: '#d97706', Low: '#16a34a'
  };
  const sentimentColors = {
    'Very Negative': '#dc2626', Negative: '#ea580c',
    Neutral: '#0284c7', Positive: '#16a34a'
  };

  const card = document.createElement('div');
  card.id = 'ticket-result';
  card.style.cssText = `
    margin-top:30px; padding:24px; background:#fff;
    border-radius:12px; border:1px solid #e2e8f0;
    box-shadow:0 4px 16px rgba(0,0,0,.08); animation:fadeIn .4s ease;
  `;

  card.innerHTML = `
    <style>
      @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
      .result-row { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
      .badge { padding:4px 14px; border-radius:50px; font-size:.82rem; font-weight:700; color:#fff; }
      .result-label { font-size:.75rem; font-weight:700; text-transform:uppercase;
                      letter-spacing:.05em; color:#64748b; margin-bottom:4px; display:block; }
      .result-box { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
                    padding:12px 14px; font-size:.95rem; line-height:1.6; margin-bottom:16px; }
      .result-box.response { background:#eff6ff; border-color:#bfdbfe; color:#1e40af; font-style:italic; }
    </style>

    <h3 style="margin-bottom:18px; color:#0f172a;">
      ✅ Ticket #${t.id} — AI Analysis Complete
    </h3>

    <div class="result-row">
      <div>
        <span class="result-label">Detected Language</span>
        <span class="badge" style="background:#0f172a">${t.source_language.toUpperCase()}</span>
      </div>
      <div>
        <span class="result-label">Category</span>
        <span class="badge" style="background:#0284c7">${t.category}</span>
      </div>
      <div>
        <span class="result-label">Priority</span>
        <span class="badge" style="background:${priorityColors[t.priority] || '#64748b'}">${t.priority}</span>
      </div>
      <div>
        <span class="result-label">Sentiment</span>
        <span class="badge" style="background:${sentimentColors[t.sentiment] || '#64748b'}">${t.sentiment}</span>
      </div>
      <div>
        <span class="result-label">AI Confidence</span>
        <span class="badge" style="background:#059669">${t.confidence ?? '—'}%</span>
      </div>
    </div>

    <span class="result-label">🔄 English Translation</span>
    <div class="result-box">${t.translated_message || '—'}</div>

    <span class="result-label">📋 Summary</span>
    <div class="result-box">${t.summary || '—'}</div>

    <span class="result-label">💬 Suggested Response</span>
    <div class="result-box response">${t.suggested_response || '—'}</div>
  `;

  // Insert after the submit card
  const card_wrapper = document.querySelector('.card');
  card_wrapper.insertAdjacentElement('afterend', card);
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// ══════════════════════════════════════════════════════════════════════════════
// TRANSLATION CENTER PAGE (admin)
// ══════════════════════════════════════════════════════════════════════════════
function initTranslationCenter() {
  loadPendingTicket();

  // Approve / Reject buttons
  document.addEventListener('click', async (e) => {

    const ticketId = document.getElementById('tc-ticket-id')?.dataset.id;
    if (!ticketId) return;

    if (e.target.classList.contains('btn-primary') &&
        e.target.textContent.trim() === 'Approve') {
      await handleAction(ticketId, 'approve');
    }

    if (e.target.classList.contains('btn-danger') &&
        e.target.textContent.trim() === 'Reject') {
      await handleAction(ticketId, 'reject');
    }
  });
}

async function loadPendingTicket() {
  try {
    const data = await apiCall('/tickets/pending');
    const t    = data.ticket;

    if (!t) {
      // No pending tickets — show empty state
      const panels = document.querySelectorAll('.translation-text');
      panels.forEach(p => { p.value = 'No pending tickets.'; });
      return;
    }

    // Populate both translation panels
    const panels = document.querySelectorAll('.translation-text');
    if (panels[0]) panels[0].value = t.original_message;
    if (panels[1]) panels[1].value = t.translated_message;

    // Update language badges
    const badges = document.querySelectorAll('.language-badge');
    if (badges[0]) badges[0].textContent = (t.source_language || 'Unknown').toUpperCase();
    if (badges[1]) badges[1].textContent = 'English';

    // Confidence score
    const conf = document.querySelector('.confidence-score');
    if (conf) conf.textContent = `AI Confidence: ${t.confidence || 95}%`;

    // Store ticket ID on a hidden element for the approve/reject handlers
    let idEl = document.getElementById('tc-ticket-id');
    if (!idEl) {
      idEl = document.createElement('span');
      idEl.id = 'tc-ticket-id';
      idEl.style.display = 'none';
      document.body.appendChild(idEl);
    }
    idEl.dataset.id = t.id;

  } catch (err) {
    console.error('Failed to load pending ticket:', err.message);
  }
}

async function handleAction(ticketId, action) {
  try {
    await apiCall(`/tickets/${ticketId}/${action}`, { method: 'POST' });
    showAlert(`Ticket #${ticketId} ${action}d!`, 'success');
    // Load next pending ticket
    setTimeout(loadPendingTicket, 800);
  } catch (err) {
    showAlert(err.message, 'error');
  }
}
