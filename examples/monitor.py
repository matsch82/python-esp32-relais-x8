"""Continuously print the board state once a second.

Usage::

    python examples/monitor.py 192.168.200.105
"""

from __future__ import annotations

import argparse
import time

from esp32_relais_x8 import RelayBoard, RelayBoardError


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll and print board state")
    parser.add_argument("host", help="Board hostname or IP address")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between polls")
    args = parser.parse_args()

    board = RelayBoard(args.host)
    try:
        while True:
            try:
                state = board.get_state()
            except RelayBoardError as exc:
                print(f"error: {exc}")
            else:
                relays = "".join("1" if state.relay(i) else "0" for i in range(8))
                print(f"up={state.uptime_seconds:>6}s  relays={relays}  led={int(state.led())}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
