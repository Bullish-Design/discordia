# Discordia Developer Guide

## Architectural Overview

Discordia is a Discord bot framework built on three core principles:

1. **Event-Driven Architecture** - Bot reacts to Discord gateway events
2. **Manager Pattern** - Domain logic separated into specialized managers
3. **Dual Persistence** - All data written to both database and JSONL

```
┌─────────────────────────────────────────────────────────┐
│                         Bot                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Discord Client (interactions.py)         │  │
│  └─────────────┬──────────────────┬──────────────────┘  │
│                │                  │                      │
│         on_ready event     on_message_create event      │
│                │                  │                      │
│  ┌─────────────▼────────┐  ┌─────▼──────────────────┐  │
│  │  CategoryManager     │  │   MessageHandler        │  │
│  │  - discover          │  │   - save user/message   │  │
│  │  - save              │  │   - get context         │  │
│  │  - lookup            │  │   - generate LLM reply  │  │
│  └──────────────────────┘  │   - send & persist      │  │
│                            └─────┬──────────────────┘  │
│  ┌──────────────────────┐        │                     │
│  │  ChannelManager      │◄───────┘                     │
│  │  - discover          │                              │
│  │  - ensure daily log  │                              │
│  │  - create channel    │                              │
│  └──────────────────────┘                              │
│                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │   DatabaseWriter     │  │    JSONLWriter        │   │
│  │   (in-memory impl)   │  │    (append-only)      │   │
│  └──────────────────────┘  └──────────────────────┘   │
│                                                         │
│  ┌──────────────────────┐                              │
│  │     LLMClient        │                              │
│  │   (Anthropic SDK)    │                              │
│  └──────────────────────┘                              │
└─────────────────────────────────────────────────────────┘
```

## Core Patterns

### 1. Optional Dependencies

Discordia's core can import without runtime dependencies:

```python
try:
    from interactions import Client, Intents
except Exception:
    # Fallback implementations for unit tests
    class Client: ...
```

This allows:
- Unit testing without Discord SDK
- Future provider swapping
- Minimal import side effects

### 2. Manager Pattern

Each domain has a dedicated manager:

- **CategoryManager** - Category discovery and lookup
- **ChannelManager** - Channel operations and daily log creation
- **MessageHandler** - Message processing and LLM orchestration

Managers are **stateless** (except for dependency injection) and coordinate between:
- Persistence layer (database + JSONL)
- Discord API (via client)
- LLM provider (via LLMClient)

### 3. Dual Persistence

Every entity is persisted twice:

```python
await self.db.save_message(message)      # Structured, queryable
await self.jsonl.write_message(message)  # Append-only backup
```

Database failures are **logged but non-fatal** - the bot continues operating. JSONL acts as disaster recovery.

### 4. Pydantic Models

All entities inherit from `DiscordiaModel` (which wraps `BaseModel`):

```python
class DiscordMessage(DiscordiaModel):
    id: int
    content: str
    author_id: int
    channel_id: int
    timestamp: datetime
    edited_at: datetime | None = None
```

Benefits:
- Validation on construction
- JSON serialization via `model_dump_json()`
- Type safety
- Easy to test without ORM dependencies

### 5. Graceful Degradation

The bot is designed to continue operating despite individual failures:

- Persistence failures → logged, bot continues
- Discord API failures → retried once, then error message to user
- LLM failures → user-friendly error message, conversation continues
- Missing categories → error logged, bot skips daily channel creation

## Project Structure

```
src/discordia/
├── __init__.py              # Public API exports
├── bot.py                   # Main Bot class and event handlers
├── settings.py              # Pydantic settings with env loading
├── exceptions.py            # Custom exception hierarchy
├── health.py                # Health check utility
│
├── models/                  # Pydantic domain models
│   ├── base.py              # DiscordiaModel base class
│   ├── category.py          # DiscordCategory
│   ├── channel.py           # DiscordTextChannel
│   ├── message.py           # DiscordMessage
│   └── user.py              # DiscordUser
│
├── persistence/             # Dual persistence layer
│   ├── database.py          # DatabaseWriter (in-memory impl)
│   └── jsonl.py             # JSONLWriter (append-only log)
│
├── llm/                     # LLM integration
│   └── client.py            # LLMClient (Anthropic wrapper)
│
└── managers/                # Domain logic coordinators
    ├── category_manager.py  # Category operations
    ├── channel_manager.py   # Channel operations + daily logs
    └── message_handler.py   # Message processing + LLM orchestration
```

## Component Details

### Bot (`bot.py`)

**Purpose:** Main orchestrator that wires together all components and handles Discord events.

**Key Responsibilities:**
- Initialize all managers and dependencies
- Register Discord event listeners
- Ensure daily log channel exists (on startup and date change)
- Route events to appropriate managers

**Important Fields:**
- `_last_date_checked: date | None` - Tracks when daily channel was last verified

**Event Handlers:**

```python
async def _on_ready(event: Ready):
    1. Initialize database
    2. Discover categories
    3. Discover channels
    4. Ensure today's log channel exists
```

```python
async def _on_message(event: MessageCreate):
    1. Ignore bot messages
    2. Ensure daily log channel (in case date changed)
    3. Delegate to MessageHandler
```

**Design Notes:**
- Event handlers catch **all exceptions** to prevent Discord gateway crashes
- Database/channel failures during ready are **logged but non-fatal**
- Uses `listen()` decorator for event registration (interactions.py convention)

### Settings (`settings.py`)

**Purpose:** Configuration management using Pydantic BaseSettings.

**Loading Strategy:**
1. Environment variables (case-insensitive)
2. `.env` file (optional)
3. Defaults for optional fields

**Validation:**
- `server_id` must be positive
- `message_context_limit` must be 1-100
- `max_message_length` must be 1-2000

**Usage Pattern:**

```python
settings = Settings()  # Auto-loads from env + .env
bot = Bot(settings)
```

### Models (`models/`)

All models inherit from `DiscordiaModel`:

```python
class DiscordiaModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
```

**Key Features:**
- `extra="ignore"` allows Discord API to return extra fields without errors
- `default_factory=datetime.utcnow` for timestamp fields
- Custom validators for business rules (e.g., positive IDs, name formats)

**Model Relationships:**
- `DiscordMessage.author_id` → `DiscordUser.id`
- `DiscordMessage.channel_id` → `DiscordTextChannel.id`
- `DiscordTextChannel.category_id` → `DiscordCategory.id` (nullable)

**Validation Examples:**

```python
@field_validator("name")
@classmethod
def _validate_channel_name(cls, value: str) -> str:
    if not cls._NAME_PATTERN.match(value):
        raise ValueError("Channel name must be lowercase, use hyphens...")
    return value
```

### DatabaseWriter (`persistence/database.py`)

**Purpose:** In-memory persistence matching SQLAlchemy-style async API.

**Why In-Memory?** 
The reference implementation uses SQLModel/SQLAlchemy, but this kata environment doesn't include those dependencies. This implementation provides the same async interface for testing.

**Internal State:**

```python
@dataclass(frozen=True)
class _State:
    categories: dict[int, DiscordCategory]
    channels: dict[int, DiscordTextChannel]
    users: dict[int, DiscordUser]
    messages: dict[int, DiscordMessage]
```

**Concurrency:** Uses `asyncio.Lock` to ensure thread-safe access.

**Key Methods:**
- `save_*()` - Upsert entity (raises if foreign keys invalid)
- `get_*()` - Retrieve by ID (returns None if not found)
- `get_*_by_name()` - Lookup by name within server
- `get_messages()` - Returns chronologically ordered recent messages

**Referential Integrity:**

```python
async def save_channel(channel: DiscordTextChannel):
    if channel.category_id not in self._state.categories:
        raise DatabaseError("missing category")
```

### JSONLWriter (`persistence/jsonl.py`)

**Purpose:** Append-only JSON Lines backup for disaster recovery.

**Format:**

```json
{"type": "category", "data": {"id": 123, "name": "Log", ...}}
{"type": "channel", "data": {"id": 456, "name": "2025-12-14", ...}}
{"type": "message", "data": {"id": 789, "content": "Hello", ...}}
{"type": "user", "data": {"id": 111, "username": "alice", ...}}
```

**Design Notes:**
- Uses `model_dump_json()` for safe serialization (handles datetimes)
- Writes are non-blocking (`asyncio.to_thread`)
- Missing file on read returns empty list (not an error)
- **No deduplication** - replaying would need external logic

**Thread Safety:** File I/O delegated to thread pool via `asyncio.to_thread`.

### LLMClient (`llm/client.py`)

**Purpose:** Lightweight wrapper for Anthropic SDK.

**Key Design:**
- Runtime import of `anthropic` SDK (optional dependency)
- Provider-agnostic message format internally
- Extracts text from provider response objects

**API:**

```python
async def generate_response(
    context_messages: list[DiscordMessage],
    system_prompt: str | None,
    max_tokens: int
) -> str
```

**Error Handling:**
- Detects context-too-large errors by keywords ("context", "token", "length")
- Wraps all provider errors in `LLMAPIError`
- Logs request/response previews at DEBUG level

**Message Formatting:**

```python
# Converts Discord messages to provider format
[{"role": "user", "content": msg.content} for msg in messages]
```

Note: Currently all messages are `role="user"`. Future enhancement could alternate user/assistant based on `author.bot`.

### CategoryManager (`managers/category_manager.py`)

**Purpose:** Discover and persist Discord categories.

**Key Methods:**

```python
async def discover_categories(guild) -> list[DiscordCategory]:
    """Iterate guild.channels, filter GuildCategory, persist all"""

async def get_category_by_name(name: str) -> DiscordCategory:
    """Lookup by name, raise CategoryNotFoundError if missing"""
```

**Discovery Flow:**
1. Filter `guild.channels` for `GuildCategory` instances
2. Extract ID, name, position from Discord API objects
3. Persist to database + JSONL
4. Return list of discovered categories

**Error Strategy:**
- Discovery failures raise `DiscordAPIError`
- Individual persistence failures are logged but don't stop discovery
- Lookup failures raise domain-specific `CategoryNotFoundError`

### ChannelManager (`managers/channel_manager.py`)

**Purpose:** Manage text channels and auto-create daily log channels.

**Daily Log Pattern:**

```python
LOG_CHANNEL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def is_log_channel(name: str) -> bool:
    return bool(LOG_CHANNEL_PATTERN.match(name))

def get_daily_channel_name() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")
```

**Key Methods:**

```python
async def discover_channels(guild) -> list[DiscordTextChannel]:
    """Discover all GuildText channels in guild"""

async def ensure_daily_log_channel(guild, category_id) -> DiscordTextChannel:
    """Get or create today's YYYY-MM-DD channel"""

async def create_channel(guild, name, category_id) -> DiscordTextChannel:
    """Create new channel via Discord API"""
```

**Daily Channel Flow:**
1. Generate today's name (`get_daily_channel_name()`)
2. Query database by name
3. If exists → return
4. If missing → create via `guild.create_text_channel()`
5. Persist and return

### MessageHandler (`managers/message_handler.py`)

**Purpose:** Orchestrate message processing, context loading, LLM generation, and reply persistence.

**Message Processing Flow:**

```python
async def handle_message(discord_message):
    1. Ignore if author is bot
    2. Save user (non-fatal if fails)
    3. Save message (non-fatal if fails)
    4. Check if channel is log channel (YYYY-MM-DD)
       - If not → return early
    5. Load recent context (MESSAGE_CONTEXT_LIMIT messages)
    6. Generate LLM response
    7. Split response into chunks (<= MAX_MESSAGE_LENGTH)
    8. Send each chunk via discord_message.reply()
    9. Persist each bot message (non-fatal if fails)
```

**Error Handling Strategy:**

| Error Type | User Message | Bot Behavior |
|------------|--------------|--------------|
| No context available | "⚠️ No conversation history available yet" | Return early |
| Context too large | "⚠️ Conversation history is too long. Try starting a new topic..." | Return early |
| LLM API failure | "⚠️ Unable to generate response. Please try again." | Return early |
| Send failure | Retry once after 1s | If still fails: "⚠️ Error: Unable to send complete response" |
| Persistence failure | (None - silent) | Log error, continue |

**Message Splitting:**

```python
def split_message(text: str) -> list[str]:
    """Split on newlines, respecting MAX_MESSAGE_LENGTH limit"""
```

Preserves line breaks where possible. Each chunk becomes a separate Discord reply.

**Context Loading:**

```python
async def get_context_messages(channel_id: int) -> list[DiscordMessage]:
    return await self.db.get_messages(channel_id, limit=self.context_limit)
```

Returns chronologically ordered (oldest to newest) messages.

## Key Flows

### Bot Startup

```
1. Settings loaded from environment
2. DatabaseWriter, JSONLWriter, LLMClient initialized
3. Managers initialized with dependencies
4. Discord client created with token + intents
5. Event listeners registered
6. client.start() called → connects to Discord gateway
7. on_ready event fires:
   a. Database initialized
   b. Categories discovered
   c. Channels discovered
   d. Daily log channel ensured
8. Bot enters event loop
```

### Message Received

```
1. on_message_create event fires
2. Check if author is bot → ignore if yes
3. Ensure daily log channel (date might have changed)
4. Save user to database + JSONL
5. Save message to database + JSONL
6. Fetch full channel object to check name
7. Check if channel name matches YYYY-MM-DD → ignore if no
8. Load last N messages from database
9. Format messages for LLM
10. Call LLM API with context + system prompt
11. Split response into chunks
12. For each chunk:
    a. Send via discord_message.reply()
    b. Save bot message to database + JSONL
```

### Daily Channel Creation

```
1. Bot startup or date change detected
2. Generate today's channel name (YYYY-MM-DD)
3. Query database for channel by name
4. If exists → done
5. If missing:
   a. Lookup log category by name
   b. Call guild.create_text_channel(name, parent_id=category_id)
   c. Persist new channel to database + JSONL
   d. Return channel
```

## Development Guidelines

### Adding a New Manager

1. Create file in `managers/` with clear responsibility
2. Inject dependencies via `__init__` (db, jsonl, etc.)
3. Keep methods **async** and **stateless**
4. Raise domain-specific exceptions (e.g., `ChannelNotFoundError`)
5. Log at appropriate levels (DEBUG for routine, INFO for significant events)
6. Add to `Bot.__init__` and wire dependencies

### Adding a New Model

1. Create in `models/`, inherit from `DiscordiaModel`
2. Use Pydantic fields with descriptions
3. Add validators for business rules
4. Implement `to_discord_format()` for API serialization
5. Update `DatabaseWriter._State` with storage dict
6. Add save/get methods to `DatabaseWriter`
7. Add write method to `JSONLWriter`

### Error Handling

**General Principle:** Catch exceptions at boundary (event handlers, API calls), log with context, convert to domain exceptions or handle gracefully.

**Patterns:**

```python
# At boundaries - catch all
try:
    await process_message()
except Exception as e:
    logger.error("Message processing failed: %s", e, exc_info=True)

# Within managers - raise domain exceptions
if not category:
    raise CategoryNotFoundError(f"Category {id} not found")

# Persistence - non-fatal
try:
    await self.db.save(entity)
except DatabaseError as e:
    logger.error("Persistence failed: %s", e, exc_info=True)
```

### Logging Strategy

| Level | Use Case |
|-------|----------|
| DEBUG | Routine operations (saved message, loaded N items) |
| INFO | Significant events (bot ready, discovered N channels) |
| WARNING | Recoverable issues (context approaching limits, retrying send) |
| ERROR | Failures requiring attention (API errors, persistence failures) |

**Format:** Include relevant IDs/names for debugging.

### Testing Considerations

**Unit Tests:**
- Mock Discord client/objects (use fallback classes)
- Mock LLM client (return canned responses)
- Test managers in isolation with in-memory database
- Use pytest + pytest-asyncio

**Integration Tests:**
- Test full message flow with real database
- Verify dual persistence (both db and JSONL updated)
- Test error recovery scenarios

**Example Test Structure:**

```python
import pytest
from discordia import Bot, Settings
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_message_handler_saves_user():
    settings = Settings(...)
    bot = Bot(settings)
    
    # Mock Discord message
    message = MagicMock()
    message.author.id = 123
    message.author.username = "test_user"
    message.content = "Hello"
    
    await bot.message_handler.save_user(message.author)
    
    user = await bot.db.get_user(123)
    assert user.username == "test_user"
```

### Extending LLM Integration

To add new providers:

1. Create new client in `llm/` (e.g., `openai_client.py`)
2. Match `LLMClient` interface:
   - `generate_response(context, system_prompt, max_tokens) -> str`
   - `summarize(messages) -> str`
3. Update `Bot.__init__` to support provider selection via settings
4. Keep message format conversion internal to client

### Extending Persistence

To add real SQLAlchemy:

1. Replace `DatabaseWriter` implementation
2. Keep same async interface (save/get methods)
3. Add SQLModel table definitions to models
4. Update initialization to run migrations
5. No changes needed in managers (they use abstract interface)

## Extension Points

### Custom System Prompts

Modify `MessageHandler.handle_message()`:

```python
system_prompt = self._build_system_prompt(channel, context)
response = await self.llm_client.generate_response(
    context,
    system_prompt=system_prompt
)
```

### Custom Channel Filters

Modify `ChannelManager.is_log_channel()`:

```python
def is_log_channel(self, name: str) -> bool:
    # Custom logic here
    return name.startswith("ai-") or self.LOG_CHANNEL_PATTERN.match(name)
```

### Multi-Server Support

Currently assumes single server (`settings.server_id`). To support multiple:

1. Remove `server_id` from Settings
2. Modify discovery to iterate `client.guilds`
3. Update database queries to filter by server_id
4. Add server_id to all manager lookups

### Response Streaming

LLMClient could stream responses:

```python
async def generate_response_stream(self, context) -> AsyncIterator[str]:
    async with client.messages.stream(...) as stream:
        async for chunk in stream:
            yield chunk.text
```

Update MessageHandler to accumulate chunks and send when buffer reaches safe size.

## Performance Considerations

### Current Implementation

- In-memory database → O(n) lookups by name
- JSONL writes are blocking file I/O (mitigated by thread pool)
- Message context loaded fresh each time (no caching)

### Production Optimizations

1. **Database Indexes:** Add indexes on (server_id, name) for categories/channels
2. **Message Pagination:** Use cursor-based pagination for large histories
3. **Context Caching:** Cache last N messages per channel, invalidate on new message
4. **Batch Persistence:** Queue writes and flush periodically
5. **Connection Pooling:** Use SQLAlchemy async engine with pool

### Memory Usage

- In-memory database scales with total messages/channels/users
- JSONL file grows unbounded (implement rotation if needed)
- Discord client maintains WebSocket connection (minimal overhead)

## Security Considerations

- **API Keys:** Never commit `.env` to version control
- **Token Scope:** Use minimum required Discord intents
- **Input Validation:** Pydantic models validate all user input
- **SQL Injection:** Not applicable (in-memory dict storage)
- **Rate Limiting:** Discord SDK handles this, but be aware of limits
- **LLM Costs:** No built-in usage limits - implement if needed

## Future Enhancements

1. **Web Dashboard** - FastAPI app to view conversations
2. **Multi-LLM Support** - OpenAI, Cohere, local models
3. **RAG Integration** - Semantic search over message history
4. **Custom Commands** - Slash commands for summaries, exports
5. **Thread Support** - Respond in Discord threads
6. **Voice Channels** - Transcription + LLM responses
7. **Reaction-Based Features** - Regenerate on 🔄, summarize on 📝
8. **Admin Commands** - Reset context, change model, adjust limits
