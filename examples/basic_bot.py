# examples/basic_bot.py
from __future__ import annotations

"""Basic bot with logging.

This example demonstrates wiring a bot with the built-in LoggingHandler.
"""

from pydantic import SecretStr

from discordia import Bot, BotConfig, LoggingHandler


def main() -> None:
    config = BotConfig(
        discord_token=SecretStr("your_token_here"),
        server_id=123456789,
    )

    bot = Bot(
        config=config,
        handlers=[LoggingHandler()],
    )

    bot.run()


if __name__ == "__main__":
    main()
