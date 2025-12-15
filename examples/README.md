# Discordia Examples

Example patterns and handlers that extend the core Discordia library.

## Patterns

Concrete implementations of `ChannelPattern` for generating dynamic channel structures:

- **DailyLogPattern**: Generates channels in `YYYY-MM-DD` format
- **WeekDayPattern**: Generates channels in `YYYY-WW-DD` (ISO year-week-day) format  
- **PrefixedPattern**: Generates channels with common prefixes from a suffix list

## LLM Handlers

PyGentic-based message handlers for LLM integration:

- **LLMHandler**: Generic handler with configurable channel pattern matching
- **WeekDayHandler**: Specialized handler for weekday-pattern channels

### Dependencies

LLM handlers require PyGentic:

```bash
uv add pygentic --git https://github.com/Bullish-Design/PyGentic.git
```

## Usage

See `basic_bot.py` and `llm_bot.py` for complete examples.
