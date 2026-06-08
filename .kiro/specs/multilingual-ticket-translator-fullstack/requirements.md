# Requirements Document

## Introduction

The Multilingual Ticket Translator (MTT) is a full-stack customer support platform that accepts support tickets written in any language, automatically detects the language, translates the content to English for support agents, uses AI to analyse and categorise the ticket, and translates agent replies back into the customer's original language. The system serves two distinct user roles — clients (customers who submit tickets) and admins/agents (support staff who review, approve, and respond to tickets). The platform consists of a vanilla JS frontend, a Python/Flask backend with AI-powered analysis, and a Node.js/Express backend with a translation audit log.

---

## Glossary

- **System**: The complete Multilingual Ticket Translator application (frontend + backend).
- **Client**: A registered end-user who submits support tickets.
- **Admin**: A privileged user who reviews, approves, rejects, and responds to tickets.
- **Agent**: Synonym for Admin in the Node.js backend context.
- **Ticket**: A customer support request containing a subject line and a message body in any supported language.
- **Translation_Service**: The MyMemory API integration that translates text between languages.
- **AI_Service**: The Google Gemini API integration (with rule-based fallback) that analyses translated tickets.
- **Language_Detector**: The component that identifies the language of incoming ticket text (offline Unicode script check + langdetect library + MyMemory detect endpoint).
- **JWT**: JSON Web Token used for stateless authentication.
- **BCP-47**: The language code standard used throughout the system (e.g., `en`, `fr`, `ta`, `zh-cn`).
- **Glossary**: The admin-managed dictionary of domain-specific terms and their translations.
- **Batch_Processor**: The service that processes multiple ticket files from a folder in a single operation.
- **Translation_Log**: The audit trail that records every translation performed by the system.
- **Source_Language**: The BCP-47 code of the language in which a ticket was originally written.
- **Target_Language**: The BCP-47 code of the language into which a reply is translated before delivery.
- **Confidence_Score**: An integer (0–100) representing the AI's self-assessed accuracy of its analysis.
- **Priority**: The urgency classification of a ticket (Low, Medium, High, or Critical).
- **Sentiment**: The emotional tone of the ticket (Positive, Neutral, Negative, or Very Negative).
- **Category**: The support domain of a ticket (e.g., Network Issue, Account Issue, Billing Issue).

---

## Requirements

### Requirement 1: User Registration

**User Story:** As a new user, I want to register an account with my email and password, so that I can access the platform.

#### Acceptance Criteria

1. WHEN a registration request is received with a valid name, email, and password, THE System SHALL create a new user account and return a JWT and user profile; IF password hashing fails for any reason, THEN THE System SHALL reject account creation and return HTTP 500.
2. WHEN a registration request is received with an email that is already registered, THE System SHALL return HTTP 409 with the message "Email already registered".
3. IF a registration request is received with a missing email or password, THEN THE System SHALL return HTTP 400 with a descriptive validation error.
4. THE System SHALL store passwords as bcrypt hashes with a salt factor of at least 10; it SHALL NOT store plaintext passwords.
5. WHEN a user account is created without an explicit role, THE System SHALL assign the default role of "client" (Python backend) or "agent" (Node.js backend).
6. THE System SHALL enforce that name values are between 1 and 100 characters and that email values conform to standard email format; IF name validation fails, THEN THE System SHALL return HTTP 400 and SHALL NOT create the account.

---

### Requirement 2: User Authentication

**User Story:** As a registered user, I want to log in with my email and password, so that I can receive a JWT to access protected endpoints.

#### Acceptance Criteria

1. WHEN a login request is received with a valid email and matching password, THE System SHALL return HTTP 200 with a JWT and the user profile (id, name, email, role).
2. WHEN a login request is received with an invalid email or an incorrect password, THE System SHALL return HTTP 401 with the message "Invalid email or password".
3. THE System SHALL sign JWTs using the configured secret key and set an expiry of 7 days (Node.js backend) or 24 hours (Python backend).
4. WHEN a protected endpoint is accessed with a missing Authorization header, THE System SHALL return HTTP 401 with the message "Authentication required".
5. WHEN a protected endpoint is accessed with an expired JWT, THE System SHALL return HTTP 401 with the message "Token expired".
6. WHEN a protected endpoint is accessed with a malformed or invalid JWT, THE System SHALL return HTTP 401 with the message "Invalid token".
7. WHEN an admin-only endpoint is accessed by a user with a non-admin role, THE System SHALL return HTTP 403 with a descriptive authorization error.

---

### Requirement 3: Ticket Submission with Automatic Language Detection and Translation

**User Story:** As a client, I want to submit a support ticket in my native language, so that the system automatically translates it and makes it readable for English-speaking agents.

#### Acceptance Criteria

1. WHEN a ticket submission is received with a subject and a message body, THE System SHALL run the full pipeline: language detection → translation → AI analysis → persistence.
2. WHEN the Language_Detector receives text containing Unicode characters in a known script range, THE Language_Detector SHALL identify the language using the offline script map before making any network call.
3. WHEN the offline script map cannot identify the language, THE Language_Detector SHALL query the MyMemory detect endpoint or the langdetect library to determine the BCP-47 language code.
4. IF language detection fails for any reason, THEN THE Language_Detector SHALL default to "en" and SHALL NOT propagate the failure to the ticket creation flow.
5. WHEN the detected language is not English, THE Translation_Service SHALL translate the original message to English using the MyMemory API and store both the original and translated text.
6. WHEN the detected language is English, THE Translation_Service SHALL skip the translation API call and store the original text as both the original and translated message.
7. WHEN the MyMemory API returns a quota warning response (HTTP 429 or body containing "MYMEMORY WARNING"), THE Translation_Service SHALL log the warning and return the original untranslated text; it SHALL NOT return an error to the caller.
8. IF the Translation_Service call fails due to a network error or timeout, THEN THE Translation_Service SHALL return the original text and SHALL NOT cause the ticket creation request to fail.
9. THE System SHALL complete language detection before persisting the ticket record; IF language detection returns a valid BCP-47 code, THEN THE System SHALL persist the ticket containing: subject/title, customer name, original message, BCP-47 source language, translated English message, and initial status "pending" (Python) or "open" (Node.js).
10. WHEN a client submits a ticket via the frontend form, THE System SHALL return the full AI analysis result including translated message, category, priority, sentiment, summary, suggested response, and confidence score.
11. THE System SHALL NOT require clients to provide a language hint; IF no language is provided in the request, THEN THE System SHALL rely entirely on automatic language detection from the message body.

---

### Requirement 4: AI-Powered Ticket Analysis

**User Story:** As an admin, I want every incoming ticket to be automatically categorised, prioritised, and summarised by AI, so that I can triage issues quickly without reading each ticket in full.

#### Acceptance Criteria

1. WHEN a translated English ticket message is available, THE AI_Service SHALL analyse it and return: category, priority, sentiment, one-sentence summary, suggested agent response, and a confidence score.
2. THE AI_Service SHALL classify tickets into exactly one of the following categories: Network Issue, Account Issue, Billing Issue, Software Issue, Hardware Issue, VPN Issue, Password Reset, General Inquiry, Other.
3. THE AI_Service SHALL assign one of four priority levels using the following rules: Critical = service down / data loss / security breach; High = user completely blocked; Medium = degraded functionality; Low = general question.
4. THE AI_Service SHALL assign one of four sentiment values: Positive, Neutral, Negative, Very Negative.
5. WHEN the Gemini API key is properly configured and the API call succeeds, THE AI_Service SHALL use the Gemini API results and SHALL NOT invoke the rule-based fallback.
6. WHEN the Gemini API is unreachable, returns an error, or returns an unparseable response, THE AI_Service SHALL fall back to the rule-based analyser; IF both Gemini and the rule-based analyser fail, THEN THE System SHALL return an error for the ticket creation request.
7. THE AI_Service SHALL validate all fields returned by Gemini; if any field contains a value outside the defined enumeration, THE AI_Service SHALL replace that field with its safe default (category → "Other", priority → "Medium", sentiment → "Neutral").
8. WHERE a language hint is provided in the ticket submission by an admin or batch processor and the Language_Detector returns "en", THE System SHALL trust the provided hint and override the detected language code; for client-submitted tickets with no language hint, THE System SHALL rely solely on automatic detection.

---

### Requirement 5: Translation Center — Translation Review and Approval

**User Story:** As an admin, I want to review automatically translated tickets, approve or reject translation quality, and send replies that are automatically translated back to the customer's language, so that accurate translations reach customers in their native language.

#### Acceptance Criteria

1. WHEN an admin requests the next pending ticket, THE System SHALL return the oldest ticket with status "pending", including its original message, translated message, source language, AI analysis fields (category, priority, sentiment, summary, suggested response), and confidence score.
2. IF there are no pending tickets, THEN THE System SHALL return HTTP 200 with a null ticket field; the frontend SHALL display an empty state message.
3. WHEN an admin approves a ticket, THE System SHALL update its status to "approved" and return HTTP 200 with the updated status; the frontend SHALL automatically load the next pending ticket.
4. WHEN an admin rejects a ticket, THE System SHALL update its status to "rejected" and return HTTP 200 with the updated status; the frontend SHALL automatically load the next pending ticket.
5. THE System SHALL restrict the approve and reject endpoints to admin-role users only.
6. WHEN an admin submits an English reply for a pending ticket via the Translation Center, THE System SHALL call `POST /api/batch/reply` with the ticket ID and English reply text, translate the reply into the ticket's source language, persist both versions, and return the translated reply for display.
7. WHEN the Translation Center page loads, IF the user is not authenticated, THEN THE System SHALL redirect to the admin login page.
8. IF a ticket being approved or rejected no longer exists, THEN THE System SHALL return HTTP 404 with a descriptive error.

---

### Requirement 6: Ticket Listing, Filtering, and Pagination

**User Story:** As an admin, I want to view and filter all tickets by status and language with pagination, so that I can manage large volumes of support requests efficiently.

#### Acceptance Criteria

1. WHEN an authenticated user requests the ticket list, THE System SHALL return paginated results ordered by creation date descending, with a default page size of 20.
2. WHEN a status filter is provided as a query parameter, THE System SHALL return only tickets matching that status value.
3. WHEN a language filter is provided as a query parameter, THE System SHALL return only tickets whose source language matches the given BCP-47 code.
4. THE System SHALL include pagination metadata in every list response: total count, current page number, page size, and total page count.
5. WHEN an admin requests a single ticket by ID, THE System SHALL return the full ticket record including the assigned agent profile; the System MAY return HTTP 404 if the ticket has been soft-deleted or if access control rules prevent access.
6. IF a requested ticket ID does not exist in the database, THEN THE System SHALL return HTTP 404 with the message "Ticket not found".

---

### Requirement 7: Ticket Status Management and Assignment

**User Story:** As an admin or agent, I want to update a ticket's status and assign it to an agent, so that the support workflow progresses from open through in-progress to closed.

#### Acceptance Criteria

1. WHEN an authenticated user updates a ticket, THE System SHALL allow changes to the "status", "assignedTo", and "title" fields only; other fields SHALL be ignored.
2. THE System SHALL accept the following status values for the Node.js backend: "open", "in_progress", "closed".
3. WHEN an agent submits a reply to an "open" ticket, THE System SHALL automatically transition the ticket status to "in_progress" and set the assignedTo field to the replying agent's ID.
4. THE System SHALL restrict ticket deletion to admin-role users only.
5. IF an update request targets a non-existent ticket ID, THEN THE System SHALL return HTTP 404 with the message "Ticket not found".

---

### Requirement 8: Agent Reply with Reverse Translation

**User Story:** As an agent, I want to write my reply in English and have it automatically translated into the customer's original language, so that the customer receives a response they can understand.

#### Acceptance Criteria

1. WHEN an agent submits an English reply for a ticket, THE System SHALL translate the reply from English into the ticket's source language using the Translation_Service.
2. WHEN the ticket's source language is English or "unknown", THE System SHALL skip the translation step and store the English reply as both the English and translated reply, setting the target language equal to the source language.
3. THE System SHALL persist the reply record containing: ticket ID, agent ID, English reply, translated reply, and BCP-47 target language.
4. THE System SHALL return the persisted reply including the agent's profile in the response.
5. IF the target ticket does not exist, THEN THE System SHALL return HTTP 404 with the message "Ticket not found".

---

### Requirement 9: Arbitrary Text Translation Endpoint

**User Story:** As an authenticated user, I want to translate arbitrary text between any two supported languages, so that I can verify translations or translate content outside of the ticket workflow.

#### Acceptance Criteria

1. WHEN a translate request is received with text, a source language, and a target language, THE Translation_Service SHALL return the translated text along with the resolved source and target language codes.
2. WHEN a translate request is received with sourceLang set to "auto" or omitted, THE System SHALL first detect the language and then translate to English.
3. WHEN the source and target language codes are identical — including when auto-detection resolves to the same code as the target — THE Translation_Service SHALL return the original text without making an API call.
4. IF the translate request omits the text field or provides an empty string, THEN THE System SHALL return HTTP 422 with a validation error.

---

### Requirement 10: Translation Audit Log

**User Story:** As an admin, I want to view a log of every translation the system has performed, so that I can audit translation quality and track API usage.

#### Acceptance Criteria

1. THE System SHALL record a Translation_Log entry for every successful translation, capturing: source language, target language, original text, translated text, and the associated ticket ID (if applicable).
2. WHEN an admin requests the translation history, THE System SHALL return paginated log entries ordered by creation timestamp descending.
3. THE System SHALL restrict the translation history endpoint to admin-role users only.
4. THE System SHALL persist Translation_Log records asynchronously so that a logging failure does not cause the parent translation request to fail.

---

### Requirement 11: Admin Dashboard Statistics

**User Story:** As an admin, I want to view aggregate statistics on my dashboard, so that I can monitor the overall health and volume of the support queue.

#### Acceptance Criteria

1. WHEN an admin requests dashboard statistics, THE System SHALL return: total ticket count, count of tickets by each status, count of tickets translated today, total number of replies, total number of translations performed, total user count, ticket distribution by source language, and the five most recently created tickets.
2. THE System SHALL restrict the dashboard statistics endpoint to admin-role users only.
3. THE System SHALL compute all statistics in a single request without requiring multiple API calls from the client.
4. THE Python backend dashboard SHALL additionally return ticket breakdown by priority and glossary term count.

---

### Requirement 12: Glossary Management

**User Story:** As an admin, I want to manage a glossary of domain-specific terms and their translations, so that I can maintain consistency across technical terminology in translated tickets.

#### Acceptance Criteria

1. WHEN an admin creates a glossary term with a source term, a translation, and an optional language code, THE System SHALL persist the term and return the created record with HTTP 201.
2. WHEN an admin requests the glossary list, THE System SHALL return all terms ordered alphabetically by the source term, along with the total count.
3. WHEN a search query parameter is provided, THE System SHALL return only terms where the source term or translation contains the search string (case-insensitive).
4. WHEN an admin updates a glossary term, THE System SHALL apply changes to any combination of term, translation, and language fields and return the updated record.
5. WHEN an admin deletes a glossary term by ID, THE System SHALL remove the record and return HTTP 200 with the message "Term deleted".
6. IF a requested glossary term ID does not exist, THEN THE System SHALL return HTTP 404.
7. THE System SHALL restrict all glossary write operations (create, update, delete) to admin-role users only.

---

### Requirement 13: Batch Ticket Processing

**User Story:** As an admin, I want to process a folder of ticket files in bulk, so that I can import historical or offline tickets into the system without submitting them one by one.

#### Acceptance Criteria

1. WHEN an admin triggers batch processing with a valid folder path, THE Batch_Processor SHALL scan the folder for `.txt` and `.json` files and process each through the full AI pipeline.
2. THE Batch_Processor SHALL parse `.txt` files by extracting optional `SUBJECT:` and `LANGUAGE:` header lines followed by the message body.
3. THE Batch_Processor SHALL parse `.json` files by reading the `subject`, `language`, and `message` fields.
4. WHEN a file cannot be parsed or has an empty message, THE Batch_Processor SHALL record it in the errors list and continue processing remaining files; it SHALL NOT abort the entire batch.
5. WHEN batch processing completes, THE System SHALL return a summary containing total files found, count of successfully processed files, count of skipped files, results for each processed ticket, and errors for each skipped file.
6. IF the specified folder path does not exist or is not a directory, THEN THE System SHALL return HTTP 400 with a descriptive error message.
7. THE System SHALL restrict batch processing endpoints to admin-role users only.
8. WHEN no folder path is provided in the batch request, THE Batch_Processor SHALL default to processing the built-in `sample_tickets/` folder.
9. WHEN an admin replies to a batch-processed ticket via `POST /api/batch/reply`, THE System SHALL translate the English reply into the ticket's source language and return both the English and translated reply text.

---

### Requirement 21: Admin Ticket History Page

**User Story:** As an admin, I want to view a paginated, filterable list of all tickets with their full details, so that I can review past translations, approve or reject individual tickets, and track the overall translation queue.

#### Acceptance Criteria

1. WHEN an admin loads the history page, THE System SHALL fetch paginated tickets from `GET /api/tickets/history` and render them in a table showing: ticket ID, subject, source language, category, priority, sentiment, status, and creation date.
2. WHEN an admin applies a status filter (pending, approved, rejected), THE System SHALL re-fetch tickets matching that status and update the table without a page reload.
3. WHEN an admin applies a language filter, THE System SHALL re-fetch tickets matching that BCP-47 code and update the table.
4. WHEN an admin clicks a ticket row, THE System SHALL display the full ticket details including original message, English translation, AI analysis, and current status.
5. WHEN an admin clicks "Approve Translation" on a ticket in the history view, THE System SHALL call `POST /api/tickets/<id>/approve` and update the displayed status without a full page reload.
6. WHEN an admin clicks "Reject" on a ticket in the history view, THE System SHALL call `POST /api/tickets/<id>/reject` and update the displayed status without a full page reload.
7. WHEN the history page loads, IF the user is not authenticated, THEN THE System SHALL redirect to the admin login page.
8. THE System SHALL display pagination controls when the total ticket count exceeds the page size, allowing the admin to navigate between pages.

---

### Requirement 14: Frontend Session Management

**User Story:** As a user, I want my session to persist across page refreshes without re-logging in, so that I do not lose my work when navigating between pages.

#### Acceptance Criteria

1. WHEN a user successfully logs in, THE System SHALL store the JWT and user profile object in localStorage under the keys `mtt_token` and `mtt_user`.
2. WHEN any frontend page loads, THE System SHALL read the stored token and user object from localStorage to restore the session without an additional network request.
3. WHEN a user clicks logout, THE System SHALL clear the `mtt_token` and `mtt_user` keys from localStorage and redirect to the home page.
4. WHEN an unauthenticated user attempts to access any admin page (dashboard, translation center, history, glossary, batch), THE System SHALL redirect to the admin login page.
5. THE System SHALL include the stored JWT as a `Bearer` token in the `Authorization` header of every API request made from the frontend.
6. WHEN a client logs in on the client login portal, THE System SHALL verify that the returned role is "client"; IF the role is not "client", THE System SHALL reject the session and show an error without revealing that an account with a different role exists.
7. WHEN an admin logs in on the admin login portal, THE System SHALL verify that the returned role is "admin"; IF the role is not "admin", THE System SHALL reject the session and show a generic error message.

---

### Requirement 15: Frontend Ticket Submission Form

**User Story:** As a client, I want to submit my support ticket by typing my subject and message in my own language without having to manually select a language, so that I can communicate my issue to the support team without needing to know language names or codes.

#### Acceptance Criteria

1. WHEN a client submits a ticket via the submit-ticket form, THE System SHALL send only the subject and message to the `/api/tickets/submit` endpoint; THE System SHALL NOT require the client to select or provide a language.
2. THE System SHALL remove the language selection dropdown from the client-facing submission form; the form SHALL contain only a subject field and a message textarea.
3. THE System SHALL automatically detect the language from the submitted message content on the backend; the detected language SHALL be returned in the response and displayed to the client.
4. IF the subject or message field is empty at submission time, THEN THE System SHALL display an error alert and SHALL NOT send the API request.
5. WHEN the API returns a successful ticket response, THE System SHALL render an AI analysis result card below the form displaying: ticket ID, detected language, category, priority, sentiment, confidence score, English translation, summary, and suggested response.
6. WHEN the API returns a successful ticket response, THE System SHALL reset the subject and message input fields.
7. WHEN the API call is in progress, THE System SHALL disable the submit button and display a loading indicator.
8. IF the API call fails, THEN THE System SHALL display an error alert with the server's error message.

---

### Requirement 16: Supported Languages

**User Story:** As a user submitting a ticket in any language, I want the system to recognise and translate my language, so that my ticket is understood by the support team.

#### Acceptance Criteria

1. THE Language_Detector SHALL support detection of the following languages: Tamil, Hindi, Malayalam, Telugu, Kannada, Bengali, Marathi, Gujarati, Punjabi, Urdu, Odia, French, German, Spanish, Arabic, Chinese (Simplified), Japanese, Korean, Portuguese, Russian, Italian, Turkish, and English.
2. THE Translation_Service SHALL support translation between any two of the languages listed in criterion 1.
3. WHEN the detected source language is one of the Indian script languages (Tamil, Hindi, Malayalam, Telugu, Kannada, Bengali, Gujarati, Punjabi, Odia), THE Language_Detector SHALL use the offline Unicode script map for detection before attempting any network call.
4. THE System SHALL represent all language identifiers using BCP-47 codes internally and SHALL map them to human-readable language names for all user-facing displays.

---

### Requirement 17: Error Handling and System Resilience

**User Story:** As a user, I want the system to handle errors gracefully and continue operating even when external services are unavailable, so that I can still submit and manage tickets.

#### Acceptance Criteria

1. WHEN any unhandled exception occurs during request processing, THE System SHALL return HTTP 500 with a generic error message and SHALL NOT expose internal stack traces or implementation details to the client.
2. WHEN a requested resource is not found (non-existent route), THE System SHALL return HTTP 404.
3. WHEN the Gemini API is unreachable, returns an error, or returns an unparseable response, THE AI_Service SHALL fall back to the rule-based analyser; IF both the Gemini API and the rule-based analyser are unavailable, THEN THE System SHALL return HTTP 500 for the ticket creation request.
4. WHEN the MyMemory Translation API is unreachable or returns a quota-exceeded response, THE Translation_Service SHALL return the original untranslated text and SHALL NOT cause the ticket creation request to fail.
5. WHEN a database write operation fails during batch processing, THE Batch_Processor SHALL roll back the failed transaction, record the error for that file, and continue processing the remaining files.
6. THE System SHALL return structured JSON error responses for all error conditions, including a `success: false` field and a descriptive `error` or `message` field.

---

### Requirement 18: API Design and Cross-Origin Resource Sharing

**User Story:** As a frontend developer, I want the backend API to accept requests from approved origins and return consistent JSON responses, so that the frontend can reliably integrate with the backend.

#### Acceptance Criteria

1. THE System SHALL accept cross-origin requests from `http://localhost:3000`, `http://localhost:5500`, and the configured production frontend domain (e.g., GitHub Pages or Vercel URL).
2. THE System SHALL respond to all API requests with `Content-Type: application/json`.
3. THE System SHALL include a `success` boolean field in every API response body.
4. THE System SHALL expose a `/health` (or `/api/health`) endpoint that returns HTTP 200 with `{"status": "ok"}` without requiring authentication, so that monitoring tools can verify the service is running.
5. WHERE a production frontend domain is configured via the `ALLOWED_ORIGINS` environment variable, THE System SHALL include that domain in the CORS allow list.

---

### Requirement 19: Data Persistence and Database Initialisation

**User Story:** As a system operator, I want the database to be automatically initialised with required tables and seed data on first startup, so that I do not need to run manual migration scripts.

#### Acceptance Criteria

1. WHEN the application starts for the first time against an empty database, THE System SHALL create all required tables: users, tickets, glossary (Python backend); Users, Tickets, Replies, TranslationLogs (Node.js backend).
2. WHEN the Python backend starts against an empty users table, THE System SHALL seed one admin account (`admin@mtt.com` / `admin123`) and one client account (`client@mtt.com` / `client123`).
3. THE System SHALL use SQLite as the default database in development and SHALL support PostgreSQL in production via the `DATABASE_URL` environment variable.
4. WHEN the `DATABASE_URL` environment variable starts with `postgres://`, THE System SHALL normalise it to `postgresql://` before passing it to the ORM.
5. THE System SHALL enforce unique constraints on user email addresses at the database level.

---

### Requirement 20: Environment Configuration

**User Story:** As a developer or operator, I want all sensitive values and deployment-specific settings to be configurable through environment variables, so that the application can be deployed to different environments without code changes.

#### Acceptance Criteria

1. THE System SHALL read the following required environment variables: `JWT_SECRET` (Node.js) / `SECRET_KEY` (Python), `PORT`, and `DATABASE_URL` (production).
2. THE System SHALL read the following optional environment variables: `GEMINI_API_KEY`, `MYMEMORY_EMAIL`, `FLASK_DEBUG`, `JWT_EXPIRES_IN`, `ALLOWED_ORIGINS`.
3. WHEN `GEMINI_API_KEY` is not set, is an empty string, contains only whitespace, or contains a malformed value, THE AI_Service SHALL operate entirely in rule-based fallback mode without attempting to call the Gemini API.
4. WHEN `MYMEMORY_EMAIL` is configured, THE Translation_Service SHALL include it as the `de` parameter in MyMemory API requests to increase the daily word quota from 5,000 to 10,000.
5. THE System SHALL provide a `.env.example` file documenting all supported environment variables with example values.
