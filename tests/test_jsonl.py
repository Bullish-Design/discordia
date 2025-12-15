# tests/test_jsonl.py
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from discordia.exceptions import JSONLError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser
from discordia.persistence.jsonl import JSONLWriter


@pytest.fixture
def temp_jsonl_file() -> str:
    """Create a temporary JSONL file path for testing."""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        filepath = f.name
    yield filepath
    Path(filepath).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_write_category(temp_jsonl_file: str) -> None:
    """Category can be written to JSONL."""

    writer = JSONLWriter(temp_jsonl_file)
    category = DiscordCategory(id=1, name="Test", server_id=100)

    await writer.write_category(category)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["type"] == "category"
        assert data["data"]["id"] == 1
        assert data["data"]["name"] == "Test"


@pytest.mark.asyncio
async def test_write_channel(temp_jsonl_file: str) -> None:
    """Channel can be written to JSONL."""

    writer = JSONLWriter(temp_jsonl_file)
    channel = DiscordTextChannel(id=2, name="test-channel", server_id=100)

    await writer.write_channel(channel)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["type"] == "channel"
        assert data["data"]["name"] == "test-channel"


@pytest.mark.asyncio
async def test_write_message(temp_jsonl_file: str) -> None:
    """Message can be written to JSONL."""

    writer = JSONLWriter(temp_jsonl_file)
    message = DiscordMessage(
        id=3,
        content="Hello",
        author_id=10,
        channel_id=20,
        timestamp=datetime.utcnow(),
    )

    await writer.write_message(message)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["type"] == "message"
        assert data["data"]["content"] == "Hello"


@pytest.mark.asyncio
async def test_write_user(temp_jsonl_file: str) -> None:
    """User can be written to JSONL."""

    writer = JSONLWriter(temp_jsonl_file)
    user = DiscordUser(id=4, username="testuser")

    await writer.write_user(user)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["type"] == "user"
        assert data["data"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_multiple_writes_append(temp_jsonl_file: str) -> None:
    """Multiple writes append to file without overwriting."""

    writer = JSONLWriter(temp_jsonl_file)
    cat1 = DiscordCategory(id=1, name="Cat1", server_id=100)
    cat2 = DiscordCategory(id=2, name="Cat2", server_id=100)

    await writer.write_category(cat1)
    await writer.write_category(cat2)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 2
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])
    assert data1["data"]["name"] == "Cat1"
    assert data2["data"]["name"] == "Cat2"


@pytest.mark.asyncio
async def test_read_all_entries(temp_jsonl_file: str) -> None:
    """read_all returns all entries in written order."""

    writer = JSONLWriter(temp_jsonl_file)
    cat = DiscordCategory(id=1, name="Test", server_id=100)
    user = DiscordUser(id=2, username="test")

    await writer.write_category(cat)
    await writer.write_user(user)

    entries = await writer.read_all()
    assert len(entries) == 2
    assert entries[0]["type"] == "category"
    assert entries[1]["type"] == "user"


@pytest.mark.asyncio
async def test_read_all_empty_file(temp_jsonl_file: str) -> None:
    """read_all returns empty list for an empty file."""

    writer = JSONLWriter(temp_jsonl_file)
    entries = await writer.read_all()
    assert entries == []


@pytest.mark.asyncio
async def test_read_all_nonexistent_file(tmp_path: Path) -> None:
    """read_all returns empty list for a non-existent file."""

    writer = JSONLWriter(str(tmp_path / "does_not_exist.jsonl"))
    entries = await writer.read_all()
    assert entries == []


@pytest.mark.asyncio
async def test_each_entry_on_separate_line(temp_jsonl_file: str) -> None:
    """Each write creates exactly one JSON object per line."""

    writer = JSONLWriter(temp_jsonl_file)

    for i in range(1, 6):
        cat = DiscordCategory(id=i, name=f"Cat{i}", server_id=100)
        await writer.write_category(cat)

    with open(temp_jsonl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 5

    for line in lines:
        data = json.loads(line)
        assert "type" in data
        assert "data" in data


@pytest.mark.asyncio
async def test_write_wraps_errors_as_jsonlerror(tmp_path: Path) -> None:
    """Write failures are wrapped as JSONLError."""

    # Use a directory path to force aiofiles.open to fail.
    dir_path = tmp_path / "a_directory"
    dir_path.mkdir()
    writer = JSONLWriter(str(dir_path))

    category = DiscordCategory(id=1, name="Test", server_id=100)

    with pytest.raises(JSONLError):
        await writer.write_category(category)
