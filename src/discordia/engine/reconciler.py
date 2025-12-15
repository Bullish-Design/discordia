# src/discordia/engine/reconciler.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discordia.exceptions import ReconciliationError
from discordia.templates.channel import TextChannelTemplate
from discordia.templates.server import ServerTemplate

if TYPE_CHECKING:
    from discordia.state.protocol import StateStore
    from discordia.state.registry import EntityRegistry
    from discordia.types import DiscordSnowflake

logger = logging.getLogger("discordia.engine.reconciler")


class Reconciler:
    """Reconciles template definitions to Discord reality."""

    def __init__(self, store: StateStore, registry: EntityRegistry, server_id: DiscordSnowflake) -> None:
        self.store = store
        self.registry = registry
        self.server_id = server_id

    async def reconcile(self, guild: Any, template: ServerTemplate) -> None:
        """Sync template to Discord."""
        try:
            resolved = template.resolve_patterns()
            print(f"\n\nStarting reconciliation for server ID {self.server_id}")

            for category_template in resolved.categories:
                print(f"\nReconciling category {category_template.name}")
                await self._reconcile_category(guild, category_template)

            for channel_template in resolved.uncategorized_channels:
                print(f"\nReconciling channel {channel_template.name}")
                await self._reconcile_channel(guild, channel_template, category_id=None)

            logger.info("Reconciliation complete")
        except Exception as e:
            logger.error("Reconciliation failed: %s", e, exc_info=True)
            raise ReconciliationError("Failed to reconcile template", cause=e) from e

    async def _reconcile_category(self, guild: Any, template: Any) -> None:
        """Ensure category exists."""
        try:
            category = await self.registry.get_category_by_name(template.name, self.server_id)
            logger.debug("Category %s exists", template.name)
        except Exception:
            discord_category = await guild.create_category(name=template.name)
            from discordia.state.models import Category

            category = Category(
                id=int(discord_category.id),
                name=str(discord_category.name),
                server_id=self.server_id,
                position=template.position or 0,
            )
            await self.store.save_category(category)
            logger.info("Created category %s", template.name)

        for channel_template in template.channels:
            await self._reconcile_channel(guild, channel_template, category_id=category.id)

    async def _reconcile_channel(self, guild: Any, template: Any, category_id: int | None) -> None:
        """Ensure channel exists."""
        try:
            await self.registry.get_channel_by_name(template.name, self.server_id)
            logger.debug("Channel %s exists", template.name)
        except Exception:
            if isinstance(template, TextChannelTemplate):
                discord_channel = await guild.create_text_channel(
                    name=template.name, parent_id=category_id, topic=template.topic
                )
                from discordia.state.models import Channel

                channel = Channel(
                    id=int(discord_channel.id),
                    name=str(discord_channel.name),
                    category_id=category_id,
                    server_id=self.server_id,
                    position=template.position or 0,
                    topic=template.topic,
                )
                await self.store.save_channel(channel)
                logger.info("Created channel %s", template.name)


__all__ = ["Reconciler"]
