# Aiko Desktop API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

All `/api/*` endpoints require a JWT Bearer token in the `Authorization` header.

```bash
Authorization: Bearer <token>
```

Generate a token by calling `/status` (public) or use the token provided by the desktop app on startup.

### Public Endpoints (No Auth Required)

- `GET /status` — Server status and metrics
- `GET /health` — Health check with bridge status
- `GET /ws` — WebSocket connection for real-time streaming

---

## Endpoints

### `GET /status`

Returns server status, CPU/RAM metrics, and RAG availability.

**Response:**
```json
{
  "status": "online",
  "hub_name": "Aiko Neural Hub v2",
  "metrics": {
    "cpu": 12.5,
    "ram": 45.2,
    "rag": 142
  },
  "rag_available": true
}
```

### `GET /health`

Health check with timestamp and bridge status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-12T14:30:00",
  "bridges": {
    "mcp": "online",
    "vision": "online"
  },
  "llm_provider": "Ollama"
}
```

### `GET /api/settings`

Returns current user settings with secrets redacted.

**Response:**
```json
{
  "llm": {
    "url": "http://127.0.0.1:11434/api/chat",
    "model": "qwen3.5:cloud"
  },
  "tts": {
    "enabled": true,
    "voice": "vivian",
    "speed": 0.9
  }
}
```

### `POST /api/settings`

Update user settings. Settings are merged with existing values. Redacted values (e.g., `sk-...`) are ignored to prevent overwriting secrets with masked strings.

**Request Body:**
```json
{
  "llm": {
    "model": "gemma4:31b-cloud"
  },
  "tts": {
    "enabled": false
  }
}
```

**Response:**
```json
{"status": "success"}
```

### `POST /api/settings/reload`

Hot-reload configuration without restarting the server.

**Response:**
```json
{"status": "reloaded"}
```

### `POST /api/chat`

Send a message to Aiko and get a response. Used by Discord/Telegram bots.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "Hello Aiko!",
  "user_id": "user123",
  "attachments": []
}
```

**Validation:**
- `message`: 1-10,000 characters, required
- `user_id`: max 256 characters, defaults to `"user"`
- `attachments`: array of strings (URLs)

**Response:**
```json
{
  "response": "Hello! How can I help you today?",
  "emotion": "happy",
  "gif_url": null,
  "audio_url": "http://127.0.0.1:8000/api/tts/audio/voice_123.wav",
  "audio_path": "/path/to/voice_123.wav",
  "timestamp": "2026-06-12T14:30:00"
}
```

### `POST /api/purge`

Clear all memory for a user (or global if no user_id).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body (optional):**
```json
{"user_id": "user123"}
```

**Response:**
```json
{"status": "success"}
```

### `GET /api/sessions`

List all chat sessions.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "sessions": [
    {"id": "abc123", "title": "First Session", "preview": "Hello!", "timestamp": "2026-06-12T14:00:00"}
  ]
}
```

### `POST /api/sessions/rename`

Rename a session.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{"id": "abc123", "name": "New Name"}
```

### `POST /api/sessions/pin`

Pin a session to the top.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{"id": "abc123"}
```

### `DELETE /api/sessions`

Delete a session.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?id=abc123
```

### `GET /api/history`

Get chat history for a user/session.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?uid=user123
```

**Response:**
```json
{
  "history": [
    {"role": "user", "content": "Hello", "timestamp": "2026-06-12T14:00:00"},
    {"role": "assistant", "content": "Hi there!", "timestamp": "2026-06-12T14:00:01"}
  ]
}
```

### `POST /api/upload`

Upload a file (image, PDF, text, code).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: The file to upload

**Response:**
```json
{
  "status": "success",
  "filename": "image.png",
  "url": "http://127.0.0.1:8000/uploads/image.png",
  "type": "image/png"
}
```

### `GET /api/project`

List project structure (files and folders in workspace).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "structure": [
    {"name": "core", "type": "folder", "path": "/path/to/core", "size": 0},
    {"name": "README.md", "type": "file", "path": "/path/to/README.md", "size": 2048}
  ]
}
```

### `GET /api/relationship`

Get relationship stats (affection, trust, level).

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?id=user123
```

**Response:**
```json
{
  "affection": 42,
  "level": "Neural Link Active",
  "trust": 85
}
```

### `POST /api/latex/render`

Render a LaTeX math snippet to an image.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{"snippet": "E = mc^2"}
```

**Validation:**
- `snippet`: 1-5,000 characters, required

**Response:**
```json
{
  "url": "/api/latex/image/equation_123.png",
  "path": "/path/to/equation_123.png"
}
```

### `GET /api/latex/image/{filename}`

Serve a rendered LaTeX image.

**No auth required.**

---

## WebSocket `/ws`

Connect to `/ws` for real-time streaming. No auth required for the WebSocket handshake (but messages are processed server-side with auth).

### Client → Server Messages

```json
{"type": "chat", "text": "Hello", "user_id": "user123", "session_id": "abc123", "attachments": []}
```

```json
{"type": "speak", "text": "Hello world", "emotion": "happy"}
```

```json
{"type": "branch", "text": "Tell me more", "message_id": "msg_123", "user_id": "user123"}
```

```json
{"type": "system", "action": "reload_config"}
```

```json
{"type": "system", "action": "proactive_toggle", "state": true, "interval": 180}
```

```json
{"type": "listen"}
```

```json
{"type": "ping"}
```

### Server → Client Events

```json
{"type": "chat_token", "data": {"token": "Hello", "text": "Hello", "emotion": "happy"}}
```

```json
{"type": "chat_end", "data": {"role": "assistant", "text": "Hello!", "emotion": "happy", "gif_url": null}}
```

```json
{"type": "chat_start", "data": {"role": "user", "text": "Hello"}}
```

```json
{"type": "emotion", "data": {"emotion": "happy"}}
```

```json
{"type": "tts_audio", "data": {"url": "/api/tts/audio/voice_123.wav", "text": "Hello"}}
```

```json
{"type": "tts_chunk", "data": {"text": "Hello"}}
```

```json
{"type": "tts_amplitude", "data": {"amplitude": 0.75}}
```

```json
{"type": "state", "data": {"thinking": true, "source": "api"}}
```

```json
{"type": "biological_sync", "data": {"chemicals": {"dopamine": 0.5, "serotonin": 0.6}}}
```

```json
{"type": "pong"}
```

---

## Error Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad Request — invalid JSON or validation error |
| 401 | Unauthorized — missing or invalid Bearer token |
| 404 | Not Found — session or resource not found |
| 500 | Internal Server Error — see logs for details |
| 502 | Bad Gateway — LLM network error |
| 503 | Service Unavailable — component not initialized |
| 504 | Gateway Timeout — LLM request timed out |

---

*Generated from Pydantic schemas in `core/api/schemas.py`.*
