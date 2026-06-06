# AI Usage Note — Multilingual Ticket Translator

## Overview

This project uses **Google Gemini AI (gemini-1.5-flash)** as the core AI engine.
The free tier provides sufficient quota for development, testing, and demonstration.

---

## How AI Is Used

### 1. Translation (External API Integration)

**Service**: `backend/services/translation_service.py`
**Capability Demonstrated**: External API Integration

The `translate_to_english()` function sends a carefully crafted prompt to Gemini:

```
Translate the following [Tamil] customer support ticket into English.
Return ONLY the translated text — no explanations, no quotation marks.

[Tamil text]

English translation:
```

**Why Gemini for translation?**
- Accurate for low-resource languages (Tamil, Hindi) where open-source models often struggle
- Single API for both translation and analysis reduces complexity
- Free tier covers hundreds of ticket translations per day

---

### 2. Ticket Analysis — AI Agent Loop

**Service**: `backend/services/analysis_service.py`
**Capability Demonstrated**: AI Agent Loop

The `analyze_ticket()` function implements an AI Agent workflow:

```
Receive English text
    → Build structured prompt (build_analysis_prompt)
    → Call Gemini (call_gemini)
    → Parse JSON response (parse_gemini_json)
    → Validate & normalise (validate_and_normalise)
    → Return structured output
```

The prompt instructs Gemini to return strict JSON with six fields:

```json
{
  "category": "...",
  "priority": "...",
  "summary": "...",
  "sentiment": "...",
  "response": "...",
  "keywords": [...]
}
```

Priority rules are embedded in the prompt:
- **Critical**: data loss, security breach, service outage
- **High**: customer is completely blocked
- **Medium**: degraded functionality
- **Low**: general questions

---

### 3. Language Detection (Offline — No AI API)

**Library**: `langdetect` (Python)
**No API Key Required**

Language detection uses the offline `langdetect` library (port of Google's language-detection library).
This conserves Gemini API quota — detection happens locally with zero latency and no cost.

---

## Prompt Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| Low temperature (0.3) | Consistent, deterministic structured output |
| Strict JSON schema in prompt | Reduces hallucination and format drift |
| Explicit allowed values | e.g., `priority` must be one of Low/Medium/High/Critical |
| Fallback parser | Strips markdown fences from responses when Gemini wraps JSON in ` ```json ` |
| Validation layer | Never trusts AI output directly — normalises to safe defaults |

---

## API Key & Quota

- **Model**: `gemini-1.5-flash`
- **Free tier**: 15 requests per minute, 1 million tokens per day
- **Get your key**: https://aistudio.google.com/app/apikey
- **Key storage**: `.env` file (never committed to git — listed in `.gitignore`)

---

## AI-Assisted Development

Parts of this project were developed with AI coding assistance:
- Boilerplate Flask application factory structure
- Prompt engineering iteration for structured output
- Test case scaffolding

All AI-generated code was reviewed, understood, and modified by the developer.

---

## Ethical Considerations

- Customer support tickets may contain personal data — in production, implement data minimisation and obtain consent before sending to third-party AI APIs
- Gemini's safety filters are configured to BLOCK_ONLY_HIGH to avoid false positives on frustrated customer language
- Translation is used to assist agents, not replace human judgment — sensitive cases should be reviewed by a human
