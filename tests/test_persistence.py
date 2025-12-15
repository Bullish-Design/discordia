# tests/test_persistence.py
from __future__ import annotations

import json

import pytest

from discordia.exceptions import JSONLError
from discordia.persistence.jsonl import JSONLBackend
from discordia.persistence.memory import MemoryBackend
from discordia.state.models import Category, User


@pytest.mark.asyncio
async def test_memory_backend_write():
    """MemoryBackend can store entities."""
    backend = MemoryBackend()
    category = Category(
        id=123456789012345678,
        name="Test Category",
        server_id=987654321098765432,
    )

    await backend.write(category, "category")

    entries = await backend.read_all()
    assert len(entries) == 1
    assert entries[0]["type"] == "category"
    assert entries[0]["data"]["name"] == "Test Category"


@pytest.mark.asyncio
async def test_memory_backend_multiple_entities():
    """MemoryBackend can store multiple entities."""
    backend = MemoryBackend()

    category = Category(
        id=123456789012345678,
        name="Category",
        server_id=987654321098765432,
    )
    user = User(id=111222333444555666, username="TestUser")

    await backend.write(category, "category")
    await backend.write(user, "user")

    entries = await backend.read_all()
    assert len(entries) == 2
    assert entries[0]["type"] == "category"
    assert entries[1]["type"] == "user"


@pytest.mark.asyncio
async def test_memory_backend_read_all_empty():
    """MemoryBackend returns empty list when no entries."""
    backend = MemoryBackend()
    entries = await backend.read_all()
    assert entries == []


@pytest.mark.asyncio
async def test_jsonl_backend_write(tmp_path):
    """JSONLBackend writes entities to file."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    category = Category(
        id=123456789012345678,
        name="Test Category",
        server_id=987654321098765432,
    )
    await backend.write(category, "category")

    assert filepath.exists()
    content = filepath.read_text()
    assert "Test Category" in content


@pytest.mark.asyncio
async def test_jsonl_backend_read_all(tmp_path):
    """JSONLBackend reads entities from file."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    category = Category(
        id=123456789012345678,
        name="Category",
        server_id=987654321098765432,
    )
    await backend.write(category, "category")

    entries = await backend.read_all()
    assert len(entries) == 1
    assert entries[0]["type"] == "category"
    assert entries[0]["data"]["name"] == "Category"


@pytest.mark.asyncio
async def test_jsonl_backend_read_nonexistent_file(tmp_path):
    """JSONLBackend returns empty list for nonexistent file."""
    filepath = tmp_path / "nonexistent.jsonl"
    backend = JSONLBackend(str(filepath))

    entries = await backend.read_all()
    assert entries == []


@pytest.mark.asyncio
async def test_jsonl_backend_multiple_writes(tmp_path):
    """JSONLBackend appends multiple entities."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    category = Category(
        id=123456789012345678,
        name="Category",
        server_id=987654321098765432,
    )
    user = User(id=111222333444555666, username="TestUser")

    await backend.write(category, "category")
    await backend.write(user, "user")

    entries = await backend.read_all()
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_jsonl_backend_preserves_order(tmp_path):
    """JSONLBackend preserves write order."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    for i in range(5):
        user = User(id=100000000000000000 + i, username=f"User{i}")
        await backend.write(user, "user")

    entries = await backend.read_all()
    assert len(entries) == 5
    assert entries[0]["data"]["username"] == "User0"
    assert entries[4]["data"]["username"] == "User4"


@pytest.mark.asyncio
async def test_jsonl_backend_format_validation(tmp_path):
    """JSONLBackend writes valid JSON lines."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    category = Category(
        id=123456789012345678,
        name="Test",
        server_id=987654321098765432,
    )
    await backend.write(category, "category")

    with open(filepath) as f:
        line = f.readline()
        data = json.loads(line)
        assert "type" in data
        assert "data" in data


@pytest.mark.asyncio
async def test_jsonl_backend_handles_special_characters(tmp_path):
    """JSONLBackend handles special characters in data."""
    filepath = tmp_path / "test.jsonl"
    backend = JSONLBackend(str(filepath))

    user = User(id=123456789012345678, username="Test\nUser\"Quote")
    await backend.write(user, "user")

    entries = await backend.read_all()
    assert entries[0]["data"]["username"] == "Test\nUser\"Quote"
