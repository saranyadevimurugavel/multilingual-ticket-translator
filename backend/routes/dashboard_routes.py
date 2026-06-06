"""
Dashboard Routes
================
Serves: pages/admin/dashboard.html

Stats cards the HTML shows:
  - Total Tickets   → 12,458  (hardcoded in HTML — we replace with live data)
  - Pending         → 248
  - Translated Today→ 1,234
  - Glossary Terms  → 8,912
"""

from datetime import datetime, date
from flask import Blueprint, jsonify
from database import db, Ticket, GlossaryTerm
from middleware import admin_required
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    Called by: pages/admin/dashboard.html — four stats cards

    Response 200:
        {
          "success": true,
          "stats": {
            "total_tickets":     42,
            "pending":           8,
            "translated_today":  5,
            "glossary_terms":    12,
            "approved":          20,
            "rejected":          4,
            "by_language": [
              { "language": "fr", "count": 15 },
              { "language": "ta", "count": 10 }
            ],
            "by_priority": [
              { "priority": "High", "count": 12 },
              { "priority": "Medium", "count": 20 }
            ]
          }
        }
    """
    today_start = datetime.combine(date.today(), datetime.min.time())

    total          = Ticket.query.count()
    pending        = Ticket.query.filter_by(status='pending').count()
    approved       = Ticket.query.filter_by(status='approved').count()
    rejected       = Ticket.query.filter_by(status='rejected').count()
    glossary_terms = GlossaryTerm.query.count()

    translated_today = (Ticket.query
                        .filter(Ticket.created_at >= today_start)
                        .count())

    # Breakdown by language
    by_language = (db.session.query(
                       Ticket.source_language,
                       func.count(Ticket.id).label('count'))
                   .group_by(Ticket.source_language)
                   .order_by(func.count(Ticket.id).desc())
                   .all())

    # Breakdown by priority
    by_priority = (db.session.query(
                       Ticket.priority,
                       func.count(Ticket.id).label('count'))
                   .group_by(Ticket.priority)
                   .all())

    return jsonify({
        'success': True,
        'stats': {
            'total_tickets':     total,
            'pending':           pending,
            'approved':          approved,
            'rejected':          rejected,
            'translated_today':  translated_today,
            'glossary_terms':    glossary_terms,
            'by_language': [
                {'language': r.source_language, 'count': r.count}
                for r in by_language
            ],
            'by_priority': [
                {'priority': r.priority, 'count': r.count}
                for r in by_priority
            ],
        },
    }), 200
