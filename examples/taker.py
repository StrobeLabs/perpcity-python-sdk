from setup import setup

from perpcity_sdk import OpenTakerPositionParams, open_taker_position


def main():
    context, perp_id = setup()

    print("Opening long taker position...")
    params = OpenTakerPositionParams(
        is_long=True,
        margin=100,  # $100 margin
        leverage=5,  # 5x leverage
        unspecified_amount_limit=0,  # no minimum
    )

    position = open_taker_position(context, perp_id, params)

    print(f"Position opened!")
    print(f"  Position ID: {position.position_id}")
    print(f"  Perp ID: {position.perp_id}")
    print(f"  Is Long: {position.is_long}")
    print(f"  Tx Hash: {position.tx_hash}")

    details = position.live_details()
    print(f"\nLive Details:")
    print(f"  PnL: ${details.pnl:.2f}")
    print(f"  Funding: ${details.funding_payment:.2f}")
    print(f"  Effective Margin: ${details.effective_margin:.2f}")
    print(f"  Liquidatable: {details.is_liquidatable}")


if __name__ == "__main__":
    main()
