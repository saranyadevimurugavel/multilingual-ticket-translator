"""
Ticket Routes
=============
Serves every API call made by the ticket-related frontend pages.

  pages/client/submit-ticket.html
      POST /api/tickets/submit
          fields: subject, language (dropdown), message (textarea)

  pages/admin/dashboard.html
      GET /api/tickets/recent          → table of recent tickets (ID, Language, Status)

  pages/admin/translation-center.html
      GET  /api/tickets/pending        → next ticket awaiting approval
      POST /api/tickets/<id>/approve   → approve translation
      POST /api/tickets/<id>/reject    → reject translation

  pages/admin/history.html
      GET  /api/tickets/history        → all tickets with filters
      POST /api/tickets/<id>/approve   → approve from history view
      POST /api/tickets/<id>/reject    → reject from history view
"""

from flask import Blueprint, request, jsonify, g
from database import db, Ticket
from services.ai_service import process_ticket
from middleware import login_required, admin_required

ticket_bp = Blueprint('tickets', __name__)


# ── Submit ticket (client page) ───────────────────────────────────────────────
@ticket_bp.route('/submit', methods=['POST'])
def submit_ticket():
    """
    Called by: pages/client/submit-ticket.html → Submit Ticket button

    Request JSON:
        {
          "subject":  "Cannot access my account",
          "language": "French",          ← from the <select> dropdown
          "message":  "Bonjour, je ne peux pas accéder à mon compte."
        }

    Response 201:
        {
          "success": true,
          "ticket": {
            "id": 3,
            "subject": "Cannot access my account",
            "source_language": "fr",
            "language_name": "French",
            "original_message": "Bonjour...",
            "translated_message": "Hello, I cannot access my account.",
            "category": "Account Issue",
            "priority": "High",
            "sentiment": "Negative",
            "summary": "Customer cannot access their account.",
            "suggested_response": "We are looking into your account access...",
            "confidence": 96,
            "status": "pending"
          }
        }
    """
    data = request.get_json(silent=True) or {}

    subject  = (data.get('subject')  or '').strip()
    message  = (data.get('message')  or '').strip()
    language = (data.get('language') or '').strip()  # hint from dropdown

    if not subject:
        return jsonify({'success': False, 'error': 'Subject is required'}), 400
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400

    # Run the full AI pipeline
    result = process_ticket(subject, message, hint_language=language or None)

    # Persist
    ticket = Ticket(
        subject            = subject,
        original_message   = message,
        source_language    = result['source_language'],
        translated_message = result['translated_message'],
        category           = result['category'],
        priority           = result['priority'],
        sentiment          = result['sentiment'],
        summary            = result['summary'],
        suggested_response = result['suggested_response'],
        status             = 'pending',
    )
    db.session.add(ticket)
    db.session.commit()

    response_data = ticket.to_dict()
    response_data['language_name'] = result['language_name']
    response_data['confidence']    = result['confidence']

    return jsonify({'success': True, 'ticket': response_data}), 201


# ── Recent tickets (dashboard table) ─────────────────────────────────────────
@ticket_bp.route('/recent', methods=['GET'])
@admin_required
def recent_tickets():
    """
    Called by: pages/admin/dashboard.html — Recent Tickets table
    Columns the table shows: ID, Language, Status

    Response 200:
        {
          "success": true,
          "tickets": [
            { "id": 1001, "source_language": "French", "status": "Translated" },
            { "id": 1002, "source_language": "German",  "status": "Pending"    }
          ]
        }
    """
    limit = request.args.get('limit', 10, type=int)

    tickets = (Ticket.query
               .order_by(Ticket.created_at.desc())
               .limit(limit)
               .all())

    rows = [
        {
            'id':              t.id,
            'subject':         t.subject,
            'source_language': t.source_language,
            'status':          t.status.capitalize(),
            'priority':        t.priority,
            'category':        t.category,
            'created_at':      t.created_at.isoformat(),
        }
        for t in tickets
    ]

    return jsonify({'success': True, 'tickets': rows}), 200


# ── Pending ticket for translation-center ─────────────────────────────────────
@ticket_bp.route('/pending', methods=['GET'])
@admin_required
def get_pending():
    """
    Called by: pages/admin/translation-center.html
    Returns the oldest pending ticket for review.

    Response 200:
        {
          "success": true,
          "ticket": { ...full ticket dict... }
        }

    Response 200 (no pending tickets):
        { "success": true, "ticket": null }
    """
    ticket = (Ticket.query
              .filter_by(status='pending')
              .order_by(Ticket.created_at.asc())
              .first())

    return jsonify({
        'success': True,
        'ticket':  ticket.to_dict() if ticket else None,
    }), 200


# ── History / all tickets ─────────────────────────────────────────────────────
@ticket_bp.route('/history', methods=['GET'])
@admin_required
def ticket_history():
    """
    Called by: pages/admin/history.html — Translation Queue

    Query params:
        status    = pending | translated | approved | rejected  (optional)
        language  = fr | ta | hi | ...                          (optional)
        page      = 1                                           (optional)
        limit     = 20                                          (optional)

    Response 200:
        {
          "success": true,
          "tickets": [...],
          "total": 42,
          "page": 1,
          "pages": 3
        }
    """
    status   = request.args.get('status')
    language = request.args.get('language')
    page     = request.args.get('page',  1,  type=int)
    limit    = request.args.get('limit', 20, type=int)

    query = Ticket.query
    if status:
        query = query.filter_by(status=status)
    if language:
        query = query.filter_by(source_language=language)

    total      = query.count()
    tickets    = (query
                  .order_by(Ticket.created_at.desc())
                  .offset((page - 1) * limit)
                  .limit(limit)
                  .all())

    return jsonify({
        'success': True,
        'tickets': [t.to_dict() for t in tickets],
        'total':   total,
        'page':    page,
        'pages':   (total + limit - 1) // limit,
    }), 200


# ── Get single ticket ─────────────────────────────────────────────────────────
@ticket_bp.route('/<int:ticket_id>', methods=['GET'])
@admin_required
def get_ticket(ticket_id):
    """
    Called by: history.html when an agent clicks a row to review it.
    Populates all form fields: Ticket ID, Source Language, Target Language,
    Original Ticket textarea, Translated Ticket textarea.
    """
    ticket = Ticket.query.get_or_404(ticket_id)
    return jsonify({'success': True, 'ticket': ticket.to_dict()}), 200


# ── Approve translation ────────────────────────────────────────────────────────
@ticket_bp.route('/<int:ticket_id>/approve', methods=['POST'])
@admin_required
def approve_ticket(ticket_id):
    """
    Called by:
      - pages/admin/translation-center.html → Approve button
      - pages/admin/history.html            → Approve Translation button

    Response 200:
        { "success": true, "message": "Ticket #3 approved", "status": "approved" }
    """
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = 'approved'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Ticket #{ticket_id} approved',
        'status':  'approved',
    }), 200


# ── Reject translation ─────────────────────────────────────────────────────────
@ticket_bp.route('/<int:ticket_id>/reject', methods=['POST'])
@admin_required
def reject_ticket(ticket_id):
    """
    Called by:
      - pages/admin/translation-center.html → Reject button
      - pages/admin/history.html            → Reject button

    Request JSON (optional):
        { "reason": "Translation is inaccurate" }

    Response 200:
        { "success": true, "message": "Ticket #3 rejected", "status": "rejected" }
    """
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = 'rejected'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Ticket #{ticket_id} rejected',
        'status':  'rejected',
    }), 200
