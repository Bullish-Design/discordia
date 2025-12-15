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
    settings = Settings()  # Loads from .env or environment

    template = ServerTemplate(
        uncategorized_channels=[
            TextChannelTemplate(name="general", topic="General chat"),
            TextChannelTemplate(name="bot-commands", topic="Bot commands go here"),
        ]
    )

    handlers = [LoggingHandler()]

    bot = Bot(settings=settings, template=template, handlers=handlers)
    bot.run()


if __name__ == "__main__":
    main()
