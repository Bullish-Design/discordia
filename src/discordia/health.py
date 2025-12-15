# src/discordia/health.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discordia.bot import Bot

logger = logging.getLogger("discordia.health")


async def health_check(bot: Bot) -> dict[str, bool]:
    """Check bot component health.

    This utility is intentionally conservative: it avoids raising and instead reports
    individual component status.

    Args:
        bot: Bot instance to check.

    Returns:
        Dict of component health status.
    """

    status: dict[str, bool] = {
        "database": False,
        "client": False,
        "managers": False,
    }

    try:
        await bot.db.initialize()
        status["database"] = True
    except Exception as e:
        logger.error("Database health check failed: %s", e, exc_info=True)

    try:
        status["client"] = bool(getattr(bot.client, "is_ready", False))
    except Exception as e:
        logger.error("Client health check failed: %s", e, exc_info=True)

    try:
        status["managers"] = all(
            [
                bot.category_manager is not None,
                bot.channel_manager is not None,
                bot.message_handler is not None,
            ]
        )
    except Exception as e:
        logger.error("Manager health check failed: %s", e, exc_info=True)

    return status


__all__ = ["health_check"]
