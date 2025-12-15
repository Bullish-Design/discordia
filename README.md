# Discordia

A Discord bot framework for building LLM-powered conversational bots with automatic daily logging.

## Features

- 🤖 **LLM-Powered Responses** - Uses Anthropic Claude for intelligent, contextual replies
- 📅 **Daily Log Channels** - Automatically creates and manages `YYYY-MM-DD` channels
- 💾 **Dual Persistence** - SQLite database + JSONL backup for reliability
- 🔄 **Context Management** - Loads recent message history for coherent conversations
- 🛡️ **Resilient** - Graceful error handling, automatic retries, non-fatal failures
- ⚡ **Async-First** - Built on modern async Python for performance
- 🎯 **Type-Safe** - Pydantic models throughout with full validation

## Installation

```bash
pip install discordia
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install discordia
```

## Quick Start

### 1. Get API Keys

- **Discord Token**: [Discord Developer Portal](https://discord.com/developers/applications)
- **Anthropic API Key**: [Anthropic Console](https://console.anthropic.com/)
- **Server ID**: Right-click your Discord server → "Copy ID" (enable Developer Mode in settings)

### 2. Configure

Create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token
SERVER_ID=your_discord_server_id
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Set Up Discord Server

Create a category named "Log" in your Discord server. The bot will auto-create daily channels inside it.

### 4. Run

```python
from discordia import Bot, Settings, setup_logging

setup_logging("INFO")
settings = Settings()
bot = Bot(settings)
bot.run()
```

### 5. Chat

Send a message in today's channel (e.g., `2025-12-14`) and the bot will respond using Claude!

## How It Works

1. Bot monitors channels with `YYYY-MM-DD` format names
2. User sends a message in a daily log channel
3. Bot loads recent conversation history (last 20 messages by default)
4. Bot sends context to Claude for response generation
5. Bot replies and persists everything to database + JSONL

```
User Message → Context Loading → Claude API → Response → Dual Persistence
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DISCORD_TOKEN` | *required* | Discord bot token |
| `SERVER_ID` | *required* | Discord server (guild) ID |
| `ANTHROPIC_API_KEY` | *required* | Anthropic API key |
| `LOG_CATEGORY_NAME` | `"Log"` | Category name for daily channels |
| `AUTO_CREATE_DAILY_LOGS` | `true` | Auto-create YYYY-MM-DD channels |
| `DATABASE_URL` | `"sqlite+aiosqlite:///discordia.db"` | SQLite database path |
| `JSONL_PATH` | `"discordia_backup.jsonl"` | JSONL backup file path |
| `LLM_MODEL` | `"claude-sonnet-4-20250514"` | Claude model to use |
| `MESSAGE_CONTEXT_LIMIT` | `20` | Messages to include in context (1-100) |
| `MAX_MESSAGE_LENGTH` | `2000` | Discord message length limit (1-2000) |

## Documentation

- **[User Guide](USER.md)** - Installation, configuration, usage, troubleshooting
- **[Developer Guide](DEV.md)** - Architecture, implementation details, extending the framework

## Architecture

```
Bot
├── CategoryManager      # Discover and manage Discord categories
├── ChannelManager       # Create and manage daily log channels
├── MessageHandler       # Process messages and orchestrate LLM responses
├── DatabaseWriter       # SQLite persistence
├── JSONLWriter          # Append-only JSONL backup
└── LLMClient           # Anthropic Claude integration
```

## Project Structure

```
src/discordia/
├── __init__.py              # Public API
├── bot.py                   # Main Bot class
├── settings.py              # Configuration
├── exceptions.py            # Custom exceptions
├── health.py                # Health checks
├── models/                  # Pydantic domain models
│   ├── category.py
│   ├── channel.py
│   ├── message.py
│   └── user.py
├── persistence/             # Dual persistence layer
│   ├── database.py
│   └── jsonl.py
├── llm/                     # LLM integration
│   └── client.py
└── managers/                # Business logic coordinators
    ├── category_manager.py
    ├── channel_manager.py
    └── message_handler.py
```

## Example: Custom Configuration

```python
from discordia import Bot, Settings

settings = Settings(
    discord_token="...",
    server_id=123456789,
    anthropic_api_key="...",
    log_category_name="Daily Logs",
    message_context_limit=30,
    llm_model="claude-opus-4-20250514"
)

bot = Bot(settings)
bot.run()
```

## Example: Health Check

```python
from discordia import health_check

status = await health_check(bot)
print(status)
# {'database': True, 'client': True, 'managers': True}
```

## Error Handling

Discordia is designed for resilience:

- **Persistence failures** - Logged but non-fatal
- **LLM failures** - User sees friendly error message
- **Discord API failures** - Retried once, then graceful degradation
- **Context too large** - User notified to start new channel

## Use Cases

- **Daily Journal Bot** - Personal journaling with AI reflection
- **Team Logs** - Daily standup conversations with team insights
- **Learning Companion** - Study sessions with AI tutor
- **Project Notes** - Development logs with AI assistance
- **Meeting Minutes** - Conversational meeting notes

## Requirements

- Python 3.11+
- Discord bot with Message Content intent enabled
- Anthropic API key

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src

# Linting
ruff check src
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [interactions.py](https://github.com/interactions-py/interactions.py) - Discord API wrapper
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) - Claude integration
- [Pydantic](https://docs.pydantic.dev/) - Data validation and settings
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL database integration

## Support

- 📖 [Documentation](USER.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/discordia/issues)
- 💬 [Discussions](https://github.com/yourusername/discordia/discussions)

---

**Note**: This bot requires Discord's Message Content intent. Enable it in your bot's Discord Developer Portal settings under "Privileged Gateway Intents".
