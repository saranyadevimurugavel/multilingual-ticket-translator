"""
Glossary Routes
===============
Serves: pages/admin/glossary.html

Form fields on the page:
  - Term input        → term
  - Translation input → translation
  - Add Term button   → POST /api/glossary/add
  - Table of terms    → GET  /api/glossary
  - Delete            → DELETE /api/glossary/<id>
"""

from flask import Blueprint, request, jsonify
from database import db, GlossaryTerm
from middleware import admin_required

glossary_bp = Blueprint('glossary', __name__)


@glossary_bp.route('', methods=['GET'])
@admin_required
def list_terms():
    """
    Called by: pages/admin/glossary.html on page load to populate the table.

    Response 200:
        {
          "success": true,
          "terms": [
            { "id": 1, "term": "VPN", "translation": "Réseau Privé Virtuel",
              "language": "fr", "created_at": "..." },
            ...
          ],
          "total": 12
        }
    """
    search = request.args.get('q', '').strip()

    query = GlossaryTerm.query
    if search:
        query = query.filter(
            GlossaryTerm.term.ilike(f'%{search}%') |
            GlossaryTerm.translation.ilike(f'%{search}%')
        )

    terms = query.order_by(GlossaryTerm.term).all()

    return jsonify({
        'success': True,
        'terms':   [t.to_dict() for t in terms],
        'total':   len(terms),
    }), 200


@glossary_bp.route('/add', methods=['POST'])
@admin_required
def add_term():
    """
    Called by: pages/admin/glossary.html → Add Term button

    Request JSON:
        { "term": "VPN", "translation": "Réseau Privé Virtuel", "language": "fr" }

    Response 201:
        { "success": true, "term": { ...term dict... } }
    """
    data = request.get_json(silent=True) or {}

    term        = (data.get('term')        or '').strip()
    translation = (data.get('translation') or '').strip()
    language    = (data.get('language')    or '').strip()

    if not term or not translation:
        return jsonify({'success': False, 'error': 'Term and translation are required'}), 400

    new_term = GlossaryTerm(term=term, translation=translation, language=language)
    db.session.add(new_term)
    db.session.commit()

    return jsonify({'success': True, 'term': new_term.to_dict()}), 201


@glossary_bp.route('/<int:term_id>', methods=['DELETE'])
@admin_required
def delete_term(term_id):
    """
    Called by: pages/admin/glossary.html → delete button on each row.

    Response 200:
        { "success": true, "message": "Term deleted" }
    """
    term = GlossaryTerm.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Term deleted'}), 200


@glossary_bp.route('/<int:term_id>', methods=['PUT'])
@admin_required
def update_term(term_id):
    """Update an existing glossary term."""
    term = GlossaryTerm.query.get_or_404(term_id)
    data = request.get_json(silent=True) or {}

    if 'term' in data:        term.term        = data['term'].strip()
    if 'translation' in data: term.translation = data['translation'].strip()
    if 'language' in data:    term.language    = data['language'].strip()

    db.session.commit()
    return jsonify({'success': True, 'term': term.to_dict()}), 200
