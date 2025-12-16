# examples/echo_bot.py
from __future__ import annotations

"""Bot with an echo handler.

Setup:
    1. Copy .env.example to .env
    2. Update DISCORDIA_DISCORD_TOKEN and DISCORDIA_SERVER_ID
    3. Run: python examples/echo_bot.py
    4. Send a message like "echo: Hello world!" to test
"""

from discordia import Bot, BotConfig, EchoConfig, EchoHandler


def main() -> None:
    config = BotConfig.from_env()

    bot = Bot(
        config=config,
        handlers=[EchoHandler(config=EchoConfig(prefix="echo:"))],
    )

    bot.run()


if __name__ == "__main__":
    main()
