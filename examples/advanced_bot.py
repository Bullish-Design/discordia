# examples/advanced_bot.py
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "discordia",
# ]
# ///
"""Advanced Discordia bot with custom configuration."""

from __future__ import annotations

from discordia import Bot, Settings, setup_logging


def main() -> None:
    """Run bot with custom configuration."""

    setup_logging(level="DEBUG")

    settings = Settings(
        discord_token="your-token",
        server_id=123456789,
        anthropic_api_key="your-key",
        log_category_name="Logs",
        llm_model="claude-sonnet-4-20250514",
        message_context_limit=50,
        database_url="sqlite+aiosqlite:///custom.db",
        jsonl_path="custom_backup.jsonl",
    )

    bot = Bot(settings)
    bot.run()


if __name__ == "__main__":
    main()
