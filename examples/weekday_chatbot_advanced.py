# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "discordia",
#     "python-dotenv",
# ]
# ///

"""
Discordia Advanced Week-Day Chatbot
====================================

Uses WeekDayPattern to auto-generate and maintain a rolling window of WW-DD channels.
Maintains last week plus current week's channels.

Run: uv run weekday_chatbot_advanced.py
"""

from __future__ import annotations

import logging

from discordia import Bot, Settings
from discordia.templates import CategoryTemplate, ServerTemplate

# Import custom pattern and handler (copy to your project)
from weekday_handler import WeekDayHandler
from weekday_pattern import WeekDayPattern

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_rolling_weekday_template() -> ServerTemplate:
    """Create template with automatic WW-DD channel management."""
    return ServerTemplate(
        categories=[
            CategoryTemplate(
                name="Log",
                position=0,
                channels=[],
            )
        ],
        patterns=[
            WeekDayPattern(
                weeks_ahead=0,  # Current week only
                weeks_behind=1,  # Plus last week
                topic="Weekly log channel",
            )
        ],
    )


def main() -> None:
    settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4",
        llm_temperature=0.7,
        auto_reconcile=True,
        reconcile_interval=300,
        message_context_limit=20,
    )

    template = create_rolling_weekday_template()
    
    handler = WeekDayHandler(
        api_key=settings.anthropic_api_key,
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )

    bot = Bot(settings=settings, template=template, handlers=[handler])

    logger.info("Starting week-day chatbot with 2-week rolling window")
    bot.run()


if __name__ == "__main__":
    main()
