# examples/basic_bot.py
#!/usr/bin/env python3
"""Basic bot example."""

from __future__ import annotations

from discordia import Bot, Settings, setup_logging


def main() -> None:
    """Run the bot."""

    setup_logging(level="INFO")
    settings = Settings()
    bot = Bot(settings)
    bot.run()


if __name__ == "__main__":
    main()
