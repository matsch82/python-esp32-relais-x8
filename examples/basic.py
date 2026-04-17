"""Minimal demo against a real board.

Run with::

    python examples/basic.py 192.168.200.105
"""

from __future__ import annotations

import sys
import time

from esp32_relais_x8 import RelayBoard


def main(host: str) -> None:
    board = RelayBoard(host)

    state = board.get_state()
    print(f"Uptime: {state.uptime_seconds}s")
    print(f"Relays: {state.relays()}")
    print(f"LED on: {state.led()}")

    print("Toggling relay 0 twice ...")
    board.toggle_relay(0)
    time.sleep(0.5)
    board.toggle_relay(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: basic.py <host>", file=sys.stderr)
        raise SystemExit(2)
    main(sys.argv[1])
