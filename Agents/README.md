# MicroLearning Telegram Bot with Agno Agents

A sophisticated Telegram bot powered by multiple Agno agents for microlearning, featuring daily video delivery, interactive quizzes, and RAG-based company documentation access.

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

### 5. Run the Bot

```bash
python main.py
```

## Project Structure

```
.
├── agents/              # Agno agent implementations
│   ├── video_agent.py
│   ├── question_agent.py
│   └── rag_agent.py
├── database/           # Database models and utilities
│   ├── models.py
│   └── operations.py
├── utils/             # Utility functions
│   ├── embeddings.py
│   └── scheduler.py
├── config/            # Configuration files
│   └── settings.py
├── main.py            # Main bot entry point
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
