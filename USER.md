# Discordia User Guide

Discordia is a Discord bot that uses Mirascope to respond to messages in specially-named daily log channels.

## Quickstart

### 1. Install Dependencies

```bash
pip install discordia
# Or with uv:
uv pip install discordia
```

### 2. Configure Environment

Create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token
SERVER_ID=your_discord_server_id
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**Required:**
- `DISCORD_TOKEN` - Get from [Discord Developer Portal](https://discord.com/developers/applications)
- `SERVER_ID` - Right-click your Discord server → "Copy ID" (enable Developer Mode first)
- `ANTHROPIC_API_KEY` - Get from [Anthropic Console](https://console.anthropic.com/)

**Optional:**
- `LOG_CATEGORY_NAME` - Category name for daily channels (default: "Log")
- `AUTO_CREATE_DAILY_LOGS` - Auto-create YYYY-MM-DD channels (default: true)
- `DATABASE_URL` - SQLite path (default: "sqlite+aiosqlite:///discordia.db")
- `JSONL_PATH` - Backup file path (default: "discordia_backup.jsonl")
- `LLM_MODEL` - Claude model (default: "claude-sonnet-4-20250514")
- `MESSAGE_CONTEXT_LIMIT` - Messages to include in context (default: 20, range: 1-100)
- `MAX_MESSAGE_LENGTH` - Discord limit (default: 2000, range: 1-2000)

### 3. Set Up Discord Server

1. Create a category named "Log" (or your custom `LOG_CATEGORY_NAME`)
2. The bot will auto-create daily channels like `2025-12-14` inside this category

### 4. Run the Bot

```python
from discordia import Bot, Settings, setup_logging

setup_logging("INFO")
settings = Settings()  # Loads from .env
bot = Bot(settings)
bot.run()
```

## How It Works

### Daily Log Channels

Discordia only responds in channels with names matching `YYYY-MM-DD` format (e.g., `2025-12-14`).

**Auto-Creation:** If `AUTO_CREATE_DAILY_LOGS=true`, the bot creates today's channel on startup and when the date changes.

**Manual Creation:** You can create channels manually if you prefer:
1. Ensure they're in the configured log category
2. Name them `YYYY-MM-DD`
3. The bot will respond to messages there

### Message Flow

1. User posts message in a `YYYY-MM-DD` channel
2. Bot saves the message and user to database + JSONL
3. Bot loads the last 20 messages (configurable) as context
4. Bot sends context to Claude for response generation
5. Bot replies with Claude's response
6. Bot saves its own reply to database + JSONL

### Context Limits

If conversation history grows too large:
- Bot will warn when approaching limits
- You'll see "⚠️ Conversation history is too long" error
- **Solution:** Start a new topic in a fresh channel (create a new daily channel or use tomorrow's)

## Advanced Usage

### Custom Configuration

```python
from discordia import Settings

settings = Settings(
    discord_token="...",
    server_id=123456789,
    anthropic_api_key="...",
    log_category_name="Daily Logs",
    message_context_limit=30,
    llm_model="claude-opus-4-20250514"
)
```

### Health Checks

```python
from discordia import health_check

status = await health_check(bot)
# Returns: {"database": bool, "client": bool, "managers": bool}
```

### Programmatic Control

```python
# Start bot (non-blocking)
import asyncio
asyncio.create_task(bot.client.start())

# Stop bot gracefully
await bot.stop()
```

### Persistence

Discordia uses **dual persistence**:

1. **SQLite Database** (`discordia.db`) - Queryable, structured storage
2. **JSONL Backup** (`discordia_backup.jsonl`) - Append-only log for disaster recovery

Both are updated simultaneously. If database fails, JSONL can be replayed.

### Message Chunking

Responses exceeding Discord's 2000-character limit are automatically split:
- Preserves line breaks where possible
- Each chunk sent as separate message
- All chunks persisted to database

### Error Handling

The bot is resilient to failures:
- Individual persistence failures (database or JSONL) are logged but don't stop the bot
- LLM failures result in user-friendly error messages
- Discord API failures are retried once with 1-second delay
- Channel lookup failures are logged but don't crash the bot

## Troubleshooting

### Bot doesn't respond to messages

- ✅ Check channel name matches `YYYY-MM-DD` format exactly
- ✅ Verify channel is in the configured log category
- ✅ Check logs for errors
- ✅ Ensure bot has "Send Messages" and "Read Message History" permissions

### "Category 'Log' not found" error

- Create a category named "Log" (or your custom `LOG_CATEGORY_NAME`) in Discord
- The bot discovers categories on startup, so restart after creating

### LLM errors

- ✅ Verify `ANTHROPIC_API_KEY` is valid
- ✅ Check you have API credits
- ✅ Review context size (reduce `MESSAGE_CONTEXT_LIMIT` if needed)

### Database errors

- Check file permissions for `discordia.db`
- Verify `DATABASE_URL` path is writable
- Check disk space

## API Reference

### Main Classes

```python
from discordia import Bot, Settings, setup_logging
from discordia import health_check
```

### Exception Types

```python
from discordia import (
    DiscordiaError,           # Base exception
    ConfigurationError,       # Invalid settings
    DiscordAPIError,          # Discord API failures
    ChannelNotFoundError,     # Channel lookup failed
    CategoryNotFoundError,    # Category lookup failed
    MessageSendError,         # Message send failed
    DatabaseError,            # Database operation failed
    JSONLError,               # JSONL operation failed
    LLMError,                 # LLM operation failed
    LLMAPIError,              # LLM API call failed
    ContextTooLargeError,     # Context exceeds limits
)
```

### Settings Validation

All settings are validated on load:
- `server_id` must be positive integer
- `message_context_limit` must be 1-100
- `max_message_length` must be 1-2000

Invalid settings raise `ValidationError` on startup.
