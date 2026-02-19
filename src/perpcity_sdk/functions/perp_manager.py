from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..types import CreatePerpParams, OpenMakerPositionParams, OpenTakerPositionParams
from ..utils.approve import approve_usdc
from ..utils.constants import NUMBER_1E6
from ..utils.conversions import price_to_sqrt_price_x96, price_to_tick, scale_6_decimals
from ..utils.errors import PerpCityError, with_error_handling
from .open_position import OpenPosition

if TYPE_CHECKING:
    from ..context import PerpCityContext


def create_perp(context: PerpCityContext, params: CreatePerpParams) -> str:
    def _create() -> str:
        sqrt_price_x96 = price_to_sqrt_price_x96(params.starting_price)
        deployments = context.deployments()

        fees_addr = params.fees or deployments.fees_module
        margin_ratios_addr = params.margin_ratios or deployments.margin_ratios_module
        lockup_period_addr = params.lockup_period or deployments.lockup_period_module
        sqrt_price_impact_addr = (
            params.sqrt_price_impact_limit or deployments.sqrt_price_impact_limit_module
        )

        if not all([fees_addr, margin_ratios_addr, lockup_period_addr, sqrt_price_impact_addr]):
            raise PerpCityError(
                "Module addresses must be provided either in params or deployment config"
            )

        contract_params = (
            params.beacon,
            fees_addr,
            margin_ratios_addr,
            lockup_period_addr,
            sqrt_price_impact_addr,
            sqrt_price_x96,
        )

        contract_fn = context._perp_manager.functions.createPerp(contract_params)
        receipt = context.execute_transaction(contract_fn)

        for log in receipt.get("logs", []):
            try:
                event = context._perp_manager.events.PerpCreated().process_log(log)
                perp_id = event["args"]["perpId"]
                if isinstance(perp_id, bytes):
                    return "0x" + perp_id.hex()
                return str(perp_id)
            except Exception:
                continue

        raise PerpCityError("PerpCreated event not found in transaction receipt")

    return with_error_handling(_create, "create_perp")


def open_taker_position(
    context: PerpCityContext,
    perp_id: str,
    params: OpenTakerPositionParams,
) -> OpenPosition:
    def _open() -> OpenPosition:
        if params.margin <= 0:
            raise PerpCityError("Margin must be greater than 0")
        if params.leverage <= 0:
            raise PerpCityError("Leverage must be greater than 0")

        margin_scaled = scale_6_decimals(params.margin)
        margin_ratio = math.floor(NUMBER_1E6 / params.leverage)

        # Calculate total approval: margin + fees
        perp_data = context.get_perp_data(perp_id)
        creator_fee = perp_data.fees.creator_fee
        insurance_fee = perp_data.fees.insurance_fee
        lp_fee = perp_data.fees.lp_fee

        protocol_fee_raw = context._perp_manager.functions.protocolFee().call()
        protocol_fee_rate = int(protocol_fee_raw) / NUMBER_1E6

        notional = (margin_scaled * NUMBER_1E6) // margin_ratio
        total_fee_rate = creator_fee + insurance_fee + lp_fee + protocol_fee_rate
        total_fees = math.ceil(int(notional) * total_fee_rate)

        approve_usdc(context, margin_scaled + total_fees)

        contract_params = (
            context.account.address,  # holder
            params.is_long,
            margin_scaled,
            margin_ratio,
            params.unspecified_amount_limit,
        )

        contract_fn = context._perp_manager.functions.openTakerPos(perp_id, contract_params)
        receipt = context.execute_transaction(contract_fn)

        tx_hash = receipt["transactionHash"].hex()

        taker_pos_id: int | None = None
        for log in receipt.get("logs", []):
            try:
                event = context._perp_manager.events.PositionOpened().process_log(log)
                event_perp_id = event["args"]["perpId"]
                event_perp_hex = (
                    "0x" + event_perp_id.hex()
                    if isinstance(event_perp_id, bytes)
                    else str(event_perp_id)
                )
                if event_perp_hex.lower() == perp_id.lower() and not event["args"]["isMaker"]:
                    taker_pos_id = int(event["args"]["posId"])
                    break
            except Exception:
                continue

        if taker_pos_id is None:
            raise PerpCityError(
                f"PositionOpened event not found in transaction receipt. Hash: {tx_hash}"
            )

        return OpenPosition(context, perp_id, taker_pos_id, params.is_long, False, tx_hash)

    return with_error_handling(_open, "open_taker_position")


def open_maker_position(
    context: PerpCityContext,
    perp_id: str,
    params: OpenMakerPositionParams,
) -> OpenPosition:
    def _open() -> OpenPosition:
        if params.margin <= 0:
            raise PerpCityError("Margin must be greater than 0")
        if params.price_lower >= params.price_upper:
            raise PerpCityError("price_lower must be less than price_upper")

        margin_scaled = scale_6_decimals(params.margin)

        approve_usdc(context, margin_scaled)

        perp_data = context.get_perp_data(perp_id)

        tick_lower = price_to_tick(params.price_lower, True)
        tick_upper = price_to_tick(params.price_upper, False)

        tick_spacing = perp_data.tick_spacing
        aligned_tick_lower = math.floor(tick_lower / tick_spacing) * tick_spacing
        aligned_tick_upper = math.ceil(tick_upper / tick_spacing) * tick_spacing

        contract_params = (
            context.account.address,  # holder
            margin_scaled,
            params.liquidity,
            aligned_tick_lower,
            aligned_tick_upper,
            params.max_amt0_in,
            params.max_amt1_in,
        )

        contract_fn = context._perp_manager.functions.openMakerPos(perp_id, contract_params)
        receipt = context.execute_transaction(contract_fn)

        tx_hash = receipt["transactionHash"].hex()

        maker_pos_id: int | None = None
        for log in receipt.get("logs", []):
            try:
                event = context._perp_manager.events.PositionOpened().process_log(log)
                event_perp_id = event["args"]["perpId"]
                event_perp_hex = (
                    "0x" + event_perp_id.hex()
                    if isinstance(event_perp_id, bytes)
                    else str(event_perp_id)
                )
                if event_perp_hex.lower() == perp_id.lower() and event["args"]["isMaker"]:
                    maker_pos_id = int(event["args"]["posId"])
                    break
            except Exception:
                continue

        if maker_pos_id is None:
            raise PerpCityError(
                f"PositionOpened event not found in transaction receipt. Hash: {tx_hash}"
            )

        return OpenPosition(context, perp_id, maker_pos_id, None, True, tx_hash)

    return with_error_handling(_open, "open_maker_position")
