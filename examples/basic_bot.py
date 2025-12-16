# examples/basic_bot.py
from __future__ import annotations

"""Basic bot with logging.

This example demonstrates wiring a bot with the built-in LoggingHandler.

Setup:
    1. Copy .env.example to .env
    2. Update DISCORDIA_DISCORD_TOKEN and DISCORDIA_SERVER_ID
    3. Run: python examples/basic_bot.py
"""

from discordia import Bot, BotConfig, LoggingHandler


def main() -> None:
    config = BotConfig.from_env()
    # logging_config =

    bot = Bot(
        config=config,
        handlers=[LoggingHandler()],
    )

    bot.run()


if __name__ == "__main__":
    main()
