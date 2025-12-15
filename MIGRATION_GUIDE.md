# Discordia v0.2.0 - Refactoring Migration Guide

## Overview

This refactoring transforms Discordia from an event-driven bot framework into a **declarative, template-based Discord environment manager** with deep Pydantic integration and PyGentic LLM capabilities.

## Key Changes

### Architecture

**Before (v0.1.0):**
- Monolithic `Bot` class handling all concerns
- Hardcoded daily log channel pattern
- Tight coupling to database and JSONL writers
- Mandatory LLM integration
- Discovery-only (no declarative structure)

**After (v0.2.0):**
- Thin `Bot` dispatcher delegating to handlers
- Template-based declarative server structure
- Protocol-based abstractions (state, handlers, persistence)
- Optional LLM integration via PyGentic
- Reconciliation engine syncing templates to Discord

### Directory Structure

```
src/discordia/
├── types.py              # Constrained types (DiscordSnowflake, ChannelName, etc.)
├── exceptions.py         # Enhanced exception hierarchy
├── settings.py           # SecretStr credentials, PyGentic config
├── templates/            # Declarative server structure
│   ├── base.py          # Frozen, validated template base
│   ├── channel.py       # Discriminated union channel types
│   ├── category.py      # Category templates
│   ├── patterns.py      # Dynamic channel generators (DailyLogPattern, etc.)
│   ├── server.py        # Complete server template
│   └── generated.py     # PyGentic auto-generation
├── state/               # Runtime Discord state
│   ├── models.py        # Live entity models
│   ├── protocol.py      # StateStore protocol
│   ├── memory.py        # In-memory implementation
│   └── registry.py      # Entity lookups
├── engine/              # Core bot machinery
│   ├── bot.py          # Event dispatcher
│   ├── context.py      # MessageContext object
│   ├── discovery.py    # Discord → State sync
│   └── reconciler.py   # Template → Discord sync
├── handlers/            # Message processing
│   ├── protocol.py     # MessageHandler protocol
│   ├── router.py       # Handler routing
│   ├── models.py       # PyGentic GenModel subclasses
│   ├── pygentic_adapter.py  # Async wrappers
│   ├── llm.py          # PyGentic LLM handler
│   └── logging.py      # Simple logging handler
└── persistence/         # Long-term storage
    ├── protocol.py     # PersistenceBackend protocol
    ├── jsonl.py        # JSONL implementation
    └── memory.py       # In-memory (testing)
```

## Migration Steps

### 1. Update Dependencies

```toml
# pyproject.toml
dependencies = [
    "interactions.py>=5.0.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.0.0",
    "pygentic @ git+https://github.com/Bullish-Design/PyGentic.git",
]

[project.optional-dependencies]
anthropic = ["mirascope[anthropic]>=1.25.0"]
```

### 2. Update Settings

**Before:**
```python
settings = Settings(
    discord_token="sk-...",
    server_id=123456789,
    anthropic_api_key="sk-...",
)
```

**After:**
```python
from pydantic import SecretStr

settings = Settings(
    discord_token=SecretStr("sk-..."),  # SecretStr for security
    server_id=123456789,
    anthropic_api_key=SecretStr("sk-..."),  # Optional
    auto_reconcile=True,
    llm_provider="anthropic",
    llm_model="claude-sonnet-4-20250514",
)
```

### 3. Define Server Template

**Before:** Server structure discovered at runtime.

**After:** Declarative template definition:

```python
from discordia.templates import (
    ServerTemplate,
    CategoryTemplate,
    TextChannelTemplate,
    DailyLogPattern,
)

template = ServerTemplate(
    categories=[
        CategoryTemplate(
            name="General",
            channels=[
                TextChannelTemplate(name="welcome", topic="Welcome to our server!"),
                TextChannelTemplate(name="rules", topic="Server rules and guidelines"),
            ],
        ),
        CategoryTemplate(
            name="Logs",
            channels=[],  # Populated by DailyLogPattern
        ),
    ],
    patterns=[
        DailyLogPattern(days_ahead=1, days_behind=7),
    ],
)
```

### 4. Create Handlers

**Before:** LLM logic embedded in `MessageHandler`.

**After:** Composable handlers implementing protocol:

```python
from discordia.handlers import LLMHandler, LoggingHandler

llm_handler = LLMHandler(
    api_key=settings.anthropic_api_key,
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)

logging_handler = LoggingHandler()

handlers = [llm_handler, logging_handler]
```

### 5. Initialize Bot

**Before:**
```python
bot = Bot(settings)
bot.run()
```

**After:**
```python
from discordia import Bot

bot = Bot(
    settings=settings,
    template=template,
    handlers=[llm_handler],
)
bot.run()
```

## New Features

### Constrained Types

```python
from discordia.types import ChannelName, DiscordSnowflake

channel_name: ChannelName = "valid-channel"  # Validated: lowercase, hyphens only
server_id: DiscordSnowflake = 123456789  # Validated: positive integer
```

### Discriminated Channel Unions

```python
from discordia.templates import TextChannelTemplate, VoiceChannelTemplate

channels: list[ChannelTemplate] = [
    TextChannelTemplate(name="general", slowmode_seconds=5),
    VoiceChannelTemplate(name="voice-chat", bitrate=96000),
]
# Pydantic auto-detects type from "type" field
```

### Dynamic Channel Patterns

```python
from discordia.templates import DailyLogPattern, PrefixedPattern

patterns = [
    DailyLogPattern(days_ahead=1, days_behind=7),
    PrefixedPattern(
        prefix="team",
        suffixes=["alpha", "beta", "gamma"],
        separator="-",
    ),
]
```

### PyGentic LLM Integration

```python
from discordia.handlers.models import ConversationResponse
from discordia.handlers.pygentic_adapter import generate_async

response_model = await generate_async(
    ConversationResponse,
    channel_name="general",
    user_message="Hello!",
    history=["user: hi", "bot: hello"],
)

response = response_model.response  # Cached after first access
```

### Custom Handlers

```python
from discordia.handlers.protocol import MessageHandler
from discordia.engine.context import MessageContext

class CustomHandler:
    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.channel_name.startswith("custom-")
    
    async def handle(self, ctx: MessageContext) -> str | None:
        return f"Custom response for {ctx.author_name}"
```

## Breaking Changes

### Removed

- `managers/category_manager.py` → `engine/reconciler.py` + `state/registry.py`
- `managers/channel_manager.py` → `engine/reconciler.py` + `state/registry.py`
- `managers/message_handler.py` → `handlers/llm.py` + `handlers/protocol.py`
- `models/` folder → Split into `state/models.py` (runtime) and `templates/` (desired state)
- `llm/client.py` → `handlers/llm.py` (PyGentic-based)
- `persistence/database.py` → `state/memory.py` (in-memory state)
- `health.py` → Removed (replaced by protocol-based design)

### Changed

- `Bot.__init__()` now accepts `template` and `handlers`
- `Settings` uses `SecretStr` for credentials
- State is in-memory by default (protocol allows swapping)
- LLM integration is optional and handler-based

## Testing

All existing tests remain valid with minimal changes. New test structure:

```
tests/
├── test_types.py              # Constrained type validation
├── test_templates.py          # Template creation and validation
├── test_state.py              # State store and registry
├── test_engine.py             # Discovery and reconciliation
├── test_handlers.py           # Handler protocol implementations
├── test_pygentic_integration.py  # PyGentic-specific tests
└── test_persistence.py        # Persistence protocols
```

## Migration Checklist

- [ ] Update `pyproject.toml` dependencies
- [ ] Convert credentials to `SecretStr` in settings
- [ ] Define `ServerTemplate` for your server structure
- [ ] Create handlers (LLM, logging, custom)
- [ ] Update `Bot` initialization with template and handlers
- [ ] Remove imports from deleted modules
- [ ] Update tests to use new structure
- [ ] Run `pytest` to verify compatibility
- [ ] Deploy and verify reconciliation

## Benefits

1. **Declarative** - Define desired state, not imperative steps
2. **Type-safe** - Pydantic validation throughout
3. **Modular** - Protocol-based, swappable components
4. **Testable** - Mock at protocol boundaries
5. **Secure** - `SecretStr` for credentials
6. **Optional LLM** - Use handlers only when needed
7. **PyGentic** - Structured LLM outputs with caching

## Support

For questions or issues during migration, refer to:
- Refactoring guide: `REFACTORING_GUIDE_Opus.md`
- PyGentic docs: https://github.com/Bullish-Design/PyGentic
- Pydantic docs: https://docs.pydantic.dev
