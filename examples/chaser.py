"""Run a simple "chaser" pattern across all 8 relays.

Usage::

    python examples/chaser.py 192.168.200.105 --delay 0.2 --loops 3
"""

from __future__ import annotations

import argparse
import time

from esp32_relais_x8 import NUM_RELAYS, RelayBoard


def main() -> None:
    parser = argparse.ArgumentParser(description="Chaser demo")
    parser.add_argument("host", help="Board hostname or IP address")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds per step")
    parser.add_argument("--loops", type=int, default=2, help="Number of full loops")
    args = parser.parse_args()

    board = RelayBoard(args.host)
    board.all_off()
    try:
        for _ in range(args.loops):
            for i in range(NUM_RELAYS):
                board.turn_on(i)
                time.sleep(args.delay)
                board.turn_off(i)
    finally:
        board.all_off()


if __name__ == "__main__":
    main()
