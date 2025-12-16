# tests/test_plugins.py
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from discordia.context import MessageContext
from discordia.plugins import Plugin
from discordia.state import Channel, MemoryState, User


class ExamplePlugin:
    """Test plugin implementation."""

    def __init__(self) -> None:
        self.ready_called = False
        self.message_count = 0

    async def on_ready(self, bot: object, guild: object) -> None:
        self.ready_called = True

    async def on_message(self, bot: object, ctx: MessageContext) -> None:
        self.message_count += 1


@pytest.mark.asyncio
async def test_plugin_on_ready() -> None:
    plugin = ExamplePlugin()
    await plugin.on_ready(None, None)
    assert plugin.ready_called is True


@pytest.mark.asyncio
async def test_plugin_on_message() -> None:
    plugin = ExamplePlugin()
    ctx = MessageContext(
        message_id=999,
        content="test",
        author=User(id=111, username="Alice"),
        channel=Channel(id=789, name="general", server_id=456),
        store=MemoryState(),
        timestamp=datetime.now(tz=UTC),
    )
    await plugin.on_message(None, ctx)
    assert plugin.message_count == 1


def test_plugin_protocol_runtime_checkable() -> None:
    plugin = ExamplePlugin()
    assert isinstance(plugin, Plugin)
