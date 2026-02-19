from __future__ import annotations

from cachetools import TTLCache
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.contract import Contract

from .abis import ERC20_ABI, FEES_ABI, MARGIN_RATIOS_ABI, PERP_MANAGER_ABI
from .types import (
    Bounds,
    Fees,
    LiveDetails,
    MarginRatios,
    OpenPositionData,
    PerpCityDeployments,
    PerpConfig,
    PerpData,
    PoolKey,
    PositionRawData,
    UserData,
)
from .utils.conversions import margin_ratio_to_leverage, sqrt_price_x96_to_price
from .utils.errors import PerpCityError, with_error_handling

DEFAULT_CHAIN_ID = 84532  # Base Sepolia


class PerpCityContext:
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        perp_manager_address: str,
        usdc_address: str,
        chain_id: int = DEFAULT_CHAIN_ID,
    ) -> None:
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account: LocalAccount = Account.from_key(private_key)
        self._deployments = PerpCityDeployments(
            perp_manager=Web3.to_checksum_address(perp_manager_address),
            usdc=Web3.to_checksum_address(usdc_address),
        )
        self._chain_id = chain_id
        self._config_cache: TTLCache[str, PerpConfig] = TTLCache(maxsize=256, ttl=300)

        self._perp_manager: Contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(perp_manager_address),
            abi=PERP_MANAGER_ABI,
        )
        self._usdc: Contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(usdc_address),
            abi=ERC20_ABI,
        )

    def deployments(self) -> PerpCityDeployments:
        return self._deployments

    def validate_chain_id(self) -> None:
        rpc_chain_id = self.w3.eth.chain_id
        if rpc_chain_id != self._chain_id:
            raise PerpCityError(
                f"RPC chain mismatch. RPC returned chain ID {rpc_chain_id}, "
                f"but expected chain ID {self._chain_id}. "
                f"Ensure rpc_url corresponds to the correct network."
            )

    def get_perp_config(self, perp_id: str) -> PerpConfig:
        cached = self._config_cache.get(perp_id)
        if cached is not None:
            return cached

        result = self._perp_manager.functions.cfgs(perp_id).call()

        key_data = result[0]
        if not key_data or key_data[3] == 0 or key_data[0] == "0x" + "0" * 40:
            raise PerpCityError(f"Perp ID {perp_id} not found or invalid")

        cfg = PerpConfig(
            key=PoolKey(
                currency0=key_data[0],
                currency1=key_data[1],
                fee=int(key_data[2]),
                tick_spacing=int(key_data[3]),
                hooks=key_data[4],
            ),
            creator=result[1],
            vault=result[2],
            beacon=result[3],
            fees=result[4],
            margin_ratios=result[5],
            lockup_period=result[6],
            sqrt_price_impact_limit=result[7],
        )

        self._config_cache[perp_id] = cfg
        return cfg

    def _fetch_perp_contract_data(self, perp_id: str) -> tuple[int, int, Bounds, Fees]:
        def _fetch() -> tuple[int, int, Bounds, Fees]:
            cfg = self.get_perp_config(perp_id)
            tick_spacing = cfg.key.tick_spacing

            sqrt_price_x96: int = self._perp_manager.functions.timeWeightedAvgSqrtPriceX96(
                perp_id, 1
            ).call()

            fees_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(cfg.fees), abi=FEES_ABI
            )
            margin_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(cfg.margin_ratios), abi=MARGIN_RATIOS_ABI
            )

            min_taker_ratio = margin_contract.functions.MIN_TAKER_RATIO().call()
            max_taker_ratio = margin_contract.functions.MAX_TAKER_RATIO().call()
            liquidation_taker_ratio = margin_contract.functions.LIQUIDATION_TAKER_RATIO().call()

            creator_fee = fees_contract.functions.CREATOR_FEE().call()
            insurance_fee = fees_contract.functions.INSURANCE_FEE().call()
            lp_fee = fees_contract.functions.LP_FEE().call()
            liquidation_fee = fees_contract.functions.LIQUIDATION_FEE().call()

            min_taker_leverage = margin_ratio_to_leverage(int(max_taker_ratio))
            max_taker_leverage = margin_ratio_to_leverage(int(min_taker_ratio))

            def scale_fee(fee: object) -> float:
                return int(fee) / 1e6

            bounds = Bounds(
                min_margin=10,
                min_taker_leverage=min_taker_leverage,
                max_taker_leverage=max_taker_leverage,
                liquidation_taker_ratio=int(liquidation_taker_ratio) / 1e6,
            )
            fees = Fees(
                creator_fee=scale_fee(creator_fee),
                insurance_fee=scale_fee(insurance_fee),
                lp_fee=scale_fee(lp_fee),
                liquidation_fee=scale_fee(liquidation_fee),
            )

            return (tick_spacing, sqrt_price_x96, bounds, fees)

        return with_error_handling(_fetch, f"fetch_perp_contract_data for perp {perp_id}")

    def get_perp_data(self, perp_id: str) -> PerpData:
        tick_spacing, sqrt_price_x96, bounds, fees = self._fetch_perp_contract_data(perp_id)
        cfg = self.get_perp_config(perp_id)

        return PerpData(
            id=perp_id,
            tick_spacing=tick_spacing,
            mark=sqrt_price_x96_to_price(sqrt_price_x96),
            beacon=cfg.beacon,
            bounds=bounds,
            fees=fees,
        )

    def _fetch_position_live_details(self, perp_id: str, position_id: int) -> LiveDetails:
        def _fetch() -> LiveDetails:
            result = self._perp_manager.functions.quoteClosePosition(position_id).call()

            unexpected_reason, pnl, funding, net_margin, was_liquidated = result

            if unexpected_reason != b"" and unexpected_reason != "0x":
                raise PerpCityError(
                    f"Failed to quote position {position_id} - "
                    "position may be invalid or already closed"
                )

            return LiveDetails(
                pnl=int(pnl) / 1e6,
                funding_payment=int(funding) / 1e6,
                effective_margin=int(net_margin) / 1e6,
                is_liquidatable=bool(was_liquidated),
            )

        return with_error_handling(
            _fetch, f"fetch_position_live_details for position {position_id}"
        )

    def get_open_position_data(
        self, perp_id: str, position_id: int, is_long: bool, is_maker: bool
    ) -> OpenPositionData:
        live_details = self._fetch_position_live_details(perp_id, position_id)
        return OpenPositionData(
            perp_id=perp_id,
            position_id=position_id,
            is_long=is_long,
            is_maker=is_maker,
            live_details=live_details,
        )

    def get_user_data(
        self,
        user_address: str,
        positions: list[dict[str, object]],
    ) -> UserData:
        checksum_addr = Web3.to_checksum_address(user_address)
        usdc_balance_raw: int = self._usdc.functions.balanceOf(checksum_addr).call()

        open_positions: list[OpenPositionData] = []
        for pos in positions:
            live_details = self._fetch_position_live_details(
                str(pos["perp_id"]),
                int(pos["position_id"]),  # type: ignore[arg-type]
            )
            open_positions.append(
                OpenPositionData(
                    perp_id=str(pos["perp_id"]),
                    position_id=int(pos["position_id"]),  # type: ignore[arg-type]
                    is_long=bool(pos.get("is_long")),
                    is_maker=bool(pos.get("is_maker")),
                    live_details=live_details,
                )
            )

        return UserData(
            wallet_address=user_address,
            usdc_balance=int(usdc_balance_raw) / 1e6,
            open_positions=open_positions,
        )

    def get_position_raw_data(self, position_id: int) -> PositionRawData:
        def _fetch() -> PositionRawData:
            result = self._perp_manager.functions.positions(position_id).call()

            perp_id = result[0]
            margin = result[1]
            entry_perp_delta = result[2]
            entry_usd_delta = result[3]
            margin_ratios_raw = result[7]

            zero_perp_id = "0x" + "0" * 64
            if perp_id == zero_perp_id or perp_id == bytes(32):
                raise PerpCityError(f"Position {position_id} does not exist")

            perp_id_hex = "0x" + perp_id.hex() if isinstance(perp_id, bytes) else str(perp_id)

            return PositionRawData(
                perp_id=perp_id_hex,
                position_id=position_id,
                margin=int(margin) / 1e6,
                entry_perp_delta=int(entry_perp_delta),
                entry_usd_delta=int(entry_usd_delta),
                margin_ratios=MarginRatios(
                    min=int(margin_ratios_raw[0]),
                    max=int(margin_ratios_raw[1]),
                    liq=int(margin_ratios_raw[2]),
                ),
            )

        return with_error_handling(_fetch, f"get_position_raw_data for position {position_id}")

    def execute_transaction(self, contract_fn: object, gas: int | None = None) -> dict:
        tx_params: dict = {
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address, "pending"),
            "chainId": self._chain_id,
        }
        if gas is not None:
            tx_params["gas"] = gas

        tx = contract_fn.build_transaction(tx_params)  # type: ignore[union-attr]

        if gas is None:
            tx["gas"] = self.w3.eth.estimate_gas(tx)

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] == 0:
            raise PerpCityError(f"Transaction reverted. Hash: {tx_hash.hex()}")

        return dict(receipt)
