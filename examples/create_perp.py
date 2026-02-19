import os
import sys

from setup import setup

from perpcity_sdk import CreatePerpParams, create_perp


def main():
    context, _ = setup()

    beacon = os.environ.get("BEACON_ADDRESS")
    if not beacon:
        print("BEACON_ADDRESS env var required")
        sys.exit(1)

    print("Creating new perpetual market...")

    params = CreatePerpParams(
        starting_price=1.0,
        beacon=beacon,
    )

    perp_id = create_perp(context, params)

    print(f"Perp created!")
    print(f"  Perp ID: {perp_id}")


if __name__ == "__main__":
    main()
