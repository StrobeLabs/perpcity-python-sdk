import os


def get_rpc_url(url: str | None = None) -> str:
    rpc_url = url or os.environ.get("RPC_URL")
    if not rpc_url:
        raise ValueError(
            "RPC_URL is required. Please set the RPC_URL environment variable "
            "with your full RPC endpoint URL.\n"
            "Example URLs (use your own provider and API key):\n"
            "  https://base-sepolia.g.alchemy.com/v2/YOUR_API_KEY\n"
            "  https://base-sepolia.infura.io/v3/YOUR_API_KEY\n"
            "  https://sepolia.base.org"
        )
    return rpc_url
