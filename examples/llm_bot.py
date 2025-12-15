#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "discordia",
#     "pygentic @ git+https://github.com/Bullish-Design/PyGentic.git",
# ]
# ///
# examples/llm_bot.py
"""Bot example with LLM integration using PyGentic."""
from __future__ import annotations

import os

from pydantic import SecretStr

from discordia import Bot, CategoryTemplate, ServerTemplate, Settings, TextChannelTemplate

from examples.llm_handlers import LLMHandler
from examples.patterns import WeekDayPattern


def main() -> None:
    settings = Settings()

    api_key = SecretStr(os.environ.get("ANTHROPIC_API_KEY", ""))

    template = ServerTemplate(
        categories=[
            CategoryTemplate(
                name="Daily Logs",
                channels=[],  # Channels added via pattern
            ),
        ],
        patterns=[
            WeekDayPattern(weeks_ahead=1, weeks_behind=2, topic="Daily log"),
        ],
    )

    handlers = [
        LLMHandler(
            api_key=api_key,
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            channel_pattern=r"^\d{4}-\d{2}-0[1-7]$",
        ),
    ]

    bot = Bot(settings=settings, template=template, handlers=handlers)
    bot.run()


if __name__ == "__main__":
    main()
