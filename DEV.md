# DEV.md

# Discordia Developer Guide

This guide helps developers understand, contribute to, and extend the Discordia framework.

## Architecture Overview

Discordia follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Bot Orchestrator              │ ← Coordinates everything
├─────────────────────────────────────────┤
│  Discovery  │  Plugins   │  Handlers    │ ← Extension points
├─────────────────────────────────────────┤
│       State Store Protocol              │ ← Storage abstraction
├─────────────────────────────────────────┤
│  Entity Models  │  Context  │  Types    │ ← Domain models
└─────────────────────────────────────────┘
```

### Design Principles

1. **Protocol-based abstractions** - Uses Python protocols for loose coupling
2. **Pydantic everywhere** - All models use Pydantic for validation
3. **Async-first** - All I/O operations are async
4. **Testability** - Core logic independent of Discord client
5. **Immutable configuration** - Config models are frozen after creation
6. **Type safety** - Custom types with validation at boundaries

## Module Breakdown

### types.py

Defines validated type aliases using Pydantic:

```python
DiscordID = Annotated[int, AfterValidator(validate_discord_id)]
ChannelName = Annotated[str, AfterValidator(validate_channel_name)]
Username = Annotated[str, AfterValidator(validate_username)]
MessageContent = Annotated[str, AfterValidator(validate_message_content)]
DiscordToken = SecretStr
```

**Key patterns:**
- Uses `Annotated` with `AfterValidator` for runtime validation
- Validators raise `ValueError` with descriptive messages
- `SecretStr` prevents token leakage in logs/errors

**When to extend:**
- Add new type aliases when creating new entities
- Keep validators focused on format, not business logic

### state.py

Core domain models and storage abstraction.

**StateEntity base class:**
```python
class StateEntity(BaseModel):
    id: DiscordID
    created_at: datetime
    updated_at: datetime
```

- Auto-updates `updated_at` on any field change (via `update_timestamp` validator)
- Normalizes datetimes to UTC in `_coerce_datetimes`
- Uses `model_config = ConfigDict(validate_assignment=True)` for runtime validation

**Entity models:**
- `Category` - Discord channel categories
- `Channel` - Text channels with optional category_id
- `User` - Discord users with username and bot flag
- `Message` - Messages with author, channel, and timestamp

**StateStore protocol:**
```python
@runtime_checkable
class StateStore(Protocol):
    async def save_category(self, category: Category) -> None: ...
    async def get_channel(self, id: DiscordID) -> Channel | None: ...
    # etc.
```

**MemoryState implementation:**
- In-memory dictionaries with asyncio locks
- Validates foreign keys (category_id, author_id, channel_id)
- `get_messages` sorts by timestamp and ID for stable ordering

**When to extend:**
- Add new entity types (Server, Role, Reaction, etc.)
- Implement alternative storage backends (database, Redis, etc.)
- Add query methods to StateStore protocol

### registry.py

Convenience layer for querying entities by properties other than ID.

**Current queries:**
- `get_category_by_name(name, server_id)` - Find category by name
- `get_channel_by_name(name, server_id)` - Find channel by name
- `get_channels_in_category(category_id)` - List channels in category

**Implementation note:**
Only works with `MemoryState` currently. Acquires the lock and iterates stored entities.

**When to extend:**
- Add new query methods as user needs arise
- Consider implementing for other StateStore backends
- Add pagination for large result sets

### exceptions.py

Custom exception hierarchy:

```python
DiscordiaError (base)
├── ConfigurationError
├── StateError
│   └── EntityNotFoundError
├── DiscordAPIError
└── ValidationError
```

All exceptions store an optional `cause` for error chaining.

**When to extend:**
- Add specific exception types for new failure modes
- Keep hierarchy shallow (2-3 levels max)

### context.py

`MessageContext` provides rich context to handlers:

**Core fields:**
- `message_id`, `content`, `author`, `channel`, `store`, `timestamp`

**Computed properties:**
- `is_command` - Checks for `!`, `/`, `.` prefix
- `command_name` - Extracts command without prefix
- `command_args` - Splits arguments
- `age_ms` - Message age in milliseconds
- `mentions_bot` - Detects `<@` mention syntax

**Methods:**
- `get_history(limit)` - Retrieves recent messages from channel

**When to extend:**
- Add computed properties for common message patterns
- Add helper methods for frequent operations
- Keep context immutable (no state mutation)

### handlers.py

Handler framework for message processing.

**Base Handler:**
```python
class Handler(BaseModel, Generic[TConfig]):
    config: TConfig
    
    async def can_handle(self, ctx: MessageContext) -> bool:
        raise NotImplementedError
    
    async def handle(self, ctx: MessageContext) -> str | None:
        raise NotImplementedError
```

**Built-in handlers:**
- `LoggingHandler` - Logs messages at configurable level
- `EchoHandler` - Echoes messages matching a prefix

**Handler lifecycle:**
1. Bot calls `can_handle()` for each handler in order
2. First handler returning `True` has its `handle()` method called
3. If `handle()` returns a string, bot sends it as a reply
4. Loop stops after first handler processes message

**When to extend:**
- Create new handlers for specific bot behaviors
- Keep configs as Pydantic models for validation
- Return `None` if handler shouldn't reply

### plugins.py

Plugin protocol for lifecycle hooks:

```python
@runtime_checkable
class Plugin(Protocol):
    async def on_ready(self, bot: Any, guild: Any) -> None: ...
    async def on_message(self, bot: Any, ctx: MessageContext) -> None: ...
```

**Key differences from handlers:**
- Plugins run for ALL messages (handlers have `can_handle` filter)
- Plugins don't return responses
- Plugins access the full bot instance

**Use cases:**
- Analytics and metrics
- Logging and monitoring
- Background tasks
- Database persistence

**When to extend:**
- Add new lifecycle hooks (on_reaction, on_member_join, etc.)
- Keep protocol minimal to reduce implementation burden

### discovery.py

Discovers and syncs Discord guild state.

**DiscoveryEngine methods:**
- `discover_categories(guild)` - Syncs all categories
- `discover_channels(guild)` - Syncs all text channels

**Best-effort imports:**
```python
try:
    from interactions.models.discord.channel import GuildCategory, GuildText
except Exception:
    # Fallback classes for testing
```

This pattern allows testing without installing `discord-py-interactions`.

**When to extend:**
- Add discovery for other entity types (roles, emojis, etc.)
- Implement incremental sync (only changed entities)
- Add rate limiting for large guilds

### config.py

Immutable configuration models:

```python
class BotConfig(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    
    discord_token: DiscordToken
    server_id: DiscordID
    message_context_limit: int = Field(default=20, ge=1, le=100)
```

**Key patterns:**
- `frozen=True` prevents modification after creation
- `strict=True` disallows extra fields
- Validators run via `model_validator(mode="after")`

**When to extend:**
- Add new config fields as needed
- Keep validation simple (use Pydantic's built-in validators)
- Use `Field()` for default values and constraints

### bot.py

Main orchestrator coordinating all components.

**Bot initialization:**
```python
def __init__(
    self,
    config: BotConfig,
    handlers: list[Handler] | None = None,
    plugins: list[Plugin] | None = None,
    client: DiscordClient | None = None,
):
    self.state = MemoryState()
    self.registry = EntityRegistry(self.state)
    self.discovery = DiscoveryEngine(self.state, config.server_id)
    self.client = client or Client(...)
    self._setup_listeners()
```

**Event flow:**

1. **on_ready:**
   - Fetches guild
   - Discovers categories and channels
   - Calls plugin `on_ready()` hooks
   
2. **on_message:**
   - Validates and saves message/author/channel
   - Calls plugin `on_message()` hooks
   - Evaluates handlers in order
   - Sends reply if handler returns string

**Key methods:**
- `_ensure_channel()` - Creates channel entity if not in state
- `_reply_and_record()` - Sends reply and saves bot's message to state

**Best-effort imports:**
Similar to discovery.py, uses fallback classes when `discord-py-interactions` unavailable.

**When to extend:**
- Add new event handlers (reactions, edits, etc.)
- Implement error recovery strategies
- Add metrics and monitoring

## Development Setup

### Prerequisites

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Project Structure

```
discordia/
├── src/
│   └── discordia/
│       ├── __init__.py
│       ├── bot.py
│       ├── config.py
│       ├── context.py
│       ├── discovery.py
│       ├── exceptions.py
│       ├── handlers.py
│       ├── plugins.py
│       ├── registry.py
│       ├── state.py
│       └── types.py
├── tests/
│   ├── test_bot.py
│   ├── test_context.py
│   ├── test_handlers.py
│   ├── test_state.py
│   └── ...
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=discordia --cov-report=html

# Run specific test file
pytest tests/test_state.py

# Run with verbose output
pytest -v
```

## Code Conventions

### Imports

Always use:
```python
from __future__ import annotations
```

Keep imports at the top:
```python
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field

from discordia.types import DiscordID
```

Order: future, stdlib, third-party, local (separated by blank lines).

### Type Hints

Use modern syntax without quotes:
```python
# Good
async def get_channel(self, id: DiscordID) -> Channel | None:
    return self.channels.get(id)

# Avoid (no quotes needed with __future__ annotations)
async def get_channel(self, id: DiscordID) -> "Channel | None":
    return self.channels.get(id)
```

### Pydantic Models

Use Pydantic for all data models:
```python
class MyModel(BaseModel):
    model_config = ConfigDict(...)
    
    id: DiscordID
    name: str = Field(min_length=1, max_length=100)
    
    @model_validator(mode="after")
    def validate_model(self) -> Self:
        # Cross-field validation
        return self
```

### Async/Await

All I/O operations must be async:
```python
# Good
async def save_channel(self, channel: Channel) -> None:
    async with self._lock:
        self.channels[channel.id] = channel

# Avoid
def save_channel(self, channel: Channel) -> None:
    self.channels[channel.id] = channel
```

### Error Handling

Use custom exceptions:
```python
from discordia.exceptions import StateError

async def save_message(self, message: Message) -> None:
    if message.author_id not in self.users:
        raise StateError(f"User {message.author_id} not found")
```

Log errors appropriately:
```python
import logging

logger = logging.getLogger(__name__)

try:
    await operation()
except Exception as exc:
    logger.exception("Operation failed: %s", exc)
    raise
```

### Line Length

Keep lines under 120 characters:
```python
# Good
async def get_category_by_name(
    self, 
    name: str, 
    server_id: DiscordID
) -> Category:
    ...

# Avoid lines over 120 chars
async def get_category_by_name(self, name: str, server_id: DiscordID) -> Category:
    ...  # (if this line exceeds 120)
```

## Testing Patterns

### Testing Without Discord

Use dependency injection:
```python
class MockClient:
    def __init__(self):
        self.user = MockUser()
    
    def add_listener(self, listener):
        self.listeners.append(listener)

def test_bot_initialization():
    config = BotConfig(discord_token="test", server_id=123)
    bot = Bot(config=config, client=MockClient())
    assert bot.state is not None
```

### Testing Handlers

```python
async def test_echo_handler():
    handler = EchoHandler(config=EchoConfig(prefix="!"))
    
    ctx = MessageContext(
        message_id=1,
        content="!hello world",
        author=User(id=1, username="test"),
        channel=Channel(id=1, name="general", server_id=123),
        store=MemoryState(),
        timestamp=datetime.now(UTC)
    )
    
    assert await handler.can_handle(ctx)
    response = await handler.handle(ctx)
    assert response == "hello world"
```

### Testing State

```python
async def test_state_storage():
    state = MemoryState()
    
    channel = Channel(id=1, name="test", server_id=123)
    await state.save_channel(channel)
    
    retrieved = await state.get_channel(1)
    assert retrieved == channel
```

## Extension Points

### Custom Handlers

Create new message handlers:

```python
from pydantic import BaseModel
from discordia import Handler
from discordia.context import MessageContext

class MyConfig(BaseModel):
    setting: str = "default"

class MyHandler(Handler[MyConfig]):
    async def can_handle(self, ctx: MessageContext) -> bool:
        return "trigger" in ctx.content.lower()
    
    async def handle(self, ctx: MessageContext) -> str | None:
        return f"Handled with config: {self.config.setting}"
```

### Custom Plugins

Add lifecycle hooks:

```python
class MyPlugin:
    async def on_ready(self, bot, guild):
        print(f"Bot ready in {guild.name}")
    
    async def on_message(self, bot, ctx):
        if ctx.author.bot:
            return  # Ignore bot messages
        # Do something with every message
```

### Custom State Storage

Implement StateStore protocol:

```python
import asyncpg
from discordia.state import StateStore, Channel
from discordia.types import DiscordID

class PostgresState:
    def __init__(self, connection_string: str):
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def save_channel(self, channel: Channel) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO channels VALUES ($1, $2, $3) "
                "ON CONFLICT (id) DO UPDATE ...",
                channel.id, channel.name, channel.server_id
            )
    
    async def get_channel(self, id: DiscordID) -> Channel | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM channels WHERE id = $1", id)
            return Channel(**row) if row else None
```

### Custom Entity Types

Add new domain models:

```python
from discordia.state import StateEntity
from discordia.types import DiscordID

class Role(StateEntity):
    name: str
    color: int
    permissions: int
    server_id: DiscordID
```

Extend StateStore protocol:
```python
class StateStore(Protocol):
    async def save_role(self, role: Role) -> None: ...
    async def get_role(self, id: DiscordID) -> Role | None: ...
```

## Common Pitfalls

### 1. Forgetting async/await

```python
# Wrong
def handle(self, ctx: MessageContext) -> str | None:
    messages = ctx.store.get_messages(ctx.channel.id)

# Correct
async def handle(self, ctx: MessageContext) -> str | None:
    messages = await ctx.store.get_messages(ctx.channel.id)
```

### 2. Not handling None returns

```python
# Risky
channel = await state.get_channel(channel_id)
print(channel.name)  # Might raise AttributeError

# Safe
channel = await state.get_channel(channel_id)
if channel:
    print(channel.name)
```

### 3. Modifying immutable config

```python
# Wrong - BotConfig is frozen
config.server_id = 456

# Correct - Create new config
new_config = BotConfig(
    discord_token=config.discord_token,
    server_id=456
)
```

### 4. Circular imports

Keep import hierarchy clean:
- types.py imports nothing from discordia
- state.py imports only types and exceptions
- Higher-level modules import lower-level ones

### 5. Not normalizing datetimes

```python
# Wrong
timestamp = datetime.now()  # No timezone

# Correct
from datetime import UTC, datetime
timestamp = datetime.now(UTC)
```

## Contributing Guidelines

### Before You Start

1. Open an issue describing your proposed change
2. Wait for maintainer feedback
3. Fork the repository
4. Create a feature branch

### Making Changes

1. Write tests for new functionality
2. Ensure all tests pass: `pytest`
3. Format code: `black src/ tests/`
4. Type check: `mypy src/`
5. Lint: `ruff check src/ tests/`

### Submitting Changes

1. Commit with descriptive messages
2. Push to your fork
3. Open a pull request
4. Address review feedback

### Code Review Checklist

- [ ] Tests added for new features
- [ ] Docstrings added for public APIs
- [ ] Type hints on all functions
- [ ] No breaking changes (or documented if unavoidable)
- [ ] Error handling appropriate
- [ ] Logging added for important operations
- [ ] Updated USER.md if user-facing changes

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Inspect State

```python
# After bot startup
print(f"Channels: {len(bot.state.channels)}")
print(f"Users: {len(bot.state.users)}")
print(f"Messages: {len(bot.state.messages)}")
```

### Test Handlers Independently

```python
# Create minimal context
ctx = MessageContext(
    message_id=1,
    content="test",
    author=User(id=1, username="test"),
    channel=Channel(id=1, name="test", server_id=123),
    store=MemoryState(),
    timestamp=datetime.now(UTC)
)

handler = MyHandler()
result = await handler.handle(ctx)
```

### Use Mock Client

```python
class MockClient:
    def __init__(self):
        self.events = []
    
    def add_listener(self, listener):
        self.events.append(listener)
    
    # Simulate events
    async def simulate_message(self, content: str):
        event = MockMessageEvent(content)
        for listener in self.events:
            await listener(event)
```

## Performance Considerations

### State Access

MemoryState uses asyncio locks. For high-throughput bots, consider:
- Sharding across multiple processes
- Read-heavy caching layer
- Database backend for persistence

### Message History

`get_messages()` loads and sorts in memory. For large channels:
- Implement pagination
- Use database indexes
- Limit default history size

### Handler Evaluation

Handlers run sequentially. Optimize `can_handle()`:
- Keep it fast (avoid heavy computation)
- Return early when possible
- Cache compiled regexes

## Future Enhancements

Areas for potential contribution:

1. **Additional entity types** - Roles, reactions, threads, etc.
2. **Database backends** - PostgreSQL, MongoDB, Redis implementations
3. **Advanced discovery** - Incremental sync, webhooks, voice channels
4. **More handlers** - Moderation, games, natural language processing
5. **Monitoring** - Prometheus metrics, health checks
6. **Horizontal scaling** - Sharding support, distributed state
7. **Testing utilities** - Mock factories, test fixtures
8. **Documentation** - More examples, video tutorials

## Resources

- Discord API: https://discord.com/developers/docs
- discord-py-interactions: https://interactions-py.github.io/
- Pydantic: https://docs.pydantic.dev/
- Python async: https://docs.python.org/3/library/asyncio.html
