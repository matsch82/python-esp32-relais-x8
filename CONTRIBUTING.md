# Contributing

Thanks for your interest in improving `esp32-relais-x8`!

## Development setup

```bash
git clone https://github.com/<your-user>/python-esp32-relais-x8.git
cd python-esp32-relais-x8
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the tests

The test suite uses only the standard library and spins up a tiny mock
HTTP server on a random local port — no real board is required.

```bash
python -m unittest discover -s tests -v
```

## Coding style

- Python 3.8+ compatible.
- Only standard-library dependencies in the runtime package.
- Public API should carry type hints and docstrings.

## Submitting changes

1. Fork the repo and create a feature branch.
2. Add/adjust tests for your change.
3. Make sure `python -m unittest discover -s tests` passes.
4. Open a pull request describing the change.
