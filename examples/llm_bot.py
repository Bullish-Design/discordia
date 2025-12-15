#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "discordia @ git+https://github.com/Bullish-Design/discordia.git@v3",
#     "pygentic @ git+https://github.com/Bullish-Design/PyGentic.git",
#     "python-dotenv>=1.0.0",
# ]
# ///
# examples/llm_bot.py
"""Bot example with LLM integration using PyGentic."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Ensure src is in sys.path for imports
# Add project root to path for examples imports
root_path = Path(__file__).parent.parent
print(f"\nAdding project root to sys.path: {root_path}\n")
sys.path.insert(0, str(root_path))



from pydantic import SecretStr

from discordia import Bot, CategoryTemplate, ServerTemplate, Settings, TextChannelTemplate



from examples.llm_handlers import LLMHandler
from examples.patterns import WeekDayPattern


def main() -> None:
    print(f"\nStarting LLM bot script!\n")
    settings = Settings()
    
    api_key = SecretStr(os.environ.get("OPENAI_API_KEY", ""))
    print(f"API key = {api_key.get_secret_value()}\n")
    template = ServerTemplate(
        categories=[
            CategoryTemplate(
                name="Logs",
                channels=[],  # Channels added via pattern
            ),
        ],
        patterns=[
            WeekDayPattern(weeks_ahead=0, weeks_behind=0, topic="Logs"),
        ],
    )
    
    print(f"Loaded server template with patterns:\n{template}\n")
    handlers = [
        LLMHandler(
            api_key=api_key,
            provider="openai",
            model="gpt-5-nano",
            channel_pattern=r"^\d{4}-\d{2}-0[1-7]$",
        ),
    ]
    print(f"Registered handlers: {[handler.__class__.__name__ for handler in handlers]}\n")

    bot = Bot(settings=settings, template=template, handlers=handlers)
    print(f"Getting bot ready to connect...\n")
    bot.run()


if __name__ == "__main__":
    main()
