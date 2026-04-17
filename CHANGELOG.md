# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-17

### Added
- Initial release.
- `RelayBoard` HTTP client for the ESP32 Relay X8 board (firmware 24.01).
- `BoardState` dataclass for the `/json` state payload.
- CLI entry point `esp32-relais-x8` / `python -m esp32_relais_x8`.
- Examples: `basic.py`, `chaser.py`.
- Unit tests running against a local mock HTTP server (stdlib only).
- GitHub Actions CI across Python 3.8 – 3.12.
