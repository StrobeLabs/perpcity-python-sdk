# PerpCity Python SDK

Python SDK for interacting with Perp City perpetual futures contracts.

## Installation

```bash
pip install perpcity-sdk
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from perpcity_sdk import PerpCityContext, open_taker_position, OpenTakerPositionParams

# Initialize context
context = PerpCityContext(
    rpc_url="https://base-sepolia.g.alchemy.com/v2/YOUR_KEY",
    private_key="0xYOUR_PRIVATE_KEY",
    perp_manager_address="0xPERP_MANAGER",
    usdc_address="0xUSDC",
)

# Fetch market data
perp_data = context.get_perp_data(perp_id)
print(f"Mark price: {perp_data.mark}")

# Open a long position
position = open_taker_position(
    context,
    perp_id,
    OpenTakerPositionParams(
        is_long=True,
        margin=100,       # $100
        leverage=5,        # 5x
        unspecified_amount_limit=0,
    ),
)
print(f"Position ID: {position.position_id}")

# Check live details
details = position.live_details()
print(f"PnL: ${details.pnl:.2f}")
```

## API Reference

### PerpCityContext

```python
context = PerpCityContext(rpc_url, private_key, perp_manager_address, usdc_address, chain_id=84532)
```

**Methods:**
- `get_perp_data(perp_id)` - Fetch market data (mark price, fees, bounds)
- `get_user_data(address, positions)` - Fetch user USDC balance and position details
- `get_position_raw_data(position_id)` - Fetch raw position data for calculations
- `get_open_position_data(perp_id, position_id, is_long, is_maker)` - Fetch position with live details
- `validate_chain_id()` - Verify RPC matches expected chain

### Trading Functions

- `open_taker_position(context, perp_id, params)` - Open a long/short position
- `open_maker_position(context, perp_id, params)` - Provide liquidity in a price range
- `close_position(context, perp_id, position_id, params)` - Close a position
- `create_perp(context, params)` - Create a new perpetual market

### Calculation Functions

- `calculate_entry_price(raw_data)` - Entry price from position data
- `calculate_position_size(raw_data)` - Position size in perp units
- `calculate_position_value(raw_data, mark_price)` - Current value in USD
- `calculate_leverage(position_value, effective_margin)` - Current leverage
- `calculate_liquidation_price(raw_data, is_long)` - Liquidation price

### Utility Functions

- `price_to_sqrt_price_x96(price)` / `sqrt_price_x96_to_price(sqrt_price_x96)`
- `price_to_tick(price, round_down)` / `tick_to_price(tick)`
- `scale_6_decimals(amount)` / `scale_from_6_decimals(value)`
- `estimate_liquidity(tick_lower, tick_upper, usd_scaled)`
- `calculate_liquidity_for_target_ratio(...)`

## Environment Variables

```
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
PRIVATE_KEY=0xYOUR_PRIVATE_KEY
PERP_MANAGER_ADDRESS=0xYOUR_PERP_MANAGER
USDC_ADDRESS=0xYOUR_USDC
```

## Development

```bash
make build          # Install with dev deps
make test-unit      # Run unit tests
make lint           # Lint with ruff
make ci             # Full CI (lint + tests)
```

## License

MIT
