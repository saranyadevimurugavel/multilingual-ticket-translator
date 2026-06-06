"""
Batch Processing Service
========================
Reads a folder of mixed-language ticket files (.txt or .json),
processes each through the full AI pipeline, and stores:
  - original message (customer's language)
  - detected language
  - English translation
  - AI category, priority, sentiment, summary, suggested response

Supported file formats:
  .txt  — plain text, optionally with SUBJECT: / LANGUAGE: header lines
  .json — { "subject": "...", "language": "...", "message": "..." }

Reply translation:
  When an engineer submits a reply in English, this service translates
  it back to the ticket's original language and stores both versions.
"""

import os
import json
from pathlib import Path

from database import db, Ticket
from services.ai_service import process_ticket, translate_to_english


# ── File parsers ──────────────────────────────────────────────────────────────

def _parse_txt(filepath: str) -> dict:
    """
    Parses a .txt ticket file.
    Supports optional header lines:
        SUBJECT: ...
        LANGUAGE: ...
    Everything after the headers is the message body.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    subject  = Path(filepath).stem   # default = filename
    language = None
    lines    = content.splitlines()
    body_lines = []
    in_headers = True

    for line in lines:
        stripped = line.strip()
        if in_headers and stripped.upper().startswith('SUBJECT:'):
            subject = stripped[8:].strip()
        elif in_headers and stripped.upper().startswith('LANGUAGE:'):
            language = stripped[9:].strip()
        elif in_headers and stripped == '':
            in_headers = False   # blank line ends header block
        else:
            in_headers = False
            body_lines.append(line)

    message = '\n'.join(body_lines).strip() or content

    return {'subject': subject, 'language': language, 'message': message}


def _parse_json(filepath: str) -> dict:
    """Parses a .json ticket file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        'subject':  data.get('subject', Path(filepath).stem),
        'language': data.get('language'),
        'message':  data.get('message', ''),
    }


def _parse_file(filepath: str) -> dict | None:
    """Routes to the correct parser based on file extension."""
    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.txt':
            return _parse_txt(filepath)
        elif ext == '.json':
            return _parse_json(filepath)
        else:
            return None   # unsupported format — skip silently
    except Exception as e:
        print(f'[Batch] Parse error for {filepath}: {e}')
        return None


# ── Main batch processor ──────────────────────────────────────────────────────

def process_folder(folder_path: str) -> dict:
    """
    Scans `folder_path` for .txt and .json ticket files,
    runs each through the AI pipeline, and saves to the database.

    Args:
        folder_path: Absolute or relative path to the tickets folder.

    Returns:
        {
          "total":     8,
          "processed": 7,
          "skipped":   1,
          "results": [ { ticket dict }, ... ],
          "errors":  [ { "file": "...", "error": "..." }, ... ]
        }
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f'Folder not found: {folder_path}')

    # Collect all supported files
    files = sorted(
        [f for f in folder.iterdir()
         if f.is_file() and f.suffix.lower() in ('.txt', '.json')]
    )

    results = []
    errors  = []

    for file in files:
        print(f'[Batch] Processing {file.name}…')

        # 1. Parse the file
        parsed = _parse_file(str(file))
        if not parsed or not parsed.get('message'):
            errors.append({'file': file.name, 'error': 'Could not parse or empty message'})
            continue

        try:
            # 2. Run full AI pipeline (detect → translate → analyse)
            result = process_ticket(
                subject       = parsed['subject'],
                message       = parsed['message'],
                hint_language = parsed.get('language'),
            )

            # 3. Store in database
            ticket = Ticket(
                subject            = result['subject'] if 'subject' in result else parsed['subject'],
                original_message   = result['original_message'],
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

            results.append({
                'file':              file.name,
                'ticket_id':         ticket.id,
                'subject':           parsed['subject'],
                'source_language':   result['source_language'],
                'language_name':     result['language_name'],
                'translated_message': result['translated_message'],
                'category':          result['category'],
                'priority':          result['priority'],
                'sentiment':         result['sentiment'],
                'summary':           result['summary'],
                'suggested_response': result['suggested_response'],
                'status':            'processed',
            })

            print(f'[Batch] ✓ {file.name} → #{ticket.id} ({result["language_name"]})')

        except Exception as e:
            db.session.rollback()
            errors.append({'file': file.name, 'error': str(e)})
            print(f'[Batch] ✗ {file.name} error: {e}')

    return {
        'total':     len(files),
        'processed': len(results),
        'skipped':   len(errors),
        'results':   results,
        'errors':    errors,
    }


# ── Reply translation ─────────────────────────────────────────────────────────

def translate_reply(ticket_id: int, english_reply: str) -> dict:
    """
    Takes an engineer's English reply, translates it back to the
    ticket's original language, and stores both versions on the ticket.

    Args:
        ticket_id:     ID of the ticket being replied to.
        english_reply: The engineer's reply written in English.

    Returns:
        {
          "ticket_id":        3,
          "english_reply":    "We have resolved the issue...",
          "translated_reply": "நாங்கள் சிக்கலை தீர்த்துள்ளோம்...",
          "target_language":  "ta",
          "language_name":    "Tamil"
        }
    """
    from services.ai_service import LANG_NAMES

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise ValueError(f'Ticket #{ticket_id} not found')

    target_lang = ticket.source_language
    lang_name   = LANG_NAMES.get(target_lang, target_lang.upper())

    # Translate English reply → original language
    if target_lang and target_lang != 'en' and target_lang != 'unknown':
        translated_reply = _translate_from_english(english_reply, target_lang)
    else:
        translated_reply = english_reply   # already English

    # Store both versions in the suggested_response field
    # (In a full system this would go to a Reply table)
    ticket.suggested_response = (
        f"[English]\n{english_reply}\n\n"
        f"[{lang_name}]\n{translated_reply}"
    )
    ticket.status = 'approved'
    db.session.commit()

    return {
        'ticket_id':        ticket_id,
        'english_reply':    english_reply,
        'translated_reply': translated_reply,
        'target_language':  target_lang,
        'language_name':    lang_name,
    }


def _translate_from_english(text: str, target_lang: str) -> str:
    """Translates English text to target_lang using MyMemory API."""
    import requests as req
    try:
        resp = req.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': f'en|{target_lang}'},
            timeout=15,
        )
        data = resp.json()
        translated = data.get('responseData', {}).get('translatedText', text)
        if 'MYMEMORY WARNING' in translated.upper():
            return text
        return translated
    except Exception as e:
        print(f'[Reply Translation] Failed: {e}')
        return text
