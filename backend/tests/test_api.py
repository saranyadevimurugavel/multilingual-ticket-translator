"""
Test Cases — Multilingual Ticket Translator
============================================
Covers the happy path for all major API endpoints.
Run with: pytest tests/ -v
"""
import json
from unittest.mock import patch

# ── Mock AI pipeline so tests don't need a real Gemini key ───────────────────
MOCK_PIPELINE = {
    'subject':            'Test ticket',
    'source_language':    'ta',
    'language_name':      'Tamil',
    'original_message':   'எனது இணையம் வேலை செய்யவில்லை',
    'translated_message': 'My internet is not working',
    'category':           'Network Issue',
    'priority':           'High',
    'sentiment':          'Negative',
    'summary':            'Customer reports internet issue.',
    'suggested_response': 'We are looking into this.',
    'confidence':         95,
}


# ── Test 1: Health check ──────────────────────────────────────────────────────
def test_health(client):
    """API must return 200 OK on /api/health"""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


# ── Test 2: Register new client ───────────────────────────────────────────────
def test_register_client(client):
    """Client can register with name, email, password"""
    resp = client.post('/api/auth/register', json={
        'name':     'Test User',
        'email':    'test@example.com',
        'password': 'password123',
        'role':     'client',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['success'] is True
    assert 'token' in data
    assert data['user']['role'] == 'client'


# ── Test 3: Login with registered credentials ─────────────────────────────────
def test_login(client):
    """Registered user can login and receive a JWT"""
    # Register first
    client.post('/api/auth/register', json={
        'name': 'Login User', 'email': 'login@test.com',
        'password': 'pass1234', 'role': 'client',
    })
    # Then login
    resp = client.post('/api/auth/login', json={
        'email': 'login@test.com', 'password': 'pass1234'
    })
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert 'token' in resp.get_json()


# ── Test 4: Wrong password returns 401 ───────────────────────────────────────
def test_login_wrong_password(client):
    """Wrong credentials must return 401"""
    resp = client.post('/api/auth/login', json={
        'email': 'nobody@test.com', 'password': 'wrongpass'
    })
    assert resp.status_code == 401
    assert resp.get_json()['success'] is False


# ── Test 5: Duplicate email returns 409 ──────────────────────────────────────
def test_register_duplicate_email(client):
    """Registering with an existing email must return 409"""
    payload = {'name':'A','email':'dup@test.com','password':'pass123','role':'client'}
    client.post('/api/auth/register', json=payload)
    resp = client.post('/api/auth/register', json=payload)
    assert resp.status_code == 409


# ── Test 6: Submit ticket (AI mocked) ────────────────────────────────────────
def test_submit_ticket(client):
    """Ticket submission returns translated + analysed result"""
    with patch('routes.ticket_routes.process_ticket', return_value=MOCK_PIPELINE):
        resp = client.post('/api/tickets/submit', json={
            'subject':  'Internet not working',
            'language': 'Tamil',
            'message':  'எனது இணையம் வேலை செய்யவில்லை',
        })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['success'] is True
    assert data['ticket']['translated_message'] == 'My internet is not working'
    assert data['ticket']['category'] == 'Network Issue'


# ── Test 7: Submit ticket without message returns 400 ────────────────────────
def test_submit_ticket_missing_message(client):
    """Missing message field must return 400"""
    resp = client.post('/api/tickets/submit', json={'subject': 'Hello'})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


# ── Test 8: Supported languages endpoint ─────────────────────────────────────
def test_supported_languages(client):
    """GET /api/tickets/pending returns success (even if no tickets)"""
    # Register + login as admin to access this endpoint
    client.post('/api/auth/register', json={
        'name':'Admin','email':'adm@test.com',
        'password':'admin123','role':'admin'
    })
    login = client.post('/api/auth/login', json={
        'email':'adm@test.com','password':'admin123'
    })
    token = login.get_json()['token']

    resp = client.get('/api/tickets/pending',
                      headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


# ── Test 9: Admin dashboard stats ────────────────────────────────────────────
def test_dashboard_stats(client):
    """Admin can access dashboard stats"""
    client.post('/api/auth/register', json={
        'name':'Admin2','email':'adm2@test.com',
        'password':'admin123','role':'admin'
    })
    login = client.post('/api/auth/login', json={
        'email':'adm2@test.com','password':'admin123'
    })
    token = login.get_json()['token']

    resp = client.get('/api/dashboard/stats',
                      headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'total_tickets' in data['stats']


# ── Test 10: Glossary add and list ───────────────────────────────────────────
def test_glossary(client):
    """Admin can add and retrieve glossary terms"""
    client.post('/api/auth/register', json={
        'name':'Admin3','email':'adm3@test.com',
        'password':'admin123','role':'admin'
    })
    login = client.post('/api/auth/login', json={
        'email':'adm3@test.com','password':'admin123'
    })
    token = login.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # Add term
    add = client.post('/api/glossary/add',
                      json={'term':'VPN','translation':'வி.பி.என்','language':'ta'},
                      headers=headers)
    assert add.status_code == 201
    assert add.get_json()['term']['term'] == 'VPN'

    # List terms
    lst = client.get('/api/glossary', headers=headers)
    assert lst.status_code == 200
    assert lst.get_json()['total'] >= 1
