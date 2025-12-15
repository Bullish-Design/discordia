# Discordia

Declarative Discord bot framework with state management.

## Features

- **Declarative Templates**: Define server structure as code
- **Pattern-based Channels**: Dynamically generate channels based on rules
- **State Management**: In-memory state tracking for channels, users, messages
- **Handler Protocol**: Simple interface for message handling

## Installation

```bash
uv add discordia
```

## Quick Start

```python
from discordia import Bot, LoggingHandler, ServerTemplate, Settings, TextChannelTemplate

settings = Settings()  # Loads DISCORD_TOKEN and SERVER_ID from environment

template = ServerTemplate(
    uncategorized_channels=[
        TextChannelTemplate(name="general", topic="General chat"),
    ]
)

bot = Bot(settings=settings, template=template, handlers=[LoggingHandler()])
bot.run()
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Bot token from Discord Developer Portal |
| `SERVER_ID` | Yes | Discord server (guild) ID |

## Custom Handlers

Implement the `MessageHandler` protocol:

```python
from discordia import MessageContext, MessageHandler

class MyHandler:
    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.channel_name == "my-channel"

    async def handle(self, ctx: MessageContext) -> str | None:
        return f"Hello, {ctx.author_name}!"
```

## Custom Patterns

Extend `ChannelPattern` for dynamic channel generation:

```python
from discordia import ChannelPattern, ChannelTemplate, TextChannelTemplate

class MyPattern(ChannelPattern):
    def generate(self) -> list[ChannelTemplate]:
        return [TextChannelTemplate(name="generated-channel")]
```

## Examples

See the `examples/` directory for patterns and LLM handler implementations.
