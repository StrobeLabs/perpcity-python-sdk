import os
import sys

from dotenv import load_dotenv

from perpcity_sdk import PerpCityContext


def setup() -> tuple[PerpCityContext, str]:
    load_dotenv(".env.local")

    required = ["RPC_URL", "PRIVATE_KEY", "PERP_MANAGER_ADDRESS", "USDC_ADDRESS", "PERP_ID"]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}")
        sys.exit(1)

    context = PerpCityContext(
        rpc_url=os.environ["RPC_URL"],
        private_key=os.environ["PRIVATE_KEY"],
        perp_manager_address=os.environ["PERP_MANAGER_ADDRESS"],
        usdc_address=os.environ["USDC_ADDRESS"],
    )

    return context, os.environ["PERP_ID"]
