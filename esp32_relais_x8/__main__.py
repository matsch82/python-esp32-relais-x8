"""Tiny command-line interface for the ESP32 Relay X8 board.

Usage examples::

    python -m esp32_relais_x8 --host 192.168.200.105 state
    python -m esp32_relais_x8 --host 192.168.200.105 on 0
    python -m esp32_relais_x8 --host 192.168.200.105 off 3
    python -m esp32_relais_x8 --host 192.168.200.105 toggle 5
    python -m esp32_relais_x8 --host 192.168.200.105 all-off
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .client import NUM_RELAYS, RelayBoard, RelayBoardError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="esp32_relais_x8",
        description="Control an ESP32 Relay X8 board over HTTP.",
    )
    parser.add_argument("--host", required=True, help="Board hostname or IP address")
    parser.add_argument("--port", type=int, default=80, help="HTTP port (default: 80)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds (default: 5)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("state", help="Print the current board state as JSON")

    p_on = sub.add_parser("on", help="Turn a relay on")
    p_on.add_argument("index", type=int, help=f"Relay index 0..{NUM_RELAYS - 1}")

    p_off = sub.add_parser("off", help="Turn a relay off")
    p_off.add_argument("index", type=int, help=f"Relay index 0..{NUM_RELAYS - 1}")

    p_tog = sub.add_parser("toggle", help="Toggle a relay")
    p_tog.add_argument("index", type=int, help=f"Relay index 0..{NUM_RELAYS - 1}")

    sub.add_parser("all-on", help="Turn all relays on")
    sub.add_parser("all-off", help="Turn all relays off")

    p_led = sub.add_parser("led", help="Control the on-board LED")
    p_led.add_argument("action", choices=["on", "off", "toggle"])

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    board = RelayBoard(args.host, port=args.port, timeout=args.timeout)

    try:
        if args.command == "state":
            state = board.get_state()
            json.dump(state.raw, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "on":
            board.turn_on(args.index)
        elif args.command == "off":
            board.turn_off(args.index)
        elif args.command == "toggle":
            board.toggle_relay(args.index)
        elif args.command == "all-on":
            board.all_on()
        elif args.command == "all-off":
            board.all_off()
        elif args.command == "led":
            if args.action == "on":
                board.set_led(True)
            elif args.action == "off":
                board.set_led(False)
            else:
                board.toggle_led()
    except RelayBoardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
