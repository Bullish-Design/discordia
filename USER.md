# USER.md

# Discordia User Guide

Discordia is a Discord bot framework built on `discord-py-interactions` that provides a clean, structured approach to building Discord bots with state management, plugins, and handlers.

## Installation

```bash
uv add discordia
```

Or with pip:

```bash
pip install discordia
```

## Quickstart

Here's a minimal bot that echoes messages:

```python
from discordia import Bot, BotConfig, EchoHandler
from discordia.types import DiscordID, DiscordToken

config = BotConfig(
    discord_token=DiscordToken("your-token-here"),
    server_id=DiscordID(123456789012345678)
)

bot = Bot(
    config=config,
    handlers=[EchoHandler()]
)

bot.run()
```

This creates a bot that responds to messages starting with `echo:` by echoing back the content.

## Core Concepts

### Handlers

Handlers process messages and optionally return responses. Each handler implements two methods:

- `can_handle(ctx)` - Returns `True` if the handler should process this message
- `handle(ctx)` - Processes the message and returns an optional string response

The first handler that can handle a message will process it. If it returns a response, the bot sends it back to the channel.

#### Built-in Handlers

**LoggingHandler** - Logs all messages to Python's logging system:

```python
from discordia import LoggingHandler, LoggingConfig

handler = LoggingHandler(
    config=LoggingConfig(
        enabled=True,
        log_level="INFO"
    )
)
```

**EchoHandler** - Echoes messages that match a prefix:

```python
from discordia import EchoHandler, EchoConfig

handler = EchoHandler(
    config=EchoConfig(prefix="!")
)
```

#### Custom Handlers

Create custom handlers by subclassing `Handler`:

```python
from pydantic import BaseModel
from discordia import Handler
from discordia.context import MessageContext

class GreetingConfig(BaseModel):
    greetings: list[str] = ["hello", "hi", "hey"]

class GreetingHandler(Handler[GreetingConfig]):
    def __init__(self, config: GreetingConfig | None = None):
        super().__init__(config=config or GreetingConfig())
    
    async def can_handle(self, ctx: MessageContext) -> bool:
        return any(
            ctx.content.lower().startswith(greeting) 
            for greeting in self.config.greetings
        )
    
    async def handle(self, ctx: MessageContext) -> str | None:
        return f"Hello, {ctx.author.username}!"
```

### Plugins

Plugins hook into bot lifecycle events without needing to process every message. They implement:

- `on_ready(bot, guild)` - Called when the bot connects and syncs state
- `on_message(bot, ctx)` - Called for every message before handlers run

```python
from discordia.plugins import Plugin
from discordia.context import MessageContext

class StatisticsPlugin:
    def __init__(self):
        self.message_count = 0
    
    async def on_ready(self, bot, guild):
        print(f"Connected to {guild.name}")
    
    async def on_message(self, bot, ctx: MessageContext):
        self.message_count += 1
        if self.message_count % 100 == 0:
            print(f"Processed {self.message_count} messages")
```

Use plugins for:
- Analytics and statistics
- Logging and monitoring
- Cross-cutting concerns
- Background tasks that don't need to respond

### State Management

Discordia automatically discovers and stores Discord entities:

```python
# Access state through the bot
channel = await bot.state.get_channel(channel_id)
user = await bot.state.get_user(user_id)
messages = await bot.state.get_messages(channel_id, limit=20)

# Or through MessageContext
history = await ctx.get_history(limit=50)
```

State entities include:
- **Category** - Discord channel categories
- **Channel** - Text channels with topics and positions
- **User** - Discord users (cached as encountered)
- **Message** - Message history (stored as sent/received)

The `EntityRegistry` provides convenience queries:

```python
from discordia.registry import EntityRegistry

registry = EntityRegistry(bot.state)

# Find entities by name
category = await registry.get_category_by_name("General", server_id)
channel = await registry.get_channel_by_name("announcements", server_id)

# List channels in a category
channels = await registry.get_channels_in_category(category_id)
```

### MessageContext

Every handler receives a `MessageContext` with rich information:

```python
async def handle(self, ctx: MessageContext) -> str | None:
    # Basic message info
    print(ctx.content)              # Message text
    print(ctx.author.username)      # Who sent it
    print(ctx.channel.name)         # Which channel
    
    # Computed properties
    if ctx.is_command:
        print(ctx.command_name)     # Command without prefix
        print(ctx.command_args)     # List of arguments
    
    print(ctx.age_ms)               # Message age in milliseconds
    print(ctx.mentions_bot)         # True if contains <@...>
    
    # Access history
    history = await ctx.get_history(limit=10)
    
    # Access state
    messages = await ctx.store.get_messages(ctx.channel.id)
```

## Configuration

### BotConfig

```python
from discordia import BotConfig
from discordia.types import DiscordID, DiscordToken

config = BotConfig(
    discord_token=DiscordToken("your-token-here"),
    server_id=DiscordID(123456789012345678),
    message_context_limit=20  # Default message history limit
)
```

All configuration is immutable and validated at initialization.

### Handler Configuration

Each handler accepts a typed config object:

```python
from discordia import EchoConfig

config = EchoConfig(prefix="bot:")
handler = EchoHandler(config=config)
```

Configuration is validated using Pydantic, ensuring type safety and catching errors early.

## Common Patterns

### Command-Based Bot

```python
from pydantic import BaseModel
from discordia import Handler
from discordia.context import MessageContext

class CommandConfig(BaseModel):
    prefix: str = "!"

class CommandHandler(Handler[CommandConfig]):
    def __init__(self, config: CommandConfig | None = None):
        super().__init__(config=config or CommandConfig())
    
    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.content.startswith(self.config.prefix)
    
    async def handle(self, ctx: MessageContext) -> str | None:
        if not ctx.is_command:
            return None
        
        if ctx.command_name == "ping":
            return "Pong!"
        elif ctx.command_name == "info":
            return f"Channel: {ctx.channel.name}, Age: {ctx.age_ms}ms"
        
        return None
```

### Context-Aware Responses

```python
async def handle(self, ctx: MessageContext) -> str | None:
    # Check message history
    history = await ctx.get_history(limit=5)
    recent_content = [msg.content for msg in history]
    
    if "help" in recent_content:
        return "I see you asked for help recently!"
    
    # Access channel info
    if ctx.channel.topic:
        return f"This channel is about: {ctx.channel.topic}"
    
    return None
```

### Multi-Handler Pipeline

Handlers are evaluated in order. The first matching handler processes the message:

```python
bot = Bot(
    config=config,
    handlers=[
        LoggingHandler(),      # Always logs (returns None)
        CommandHandler(),      # Handles commands
        GreetingHandler(),     # Handles greetings
        EchoHandler()          # Fallback echo
    ]
)
```

## Error Handling

Discordia includes custom exceptions for different failure modes:

- `ConfigurationError` - Invalid bot configuration
- `StateError` - State management issues
- `DiscordAPIError` - Discord API failures
- `EntityNotFoundError` - Entity lookup failures
- `ValidationError` - Data validation failures

```python
from discordia.exceptions import EntityNotFoundError

try:
    channel = await registry.get_channel_by_name("nonexistent", server_id)
except EntityNotFoundError:
    print("Channel not found")
```

## Logging

Discordia uses Python's standard logging module:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Adjust Discordia's log level
logging.getLogger("discordia").setLevel(logging.DEBUG)
```

## Advanced Usage

### Custom State Storage

Implement the `StateStore` protocol for custom storage backends:

```python
from discordia.state import StateStore, Category, Channel, User, Message
from discordia.types import DiscordID

class DatabaseState:
    async def save_channel(self, channel: Channel) -> None:
        # Save to database
        pass
    
    async def get_channel(self, id: DiscordID) -> Channel | None:
        # Load from database
        pass
    
    # Implement other StateStore methods...
```

Use it with the bot:

```python
from discordia.bot import Bot

custom_state = DatabaseState()
bot = Bot(config=config, handlers=handlers)
bot.state = custom_state  # Replace default MemoryState
```

### Custom Discord Client

Inject a custom client for testing or alternative Discord libraries:

```python
from discordia.bot import DiscordClient

class MockClient:
    def __init__(self):
        self.user = None
    
    def add_listener(self, listener):
        pass
    
    async def fetch_guild(self, guild_id: int):
        return MockGuild()
    
    def start(self):
        pass
    
    async def stop(self):
        pass

bot = Bot(config=config, handlers=handlers, client=MockClient())
```

## Best Practices

1. **Keep handlers focused** - Each handler should do one thing well
2. **Use plugins for cross-cutting concerns** - Analytics, logging, monitoring
3. **Validate configuration early** - Use Pydantic models for all config
4. **Handle errors gracefully** - Catch exceptions in handlers to avoid crashes
5. **Test without Discord** - Use custom clients for unit testing
6. **Log important events** - Use Python's logging for observability
7. **Keep state operations async** - All state methods are async for future extensibility

## Getting Help

- Check logs for detailed error messages
- Review the DEV.md guide for architecture details
- Enable DEBUG logging to see internal operations
- Test handlers independently before integration
