"""
Batch Processing Routes
=======================
POST /api/batch/process-folder   — scan folder, process all tickets
POST /api/batch/reply            — translate engineer reply back to original lang
GET  /api/batch/status           — get all batch-processed tickets
"""

import os
from pathlib import Path
from flask import Blueprint, request, jsonify
from middleware import admin_required
from services.batch_service import process_folder, translate_reply

batch_bp = Blueprint('batch', __name__)

# Default folder — relative to project root
DEFAULT_FOLDER = os.path.join(
    os.path.dirname(__file__), '..', '..', 'sample_tickets'
)


@batch_bp.route('/process-folder', methods=['POST'])
@admin_required
def process_batch():
    """
    Scans a folder of .txt/.json ticket files and processes each one.

    Request JSON (optional):
        { "folder_path": "/absolute/path/to/tickets" }
        If omitted, uses the default sample_tickets/ folder.

    Response 200:
        {
          "success": true,
          "summary": {
            "total": 8, "processed": 7, "skipped": 1
          },
          "results": [ { ticket details per file }, ... ],
          "errors":  [ { "file": "...", "error": "..." } ]
        }
    """
    data        = request.get_json(silent=True) or {}
    folder_path = data.get('folder_path') or DEFAULT_FOLDER
    folder_path = str(Path(folder_path).resolve())

    if not os.path.isdir(folder_path):
        return jsonify({
            'success': False,
            'error':   f'Folder not found: {folder_path}'
        }), 400

    try:
        result = process_folder(folder_path)
        return jsonify({
            'success': True,
            'summary': {
                'total':     result['total'],
                'processed': result['processed'],
                'skipped':   result['skipped'],
            },
            'results': result['results'],
            'errors':  result['errors'],
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@batch_bp.route('/reply', methods=['POST'])
@admin_required
def reply_to_ticket():
    """
    Translates an engineer's English reply back to the ticket's
    original language and stores both versions.

    Request JSON:
        {
          "ticket_id":     3,
          "english_reply": "We have resolved your issue. Please restart your device."
        }

    Response 200:
        {
          "success": true,
          "data": {
            "ticket_id":        3,
            "english_reply":    "We have resolved your issue...",
            "translated_reply": "நாங்கள் உங்கள் சிக்கலை தீர்த்துள்ளோம்...",
            "target_language":  "ta",
            "language_name":    "Tamil"
          }
        }
    """
    data = request.get_json(silent=True) or {}

    ticket_id     = data.get('ticket_id')
    english_reply = (data.get('english_reply') or '').strip()

    if not ticket_id:
        return jsonify({'success': False, 'error': 'ticket_id is required'}), 400
    if not english_reply:
        return jsonify({'success': False, 'error': 'english_reply is required'}), 400

    try:
        result = translate_reply(int(ticket_id), english_reply)
        return jsonify({'success': True, 'data': result}), 200
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@batch_bp.route('/status', methods=['GET'])
@admin_required
def batch_status():
    """Returns all tickets that came from batch processing (status=pending/approved)."""
    from database import Ticket
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'tickets': [t.to_dict() for t in tickets],
        'total':   len(tickets),
    }), 200
