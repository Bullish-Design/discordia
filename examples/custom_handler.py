# examples/custom_handler.py
from __future__ import annotations

"""Bot with a custom handler."""

from pydantic import BaseModel, SecretStr

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
    config = BotConfig(
        discord_token=SecretStr("your_token_here"),
        server_id=123456789,
    )

    bot = Bot(
        config=config,
        handlers=[PingHandler()],
    )

    bot.run()


if __name__ == "__main__":
    main()
