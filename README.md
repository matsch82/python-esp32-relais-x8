# esp32-relais-x8

[![CI](https://github.com/your-user/python-esp32-relais-x8/actions/workflows/ci.yml/badge.svg)](https://github.com/your-user/python-esp32-relais-x8/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Small Python client for the **ESP32 Relay X8** board (firmware 24.01).
It wraps the board's minimal HTTP API in a friendly Python interface
and ships with a tiny CLI. Depends only on the Python standard library.

## The board's HTTP API

The web UI at `http://<board>/` uses exactly three endpoints:

| Method / path                                | Purpose                                                 |
|----------------------------------------------|---------------------------------------------------------|
| `GET /json`                                  | Return current board state as JSON                      |
| `GET /cmd?cb=outputPin<N>&v=<0\|1>`          | Set output `N` to the given value (`0` = off, `1` = on) |
| `GET /cmd?toggle=<N>`                        | Toggle output `N`                                        |

Output indices:

- `0..7` — the eight physical relays (labelled *Relay 1..8* in the UI)
- `8`    — the on-board LED

Example state payload:

```json
{"ss": 389, "inputPin0": 1,
 "outputPin0": 0, "outputPin1": 0, "outputPin2": 0, "outputPin3": 0,
 "outputPin4": 0, "outputPin5": 0, "outputPin6": 0, "outputPin7": 0,
 "outputPin8": 0}
```

`ss` is the uptime in seconds; `inputPin0` mirrors the on-board IO00
button; `outputPinN` reflects the eight relays plus the LED.

## Installation

```bash
pip install .
```

The package only depends on the Python standard library (`urllib`,
`json`), so it runs on any Python 3.8+ interpreter.

## Library usage

```python
from esp32_relais_x8 import RelayBoard

board = RelayBoard("192.168.200.105")

# Query the current state.
state = board.get_state()
print(state.uptime_seconds, state.relays())

# Control individual relays (0..7).
board.turn_on(0)       # relay 1 on
board.turn_off(3)      # relay 4 off
board.toggle_relay(5)  # relay 6 toggle

# Bulk helpers.
board.all_off()
board.all_on()

# On-board LED (output 8).
board.set_led(True)
board.toggle_led()
```

Any network error is raised as `esp32_relais_x8.RelayBoardError`.

## CLI usage

```bash
# Dump the raw state.
python -m esp32_relais_x8 --host 192.168.200.105 state

# Relay control.
python -m esp32_relais_x8 --host 192.168.200.105 on 0
python -m esp32_relais_x8 --host 192.168.200.105 off 3
python -m esp32_relais_x8 --host 192.168.200.105 toggle 5
python -m esp32_relais_x8 --host 192.168.200.105 all-off

# On-board LED.
python -m esp32_relais_x8 --host 192.168.200.105 led toggle
```

After `pip install .` the same CLI is also available as
`esp32-relais-x8`.

## Examples

Runnable examples live in [`examples/`](examples):

- `examples/basic.py` — print state and toggle relay 0.
- `examples/chaser.py` — run a chaser/running-light pattern across all relays.
- `examples/monitor.py` — continuously poll and print the board state.

```bash
python examples/basic.py 192.168.200.105
python examples/chaser.py 192.168.200.105 --delay 0.2 --loops 3
python examples/monitor.py 192.168.200.105
```

## Repository layout

```
esp32_relais_x8/       # package source
├── __init__.py        # public API re-exports
├── client.py          # RelayBoard + BoardState
└── __main__.py        # CLI entry point
examples/              # runnable scripts
tests/                 # unit tests (no hardware required)
.github/workflows/     # CI configuration
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

The tests spin up a tiny mock HTTP server on a random local port and
run entirely offline.

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

Released under the [MIT License](LICENSE).
