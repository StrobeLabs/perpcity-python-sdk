import json
from pathlib import Path

_ABI_DIR = Path(__file__).parent


def _load_abi(filename: str) -> list:
    with open(_ABI_DIR / filename) as f:
        return json.load(f)


PERP_MANAGER_ABI = _load_abi("perp_manager.json")
BEACON_ABI = _load_abi("beacon.json")
FEES_ABI = _load_abi("fees.json")
MARGIN_RATIOS_ABI = _load_abi("margin_ratios.json")
ERC20_ABI = _load_abi("erc20.json")
