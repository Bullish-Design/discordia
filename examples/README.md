# Discordia Week-Day Chatbot Walkthrough

Demonstrates Discordia's template reconciliation and LLM message handling using WW-DD channel format.

## What This Does

1. Creates "Log" category with channels named `WW-DD` (ISO week number, day 01-07 with Monday=01)
2. Auto-syncs every 5 minutes to ensure current channel exists
3. Responds to messages using OpenAI API

## Quick Start

### 1. Prerequisites

- Python 3.11+
- UV package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Discord bot token ([create one here](https://discord.com/developers/applications))
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 2. Discord Bot Setup

Create a Discord application and bot:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application", name it, and create
3. Go to "Bot" section, click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - Message Content Intent (required to read messages)
   - Server Members Intent (recommended)
5. Copy your bot token
6. Go to OAuth2 > URL Generator:
   - Select scopes: `bot`
   - Select bot permissions: `Manage Channels`, `Send Messages`, `Read Message History`
7. Open the generated URL to invite the bot to your server

### 3. Get Your Server ID

1. Enable Developer Mode in Discord: Settings > Advanced > Developer Mode
2. Right-click your server icon and select "Copy ID"

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
# DISCORD_TOKEN=your_bot_token
# SERVER_ID=your_server_id
# ANTHROPIC_API_KEY=your_openai_key  # Yes, use this field for OpenAI
```

### 5. Run the Bot

```bash
# UV will automatically install dependencies and run
uv run daily_chatbot.py
```

## How It Works

### Template Definition

```python
# Today's channel in WW-DD format (e.g., "50-01" for week 50, Monday)
today = date.today()
iso = today.isocalendar()
channel_name = f"{iso.week:02d}-{iso.weekday:02d}"

ServerTemplate(
    categories=[
        CategoryTemplate(
            name="Log",
            channels=[
                TextChannelTemplate(
                    name=channel_name,
                    topic="Weekly log channel"
                )
            ]
        )
    ]
)
```

### Reconciliation Process

When the bot starts:
1. **Discovery**: Scans existing Discord channels and categories
2. **Comparison**: Compares template vs. actual state
3. **Reconciliation**: Creates missing categories/channels
4. **Periodic Sync**: Re-runs every 5 minutes (configurable)

### Message Handling

The `WeekDayHandler` processes messages:
- **Filter**: Only handles channels matching WW-DD pattern (e.g., "50-01")
- **Context**: Includes last 20 messages as conversation history
- **Response**: Generates reply using OpenAI API
- **Delivery**: Posts response as reply to user

## Key Configuration Options

In `Settings`:

```python
settings = Settings(
    llm_provider="openai",        # or "anthropic", "google"
    llm_model="gpt-4",            # or "gpt-3.5-turbo"
    llm_temperature=0.7,          # 0.0 = deterministic, 2.0 = creative
    auto_reconcile=True,          # Sync on startup
    reconcile_interval=300,       # Seconds between syncs (0 = disabled)
    message_context_limit=20,     # Messages included in LLM context
)
```

## Extending the Example

### Using WeekDay Pattern Generator

Auto-generate WW-DD channels for a rolling window:

```python
from weekday_pattern import WeekDayPattern

ServerTemplate(
    categories=[CategoryTemplate(name="Log", channels=[])],
    patterns=[
        WeekDayPattern(
            weeks_ahead=0,   # Current week
            weeks_behind=1,  # Plus last week
            topic="Weekly log"
        )
    ]
)
```

### Custom Message Handler

```python
from discordia.handlers.protocol import MessageHandler
from discordia.engine.context import MessageContext

class KeywordHandler:
    async def can_handle(self, ctx: MessageContext) -> bool:
        return "!help" in ctx.content.lower()

    async def handle(self, ctx: MessageContext) -> str | None:
        return "Available commands: !help, !info"

bot = Bot(settings, template, handlers=[KeywordHandler(), weekday_handler])
```

### Multiple Handlers

Handlers execute in order until one responds:

```python
handlers = [
    AdminCommandHandler(),    # First: admin commands
    KeywordHandler(),         # Second: keyword responses
    WeekDayHandler(),        # Fallback: AI in WW-DD channels
    LoggingHandler(),        # Always logs (returns None)
]
```

## Troubleshooting

**Bot connects but doesn't respond:**
- Verify "Message Content Intent" is enabled in Discord Developer Portal
- Check the bot has "Send Messages" permission in your server

**Channel not created:**
- Ensure bot has "Manage Channels" permission
- Check logs for reconciliation errors

**OpenAI errors:**
- Verify API key in .env
- Check OpenAI account has credits/quota
- Note: API key goes in `ANTHROPIC_API_KEY` field (PyGentic handles provider routing)

## Project Structure

```
discordia/
├── engine/          # Core bot and event handling
│   ├── bot.py      # Main Bot class
│   ├── context.py  # Message context for handlers
│   └── reconciler.py  # Template sync logic
├── handlers/        # Message processing
│   ├── llm.py      # LLM-powered handler
│   └── router.py   # Handler chain execution
├── templates/       # Server structure definition
│   ├── server.py   # ServerTemplate
│   ├── category.py # CategoryTemplate
│   ├── channel.py  # Channel types
│   └── patterns.py # Dynamic generators (DailyLogPattern, etc.)
├── state/           # Runtime state management
│   └── memory.py   # In-memory storage
└── settings.py      # Configuration
```

## License

MIT
