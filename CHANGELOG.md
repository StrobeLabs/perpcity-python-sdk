# Changelog

All notable changes to the PerpCity Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.2] - 2026-02-25

Initial public release.

### Added

- **PerpCityContext** -- Core context for RPC connection, wallet, and contract addresses
- **Position management** -- Open/close taker and maker positions, adjust margin and notional
- **Market data** -- Fetch perp data (mark price, fees, bounds, liquidity)
- **Token approvals** -- USDC approval flow for perp manager
- **Pure math** -- Tick/price conversions, sqrt price math, PnL calculations, liquidation checks
- **Integration tests** -- Full test suite against Anvil with mock contract deployment
- **CI** -- Lint (Ruff), unit tests (pytest), integration tests with Anvil
