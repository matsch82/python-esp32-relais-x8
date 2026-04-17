"""Python client for the ESP32 Relay X8 board.

The board exposes a very small HTTP API that this package wraps in a
convenient Python interface.
"""

from .client import (
    NUM_RELAYS,
    LED_INDEX,
    BoardState,
    RelayBoard,
    RelayBoardError,
)

__all__ = [
    "NUM_RELAYS",
    "LED_INDEX",
    "BoardState",
    "RelayBoard",
    "RelayBoardError",
]

__version__ = "0.1.0"
