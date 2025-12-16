# examples/echo_bot.py
from __future__ import annotations

"""Bot with an echo handler."""

from pydantic import SecretStr

from discordia import Bot, BotConfig, EchoConfig, EchoHandler


def main() -> None:
    config = BotConfig(
        discord_token=SecretStr("your_token_here"),
        server_id=123456789,
    )

    bot = Bot(
        config=config,
        handlers=[EchoHandler(config=EchoConfig(prefix="echo:"))],
    )

    bot.run()


if __name__ == "__main__":
    main()
