# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "discordia @ git+https://github.com/Bullish-Design/discordia.git",
#     "python-dotenv",
# ]
# ///

"""
Discordia Week-Day Chatbot Example
===================================

Creates channels named WW-DD (ISO week number, day 01-07 with Monday as 01).
Responds to all messages in the current week-day channel using OpenAI.

Setup: Create .env with DISCORD_TOKEN, SERVER_ID, OPENAI_API_KEY
Run: uv run weekday_chatbot.py
"""

from __future__ import annotations

import logging
from datetime import date

from discordia import Bot, Settings
from discordia.templates import CategoryTemplate, ServerTemplate, TextChannelTemplate

# Import custom handler (you'll need to copy this to your project)
from weekday_handler import WeekDayHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_weekday_template() -> ServerTemplate:
    """Create template with today's WW-DD channel."""
    today = date.today()
    iso_cal = today.isocalendar()
    channel_name = f"{iso_cal.week:02d}-{iso_cal.weekday:02d}"

    return ServerTemplate(
        categories=[
            CategoryTemplate(
                name="Log",
                position=0,
                channels=[
                    TextChannelTemplate(
                        name=channel_name,
                        topic=f"Week {iso_cal.week}, Day {iso_cal.weekday} (Monday=01)",
                        position=0,
                    )
                ],
            )
        ],
    )


def main() -> None:
    settings = Settings(
        llm_provider="openai",
        llm_model="gpt-5-nano",
        llm_temperature=0.7,
        auto_reconcile=True,
        reconcile_interval=300,
        message_context_limit=20,
    )

    template = create_weekday_template()
    
    handler = WeekDayHandler(
        api_key=settings.anthropic_api_key,
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )

    bot = Bot(settings=settings, template=template, handlers=[handler])

    today = date.today()
    iso_cal = today.isocalendar()
    logger.info("Starting chatbot for channel: %02d-%02d", iso_cal.week, iso_cal.weekday)
    bot.run()


if __name__ == "__main__":
    main()
