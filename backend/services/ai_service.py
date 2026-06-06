"""
AI Service — Gemini Integration
================================
Handles the full AI pipeline for a ticket:
  1. Language detection  (langdetect — offline)
  2. Translation         (MyMemory API — free, no key)
  3. Ticket analysis     (Gemini — category / priority / sentiment / summary / response)
"""

import os, re, json, requests
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

DetectorFactory.seed = 42

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
MYMEMORY_URL   = 'https://api.mymemory.translated.net/get'

if _GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ── Language name map ─────────────────────────────────────────────────────────
LANG_NAMES = {
    'ta': 'Tamil',      'hi': 'Hindi',      'en': 'English',
    'ml': 'Malayalam',  'te': 'Telugu',     'kn': 'Kannada',
    'bn': 'Bengali',    'mr': 'Marathi',    'gu': 'Gujarati',
    'pa': 'Punjabi',    'ur': 'Urdu',       'or': 'Odia',
    'fr': 'French',     'de': 'German',     'es': 'Spanish',
    'ar': 'Arabic',     'zh-cn': 'Chinese', 'ja': 'Japanese',
    'pt': 'Portuguese', 'ru': 'Russian',    'ko': 'Korean',
    'it': 'Italian',    'nl': 'Dutch',      'tr': 'Turkish',
}

# Unicode script → language fallback (for scripts langdetect struggles with)
_SCRIPT_MAP = [
    (r'[\u0B80-\u0BFF]', 'ta'),    # Tamil
    (r'[\u0900-\u097F]', 'hi'),    # Hindi / Devanagari (also Marathi)
    (r'[\u0D00-\u0D7F]', 'ml'),    # Malayalam
    (r'[\u0C00-\u0C7F]', 'te'),    # Telugu
    (r'[\u0C80-\u0CFF]', 'kn'),    # Kannada
    (r'[\u0980-\u09FF]', 'bn'),    # Bengali
    (r'[\u0A80-\u0AFF]', 'gu'),    # Gujarati
    (r'[\u0A00-\u0A7F]', 'pa'),    # Punjabi / Gurmukhi
    (r'[\u0B00-\u0B7F]', 'or'),    # Odia
    (r'[\u0600-\u06FF]', 'ur'),    # Urdu / Arabic script
    (r'[\u4E00-\u9FFF]', 'zh-cn'), # Chinese
    (r'[\u3040-\u30FF]', 'ja'),    # Japanese
    (r'[\uAC00-\uD7AF]', 'ko'),    # Korean
    (r'[\u0400-\u04FF]', 'ru'),    # Russian / Cyrillic
]


def detect_language(text: str) -> tuple[str, str]:
    """
    Returns (lang_code, lang_name).
    Tries Unicode script map first (instant), then langdetect.
    """
    for pattern, code in _SCRIPT_MAP:
        if re.search(pattern, text):
            return code, LANG_NAMES.get(code, code)
    try:
        code = detect(text)
        return code, LANG_NAMES.get(code, code.upper())
    except LangDetectException:
        return 'en', 'English'


def translate_to_english(text: str, source_lang: str) -> str:
    """Translates text to English using the free MyMemory API."""
    if source_lang.startswith('en'):
        return text
    try:
        resp = requests.get(MYMEMORY_URL, params={
            'q':        text,
            'langpair': f'{source_lang}|en',
        }, timeout=15)
        data = resp.json()
        translated = data.get('responseData', {}).get('translatedText', text)
        # Reject MyMemory quota warning strings
        if 'MYMEMORY WARNING' in translated.upper():
            return text
        return translated
    except Exception as e:
        print(f'[Translation] MyMemory failed: {e}')
        return text


def _call_gemini(prompt: str) -> str:
    """Calls Gemini gemini-1.5-flash and returns the text response."""
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={'temperature': 0.3, 'max_output_tokens': 1024},
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def _fallback_analysis(text: str) -> dict:
    """
    Rule-based fallback used when Gemini is not available.
    Keeps the app working without an API key.
    """
    text_lower = text.lower()

    # Category
    if any(w in text_lower for w in ['network', 'internet', 'wifi', 'connection', 'vpn']):
        category = 'Network Issue'
    elif any(w in text_lower for w in ['password', 'login', 'access', 'account', 'locked']):
        category = 'Account Issue'
    elif any(w in text_lower for w in ['bill', 'payment', 'invoice', 'charge']):
        category = 'Billing Issue'
    elif any(w in text_lower for w in ['software', 'app', 'crash', 'error', 'bug']):
        category = 'Software Issue'
    elif any(w in text_lower for w in ['hardware', 'device', 'printer', 'screen']):
        category = 'Hardware Issue'
    else:
        category = 'General Inquiry'

    # Priority
    if any(w in text_lower for w in ['urgent', 'critical', 'emergency', 'asap', 'immediately']):
        priority = 'Critical'
    elif any(w in text_lower for w in ['cannot', "can't", 'not working', 'blocked', 'down']):
        priority = 'High'
    elif any(w in text_lower for w in ['slow', 'issue', 'problem', 'help']):
        priority = 'Medium'
    else:
        priority = 'Low'

    # Sentiment
    if any(w in text_lower for w in ['angry', 'furious', 'terrible', 'worst', 'awful', 'frustrated']):
        sentiment = 'Very Negative'
    elif any(w in text_lower for w in ['problem', 'issue', 'cannot', 'failed', 'error']):
        sentiment = 'Negative'
    elif any(w in text_lower for w in ['thank', 'please', 'help', 'appreciate']):
        sentiment = 'Neutral'
    else:
        sentiment = 'Neutral'

    return {
        'category':          category,
        'priority':          priority,
        'sentiment':         sentiment,
        'summary':           f'Customer reports: {text[:120]}{"..." if len(text) > 120 else ""}',
        'suggested_response': (
            f'Thank you for reaching out. We have received your ticket regarding '
            f'"{category.lower()}" and will investigate immediately. '
            f'Our team will contact you within 24 hours.'
        ),
        'confidence':        75,
    }


def _parse_json_from_gemini(raw: str) -> dict:
    """Strip markdown fences and parse JSON from Gemini's response."""
    cleaned = re.sub(r'```(?:json)?', '', raw).replace('```', '').strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f'Cannot parse Gemini response: {raw[:200]}')


def analyze_with_gemini(english_text: str) -> dict:
    """
    Uses Gemini to analyse a translated English ticket.
    Falls back to rule-based analysis if Gemini is unavailable.
    """
    if not (_GEMINI_AVAILABLE and GEMINI_API_KEY):
        print('[AI] Gemini not configured — using rule-based fallback.')
        return _fallback_analysis(english_text)

    prompt = f"""You are an expert IT support AI analyst.
Analyze the following English customer support ticket and return ONLY a valid JSON object.

Ticket:
\"\"\"{english_text}\"\"\"

Return this exact JSON (no markdown, no extra text):
{{
  "category": "<Network Issue | Account Issue | Billing Issue | Software Issue | Hardware Issue | VPN Issue | Password Reset | General Inquiry | Other>",
  "priority": "<Low | Medium | High | Critical>",
  "sentiment": "<Positive | Neutral | Negative | Very Negative>",
  "summary": "<one sentence summary>",
  "suggested_response": "<professional 1-2 sentence reply to customer>",
  "confidence": <integer 0-100>
}}

Priority rules:
- Critical = service down, data loss, security breach
- High     = user completely blocked
- Medium   = degraded functionality
- Low      = general question
"""
    try:
        raw  = _call_gemini(prompt)
        data = _parse_json_from_gemini(raw)

        # Validate and normalise
        valid_categories = {
            'Network Issue', 'Account Issue', 'Billing Issue', 'Software Issue',
            'Hardware Issue', 'VPN Issue', 'Password Reset', 'General Inquiry', 'Other'
        }
        valid_priorities = {'Low', 'Medium', 'High', 'Critical'}
        valid_sentiments = {'Positive', 'Neutral', 'Negative', 'Very Negative'}

        return {
            'category':          data.get('category', 'Other') if data.get('category') in valid_categories else 'Other',
            'priority':          data.get('priority', 'Medium') if data.get('priority') in valid_priorities else 'Medium',
            'sentiment':         data.get('sentiment', 'Neutral') if data.get('sentiment') in valid_sentiments else 'Neutral',
            'summary':           str(data.get('summary', '')).strip(),
            'suggested_response': str(data.get('suggested_response', '')).strip(),
            'confidence':        int(data.get('confidence', 90)),
        }
    except Exception as e:
        print(f'[AI] Gemini analysis failed: {e} — using fallback.')
        return _fallback_analysis(english_text)


def process_ticket(subject: str, message: str, hint_language: str = None) -> dict:
    """
    Full pipeline:
      detect → translate → analyse → return structured result

    Args:
        subject:       Ticket subject line
        message:       Raw customer message (any language)
        hint_language: Optional language name from the dropdown (e.g. "French")

    Returns:
        Complete ticket analysis dict ready to store in DB and send to frontend.
    """
    # Step 1 — Language detection
    lang_code, lang_name = detect_language(message)

    # If frontend provided a language hint and detection gave 'en', trust the hint
    hint_map = {
        # Indian languages
        'Tamil':     'ta',
        'Hindi':     'hi',
        'Malayalam': 'ml',
        'Telugu':    'te',
        'Kannada':   'kn',
        'Bengali':   'bn',
        'Marathi':   'mr',
        'Gujarati':  'gu',
        'Punjabi':   'pa',
        'Urdu':      'ur',
        'Odia':      'or',
        # International
        'French':     'fr',
        'German':     'de',
        'Spanish':    'es',
        'Arabic':     'ar',
        'Chinese':    'zh-cn',
        'Japanese':   'ja',
        'Portuguese': 'pt',
        'Russian':    'ru',
        'Korean':     'ko',
        'Italian':    'it',
        'Turkish':    'tr',
    }
    if hint_language and hint_language != 'English' and lang_code == 'en':
        lang_code = hint_map.get(hint_language, lang_code)
        lang_name = hint_language

    # Step 2 — Translation
    english_text = translate_to_english(message, lang_code)

    # Step 3 — AI Analysis
    analysis = analyze_with_gemini(english_text)

    return {
        'subject':            subject,
        'source_language':    lang_code,
        'language_name':      lang_name,
        'original_message':   message,
        'translated_message': english_text,
        'category':           analysis['category'],
        'priority':           analysis['priority'],
        'sentiment':          analysis['sentiment'],
        'summary':            analysis['summary'],
        'suggested_response': analysis['suggested_response'],
        'confidence':         analysis.get('confidence', 90),
    }
