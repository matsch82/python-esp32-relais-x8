"""Unit tests for the :mod:`esp32_relais_x8` package.

The tests spin up a tiny in-process HTTP server that mimics the ESP32
Relay X8 board's ``/json`` and ``/cmd`` endpoints. This keeps the test
suite self-contained (no real hardware or external network required).
"""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Tuple
from urllib.parse import parse_qs, urlparse

from esp32_relais_x8 import (
    LED_INDEX,
    NUM_RELAYS,
    BoardState,
    RelayBoard,
    RelayBoardError,
)


# --------------------------------------------------------------------- helpers


class _MockBoardHandler(BaseHTTPRequestHandler):
    """HTTP handler emulating the ESP32 Relay X8 API."""

    # Populated per-server in :meth:`_MockBoard.start`.
    state: dict
    requests: List[Tuple[str, dict]]

    def log_message(self, *_args, **_kwargs) -> None:  # silence test output
        pass

    def do_GET(self) -> None:  # noqa: N802 — required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        self.server.requests.append((parsed.path, query))

        if parsed.path == "/json":
            body = json.dumps(self.server.state).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/cmd":
            if "cb" in query and "v" in query:
                pin = query["cb"]
                self.server.state[pin] = int(query["v"])
            elif "toggle" in query:
                pin = f"outputPin{int(query['toggle'])}"
                self.server.state[pin] = 0 if self.server.state.get(pin) else 1
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()


class _MockBoard:
    """Context manager wrapping a :class:`ThreadingHTTPServer`."""

    def __enter__(self) -> "_MockBoard":
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _MockBoardHandler)
        self.server.state = {
            "ss": 42,
            "inputPin0": 1,
            **{f"outputPin{i}": 0 for i in range(NUM_RELAYS + 1)},
        }
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address
        return self

    def __exit__(self, *_exc) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def client(self) -> RelayBoard:
        return RelayBoard(self.host, port=self.port, timeout=2.0)


# ------------------------------------------------------------------------ tests


class BoardStateTests(unittest.TestCase):
    def test_from_json_classifies_pins(self) -> None:
        state = BoardState.from_json(
            {
                "ss": 10,
                "inputPin0": 1,
                "outputPin0": 0,
                "outputPin1": 1,
                "outputPin8": 1,
                "junk": "ignored",
            }
        )
        self.assertEqual(state.uptime_seconds, 10)
        self.assertEqual(state.inputs, {"inputPin0": 1})
        self.assertEqual(
            state.outputs,
            {"outputPin0": 0, "outputPin1": 1, "outputPin8": 1},
        )
        self.assertFalse(state.relay(0))
        self.assertTrue(state.relay(1))
        self.assertTrue(state.led())
        self.assertEqual(state.relays()[1], True)


class RelayBoardTests(unittest.TestCase):
    def test_get_state_returns_board_state(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            state = board.get_state()
            self.assertIsInstance(state, BoardState)
            self.assertEqual(state.uptime_seconds, 42)
            self.assertEqual(state.relays(), {i: False for i in range(NUM_RELAYS)})

    def test_turn_on_and_off(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            board.turn_on(0)
            self.assertEqual(mock.server.state["outputPin0"], 1)
            board.turn_off(0)
            self.assertEqual(mock.server.state["outputPin0"], 0)

    def test_toggle_relay_flips_state(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            self.assertFalse(board.get_state().relay(3))
            board.toggle_relay(3)
            self.assertTrue(board.get_state().relay(3))
            board.toggle_relay(3)
            self.assertFalse(board.get_state().relay(3))

    def test_all_on_and_all_off(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            board.all_on()
            relays = board.get_state().relays()
            self.assertTrue(all(relays.values()))
            board.all_off()
            relays = board.get_state().relays()
            self.assertFalse(any(relays.values()))

    def test_led_controls_output_8(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            board.set_led(True)
            self.assertEqual(mock.server.state[f"outputPin{LED_INDEX}"], 1)
            board.toggle_led()
            self.assertEqual(mock.server.state[f"outputPin{LED_INDEX}"], 0)

    def test_uses_cb_parameter_for_set_relay(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            board.set_relay(2, True)
            cmd_requests = [r for r in mock.server.requests if r[0] == "/cmd"]
            self.assertEqual(len(cmd_requests), 1)
            _, query = cmd_requests[0]
            self.assertEqual(query, {"cb": "outputPin2", "v": "1"})

    def test_invalid_relay_index_raises(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            for bad in (-1, NUM_RELAYS, 99, "0", 1.5):
                with self.subTest(bad=bad):
                    with self.assertRaises(ValueError):
                        board.set_relay(bad, True)  # type: ignore[arg-type]

    def test_invalid_output_index_raises(self) -> None:
        with _MockBoard() as mock:
            board = mock.client()
            with self.assertRaises(ValueError):
                board.toggle_output(LED_INDEX + 1)

    def test_network_error_raises_relayboard_error(self) -> None:
        # Port 1 is almost always closed on local machines.
        board = RelayBoard("127.0.0.1", port=1, timeout=0.5)
        with self.assertRaises(RelayBoardError):
            board.get_state()

    def test_host_accepts_scheme_prefix(self) -> None:
        board = RelayBoard("http://192.168.0.10/", port=81)
        self.assertEqual(board.base_url, "http://192.168.0.10:81")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
