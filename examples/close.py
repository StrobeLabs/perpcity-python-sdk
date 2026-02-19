import os
import sys

from setup import setup

from perpcity_sdk import ClosePositionParams, close_position


def main():
    context, perp_id = setup()

    position_id = os.environ.get("POSITION_ID")
    if not position_id:
        print("POSITION_ID env var required")
        sys.exit(1)

    print(f"Closing position {position_id}...")

    params = ClosePositionParams(
        min_amt0_out=0,
        min_amt1_out=0,
        max_amt1_in=0,
    )

    result = close_position(context, perp_id, int(position_id), params)

    if result.position is None:
        print(f"Position fully closed. Tx: {result.tx_hash}")
    else:
        print(f"Position partially closed. New position created. Tx: {result.tx_hash}")


if __name__ == "__main__":
    main()
