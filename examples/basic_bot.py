#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "discordia @ git+https://github.com/Bullish-Design/discordia.git@v3",
# ]
# ///
# examples/basic_bot.py
"""Basic bot example without LLM integration."""
from __future__ import annotations

from discordia import Bot, LoggingHandler, ServerTemplate, Settings, TextChannelTemplate


def main() -> None:
    print(f"\nStarting basic bot script!\n")
    settings = Settings()  # Loads from .env or environment
    print(f"Using server ID: {settings.server_id}\n")
    template = ServerTemplate(
        uncategorized_channels=[
            TextChannelTemplate(name="general", topic="General chat"),
            #TextChannelTemplate(name="bot-commands", topic="Bot commands go here"),
        ]
    )

    handlers = [LoggingHandler()]
    print(f"Registered handlers: {[handler.__class__.__name__ for handler in handlers]}\n")
    print(f"Running bot...\n")
    bot = Bot(settings=settings, template=template, handlers=handlers)
    print(f"Getting bot ready to connect...\n")
    bot.run()


if __name__ == "__main__":
    main()
