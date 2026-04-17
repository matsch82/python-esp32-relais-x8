"""HTTP client for the ESP32 Relay X8 board.

The board under test (firmware version 24.01) serves three relevant
endpoints over plain HTTP:

* ``GET /json``
      Returns a JSON object with the current state of the board, e.g.::

          {"ss": 389, "inputPin0": 1,
           "outputPin0": 0, ..., "outputPin8": 0}

      ``ss`` is the uptime in seconds, ``inputPinN`` reflects digital
      input pins, and ``outputPinN`` reflects the 8 relays (0..7) plus
      an on-board LED (8).

* ``GET /cmd?cb=outputPin<N>&v=<0|1>``
      Sets output ``N`` to the requested level (0 = off, 1 = on).

* ``GET /cmd?toggle=<N>``
      Toggles output ``N`` (0..7 for the relays, 8 for the on-board
      LED).

This module wraps those endpoints in a small, typed client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import urllib.parse
import urllib.request
import json


#: Number of physical relays on the board.
NUM_RELAYS: int = 8

#: Index of the on-board LED when addressed via ``outputPinN``/``toggle``.
LED_INDEX: int = 8

#: Default timeout (in seconds) for HTTP requests.
DEFAULT_TIMEOUT: float = 5.0


class RelayBoardError(RuntimeError):
    """Raised when communication with the board fails."""


@dataclass
class BoardState:
    """Snapshot of the board state returned by ``GET /json``.

    Attributes:
        uptime_seconds: Seconds since the board booted (``ss``).
        inputs: Mapping of input pin name (e.g. ``inputPin0``) to its
            value (0 or 1).
        outputs: Mapping of output pin name (e.g. ``outputPin0``) to its
            value (0 or 1).  Outputs 0..7 are the relays, output 8 is
            the on-board LED.
        raw: The raw JSON payload as returned by the board, untouched.
    """

    uptime_seconds: int = 0
    inputs: Dict[str, int] = field(default_factory=dict)
    outputs: Dict[str, int] = field(default_factory=dict)
    raw: Dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_json(cls, payload: Dict[str, object]) -> "BoardState":
        inputs: Dict[str, int] = {}
        outputs: Dict[str, int] = {}
        for key, value in payload.items():
            if not isinstance(value, (int, float)):
                continue
            if key.startswith("inputPin"):
                inputs[key] = int(value)
            elif key.startswith("outputPin"):
                outputs[key] = int(value)
        return cls(
            uptime_seconds=int(payload.get("ss", 0) or 0),
            inputs=inputs,
            outputs=outputs,
            raw=dict(payload),
        )

    # Convenience accessors --------------------------------------------------

    def relay(self, index: int) -> bool:
        """Return True if relay ``index`` (0..7) is currently on."""
        _check_relay_index(index)
        return bool(self.outputs.get(f"outputPin{index}", 0))

    def led(self) -> bool:
        """Return True if the on-board LED is currently on."""
        return bool(self.outputs.get(f"outputPin{LED_INDEX}", 0))

    def relays(self) -> Dict[int, bool]:
        """Return a ``{index: on?}`` mapping for all 8 relays."""
        return {i: self.relay(i) for i in range(NUM_RELAYS)}


class RelayBoard:
    """Client for a single ESP32 Relay X8 board.

    Example:
        >>> board = RelayBoard("192.168.200.105")
        >>> board.set_relay(0, True)      # turn relay 1 on
        >>> board.toggle_relay(2)         # toggle relay 3
        >>> state = board.get_state()
        >>> state.relay(0)
        True
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 80,
        scheme: str = "http",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not host:
            raise ValueError("host must be a non-empty string")
        # Strip any accidental scheme/trailing slash from ``host``.
        if "://" in host:
            scheme, _, host = host.partition("://")
        host = host.rstrip("/")
        self._base_url = f"{scheme}://{host}:{port}"
        self._timeout = float(timeout)

    # ------------------------------------------------------------------ core

    @property
    def base_url(self) -> str:
        """Base URL (``scheme://host:port``) used for requests."""
        return self._base_url

    def _request(self, path: str, params: Optional[Dict[str, str]] = None) -> bytes:
        """Issue a GET request and return the raw response body."""
        url = f"{self._base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RelayBoardError(f"Request to {url!r} failed: {exc}") from exc

    # ---------------------------------------------------------------- state

    def get_state(self) -> BoardState:
        """Fetch the current :class:`BoardState` from ``GET /json``."""
        body = self._request("/json")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RelayBoardError(
                f"Board returned non-JSON payload: {body!r}"
            ) from exc
        if not isinstance(payload, dict):
            raise RelayBoardError(
                f"Board returned unexpected JSON payload: {payload!r}"
            )
        return BoardState.from_json(payload)

    # ---------------------------------------------------------------- relays

    def set_output(self, index: int, on: bool) -> None:
        """Set output ``index`` to ``on`` (True = closed, False = open).

        ``index`` is the 0-based ``outputPinN`` index: 0..7 for the
        relays and :data:`LED_INDEX` (8) for the on-board LED.
        """
        _check_output_index(index)
        self._request(
            "/cmd",
            {"cb": f"outputPin{index}", "v": "1" if on else "0"},
        )

    def toggle_output(self, index: int) -> None:
        """Toggle output ``index`` (0..7 relays, 8 LED)."""
        _check_output_index(index)
        self._request("/cmd", {"toggle": str(index)})

    # Sugar on top of ``set_output``/``toggle_output`` --------------------

    def set_relay(self, index: int, on: bool) -> None:
        """Set relay ``index`` (0..7) on or off."""
        _check_relay_index(index)
        self.set_output(index, on)

    def toggle_relay(self, index: int) -> None:
        """Toggle relay ``index`` (0..7)."""
        _check_relay_index(index)
        self.toggle_output(index)

    def turn_on(self, index: int) -> None:
        """Turn relay ``index`` (0..7) on."""
        self.set_relay(index, True)

    def turn_off(self, index: int) -> None:
        """Turn relay ``index`` (0..7) off."""
        self.set_relay(index, False)

    def all_off(self) -> None:
        """Turn every relay off."""
        for i in range(NUM_RELAYS):
            self.set_relay(i, False)

    def all_on(self) -> None:
        """Turn every relay on."""
        for i in range(NUM_RELAYS):
            self.set_relay(i, True)

    # LED helpers --------------------------------------------------------

    def set_led(self, on: bool) -> None:
        """Turn the on-board LED on or off."""
        self.set_output(LED_INDEX, on)

    def toggle_led(self) -> None:
        """Toggle the on-board LED."""
        self.toggle_output(LED_INDEX)


# --------------------------------------------------------------------- helpers

def _check_relay_index(index: int) -> None:
    if not isinstance(index, int) or not 0 <= index < NUM_RELAYS:
        raise ValueError(
            f"relay index must be an int in [0, {NUM_RELAYS - 1}], got {index!r}"
        )


def _check_output_index(index: int) -> None:
    if not isinstance(index, int) or not 0 <= index <= LED_INDEX:
        raise ValueError(
            f"output index must be an int in [0, {LED_INDEX}], got {index!r}"
        )
