# MicroLearning Bot with Agno Agents

A sophisticated **Telegram and WhatsApp** bot powered by multiple Agno agents for microlearning, featuring daily video delivery, interactive quizzes, and RAG-based company documentation access.

## Messaging platforms

Which channels run is controlled by a single environment variable:

```bash
MESSAGING_PLATFORM=telegram   # Telegram only (default)
MESSAGING_PLATFORM=whatsapp   # WhatsApp Cloud API only
MESSAGING_PLATFORM=both       # Both at the same time
```

Agents never talk to a platform SDK directly — they use `MessagingRouter`, which
dispatches on the learner's platform. Adding a channel means adding one
`MessagingClient`, not touching the learning logic.

WhatsApp requires Meta-side configuration (business app, phone number ID,
permanent token, webhook). **See [docs/WHATSAPP_SETUP.md](docs/WHATSAPP_SETUP.md)
for the full step-by-step guide.**

Two WhatsApp constraints have no Telegram equivalent and affect behaviour:

- **24-hour customer service window** — free-form messages are only allowed
  within 24h of the learner's last inbound message; outside it you must use an
  approved template.
- **16 MB video limit** (Telegram allows 50 MB).

## Features

###  Video Sending Agent
- Sends daily videos from database to users
- Tracks user progress and video history
- Schedules videos based on user preferences

###   Question & Rating Agent
- Asks conceptual questions based on video content
- Rates and evaluates user answers using AI
- Provides feedback and learning insights
- Tracks learning progress

###   RAG Agent
- Access to company manuals and SOPs
- Semantic search capabilities
- Context-aware responses
- Document retrieval and summarization

## Architecture

The bot uses **Agno** (AgentOS) for dynamic agent orchestration:
- Each agent operates independently
- Agents communicate through shared state
- Dynamic routing based on user context
- Scalable and maintainable design

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Load Documents for RAG

```bash
python scripts/load_documents.py --path ./documents
```

### 5. Publish videos to the enabled platforms

Each platform issues its own media handle, so every video is uploaded once per
platform and the handle is cached in the `video_media` table.

```bash
python scripts/publish_videos.py --status
```

```bash
python scripts/publish_videos.py --all
```

### 6. Run the Bot

```bash
python start_bot.py
```

`start_bot.py` runs pre-flight checks (credentials for the enabled platforms,
directories, database, video files) before starting. `python main.py` skips
the checks.

## Project Structure

```
.
├── agents/                   # Agno agent implementations
│   ├── video_agent.py
│   ├── video_upload_agent.py     # uploads once per platform
│   ├── video_delivery_agent.py   # delivers via cached media refs
│   ├── question_agent.py
│   ├── rag_agent.py
│   └── orchestrator.py
├── messaging/                # Platform abstraction (the feature flag lives here)
│   ├── base.py                   # Platform, UserRef, errors, client interface
│   ├── telegram_client.py
│   ├── whatsapp_client.py        # Meta Graph API
│   ├── router.py                 # dispatches by UserRef.platform
│   ├── factory.py                # builds clients from MESSAGING_PLATFORM
│   └── worker.py                 # background asyncio loop for the webhook
├── database/                 # Database models and utilities
│   ├── models.py
│   ├── operations.py
│   └── migrations.py             # idempotent additive schema upgrades
├── config/                   # Configuration files
│   └── settings.py
├── dispatcher.py             # Platform-agnostic command handling
├── whatsapp_webhook.py       # Meta webhook + /health
├── main.py                   # Main entry point
├── start_bot.py              # Pre-flight checks + start
└── requirements.txt
```

## Usage

### Commands

- `/start` - Start the bot and register
- `/video` - Request today's video
- `/quiz` - Take a quiz on recent videos
- `/help` - Get help on available commands
- `/ask` - Ask questions about company docs (RAG)
- `/progress` - View your learning progress
- `/docs` - List available documents

On WhatsApp the slash is optional — `video`, `quiz`, `docs`, `help` and `hi`
work as bare words, because WhatsApp has no slash-command menu. While a quiz is
in progress bare words are treated as answers, so a legitimate answer is never
swallowed as a command.

### Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health`, `GET /api/health` | Liveness probe and agent status |
| `GET /webhook/whatsapp` | Meta's verification handshake |
| `POST /webhook/whatsapp` | Inbound WhatsApp messages (signature-verified) |

## Testing

```bash
pytest tests/ -v
```

The suite runs without the heavy runtime dependencies (chromadb,
sentence-transformers, python-telegram-bot) because the agents import them
lazily.

## Development

### Adding New Agents

1. Create a new agent file in `agents/`
2. Inherit from Agno's base agent class
3. Register the agent in `main.py`

### Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## License

MIT License
