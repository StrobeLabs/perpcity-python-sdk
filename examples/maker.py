from setup import setup

from perpcity_sdk import (
    OpenMakerPositionParams,
    estimate_liquidity,
    open_maker_position,
    price_to_tick,
    scale_6_decimals,
)


def main():
    context, perp_id = setup()

    price_lower = 0.9
    price_upper = 1.1
    margin = 100  # $100

    tick_lower = price_to_tick(price_lower, True)
    tick_upper = price_to_tick(price_upper, False)

    margin_scaled = scale_6_decimals(margin)
    liquidity = estimate_liquidity(tick_lower, tick_upper, margin_scaled)

    print(f"Opening maker position...")
    print(f"  Price range: {price_lower} - {price_upper}")
    print(f"  Tick range: {tick_lower} - {tick_upper}")
    print(f"  Margin: ${margin}")
    print(f"  Liquidity: {liquidity}")

    params = OpenMakerPositionParams(
        margin=margin,
        price_lower=price_lower,
        price_upper=price_upper,
        liquidity=liquidity,
        max_amt0_in=margin_scaled * 10,
        max_amt1_in=margin_scaled * 10,
    )

    position = open_maker_position(context, perp_id, params)

    print(f"\nPosition opened!")
    print(f"  Position ID: {position.position_id}")
    print(f"  Tx Hash: {position.tx_hash}")


if __name__ == "__main__":
    main()
