"""
Database models — SQLite via Flask-SQLAlchemy.
All four tables map directly to what the frontend pages display.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ── User ──────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20), default='client')   # 'client' | 'admin'
    name       = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    def to_dict(self):
        return {'id': self.id, 'email': self.email,
                'role': self.role, 'name': self.name}


# ── Ticket ────────────────────────────────────────────────────────────────────
class Ticket(db.Model):
    __tablename__ = 'tickets'

    id                  = db.Column(db.Integer, primary_key=True)
    subject             = db.Column(db.String(200), nullable=False)
    original_message    = db.Column(db.Text, nullable=False)
    source_language     = db.Column(db.String(50), default='unknown')
    translated_message  = db.Column(db.Text, default='')
    category            = db.Column(db.String(80), default='')
    priority            = db.Column(db.String(20), default='Medium')
    sentiment           = db.Column(db.String(30), default='')
    summary             = db.Column(db.Text, default='')
    suggested_response  = db.Column(db.Text, default='')
    status              = db.Column(db.String(20), default='pending')
    # 'pending' | 'translated' | 'approved' | 'rejected'
    submitted_by        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow,
                                    onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':                 self.id,
            'subject':            self.subject,
            'original_message':   self.original_message,
            'source_language':    self.source_language,
            'translated_message': self.translated_message,
            'category':           self.category,
            'priority':           self.priority,
            'sentiment':          self.sentiment,
            'summary':            self.summary,
            'suggested_response': self.suggested_response,
            'status':             self.status,
            'created_at':         self.created_at.isoformat(),
        }


# ── Glossary ──────────────────────────────────────────────────────────────────
class GlossaryTerm(db.Model):
    __tablename__ = 'glossary'

    id          = db.Column(db.Integer, primary_key=True)
    term        = db.Column(db.String(200), nullable=False)
    translation = db.Column(db.String(200), nullable=False)
    language    = db.Column(db.String(50), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'term':        self.term,
            'translation': self.translation,
            'language':    self.language,
            'created_at':  self.created_at.isoformat(),
        }


# ── Seed & Init ───────────────────────────────────────────────────────────────
def init_db():
    """Create all tables. Seed one admin and one client account if empty."""
    db.create_all()

    if User.query.count() == 0:
        admin = User(email='admin@mtt.com', role='admin', name='Admin')
        admin.set_password('admin123')

        client = User(email='client@mtt.com', role='client', name='Test Client')
        client.set_password('client123')

        db.session.add_all([admin, client])
        db.session.commit()
        print('[DB] Seeded default admin (admin@mtt.com / admin123) '
              'and client (client@mtt.com / client123)')
