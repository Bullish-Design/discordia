# examples/custom_handler.py
from __future__ import annotations

"""Bot with a custom handler.

Setup:
    1. Copy .env.example to .env
    2. Update DISCORDIA_DISCORD_TOKEN and DISCORDIA_SERVER_ID
    3. Run: python examples/custom_handler.py
    4. Send "!ping" to test
"""

from pydantic import BaseModel

from discordia import Bot, BotConfig, Handler, MessageContext


class PingConfig(BaseModel):
    response: str = "Pong!"


class PingHandler(Handler[PingConfig]):
    def __init__(self) -> None:
        super().__init__(config=PingConfig())

    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.content == "!ping"

    async def handle(self, ctx: MessageContext) -> str | None:
        return self.config.response


def main() -> None:
    config = BotConfig.from_env()

    bot = Bot(
        config=config,
        handlers=[PingHandler()],
    )

    bot.run()


if __name__ == "__main__":
    main()
