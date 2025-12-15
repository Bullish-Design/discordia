# examples/basic_bot.py
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "discordia",
# ]
# ///
"""Basic Discordia bot example.

This example demonstrates the minimal setup needed to run a Discordia bot.
The bot will:
1. Connect to Discord
2. Create daily log channels in YYYY-MM-DD format
3. Respond to messages in log channels using Claude
4. Persist all interactions to SQLite and JSONL
"""

from __future__ import annotations

from discordia import Bot, Settings, setup_logging


def main() -> None:
    """Run the Discordia bot."""

    setup_logging(level="INFO")
    settings = Settings()

    bot = Bot(settings)

    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
