from setup import setup

from perpcity_sdk import get_perp_bounds, get_perp_fees, get_perp_mark, get_perp_tick_spacing


def main():
    context, perp_id = setup()

    print(f"Fetching data for perp {perp_id}...")
    perp_data = context.get_perp_data(perp_id)

    print(f"\nPerp Data:")
    print(f"  ID: {perp_data.id}")
    print(f"  Mark Price: {get_perp_mark(perp_data):.4f}")
    print(f"  Tick Spacing: {get_perp_tick_spacing(perp_data)}")
    print(f"  Beacon: {perp_data.beacon}")

    bounds = get_perp_bounds(perp_data)
    print(f"\nBounds:")
    print(f"  Min Margin: {bounds.min_margin}")
    print(f"  Min Leverage: {bounds.min_taker_leverage:.2f}x")
    print(f"  Max Leverage: {bounds.max_taker_leverage:.2f}x")
    print(f"  Liquidation Ratio: {bounds.liquidation_taker_ratio:.4f}")

    fees = get_perp_fees(perp_data)
    print(f"\nFees:")
    print(f"  Creator: {fees.creator_fee:.4%}")
    print(f"  Insurance: {fees.insurance_fee:.4%}")
    print(f"  LP: {fees.lp_fee:.4%}")
    print(f"  Liquidation: {fees.liquidation_fee:.4%}")


if __name__ == "__main__":
    main()
