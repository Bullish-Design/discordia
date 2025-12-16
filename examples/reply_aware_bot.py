# examples/reply_aware_bot.py
from __future__ import annotations

"""Bot that handles message replies.

Setup:
    1. Copy .env.example to .env
    2. Update DISCORDIA_DISCORD_TOKEN and DISCORDIA_SERVER_ID
    3. Run: python examples/reply_aware_bot.py
    4. Reply to any message with "!context" to see who you're replying to
"""

from pydantic import BaseModel

from discordia import Bot, BotConfig, Handler, MessageContext


class ReplyConfig(BaseModel):
    pass


class ReplyHandler(Handler[ReplyConfig]):
    def __init__(self) -> None:
        super().__init__(config=ReplyConfig())

    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.content == "!context"

    async def handle(self, ctx: MessageContext) -> str | None:
        replied_msg = await ctx.get_replied_message()
        
        if replied_msg:
            author = await ctx.store.get_user(replied_msg.author_id)
            author_name = author.username if author else "unknown"
            return f"📎 You're replying to {author_name}: '{replied_msg.content[:50]}...'"
        else:
            return "💬 This is not a reply to another message"


def main() -> None:
    config = BotConfig.from_env()

    bot = Bot(
        config=config,
        handlers=[ReplyHandler()],
    )

    bot.run()


if __name__ == "__main__":
    main()
