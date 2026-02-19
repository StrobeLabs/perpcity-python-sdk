from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..types import (
    ClosePositionParams,
    ClosePositionResult,
    LiveDetails,
    OpenPositionData,
    PositionRawData,
)
from ..utils.conversions import scale_6_decimals
from ..utils.errors import with_error_handling

if TYPE_CHECKING:
    from ..context import PerpCityContext


# Pure accessor functions for OpenPositionData


def get_position_perp_id(position_data: OpenPositionData) -> str:
    return position_data.perp_id


def get_position_id(position_data: OpenPositionData) -> int:
    return position_data.position_id


def get_position_is_long(position_data: OpenPositionData) -> bool | None:
    return position_data.is_long


def get_position_is_maker(position_data: OpenPositionData) -> bool | None:
    return position_data.is_maker


def get_position_live_details(position_data: OpenPositionData) -> LiveDetails:
    return position_data.live_details


def get_position_pnl(position_data: OpenPositionData) -> float:
    return position_data.live_details.pnl


def get_position_funding_payment(position_data: OpenPositionData) -> float:
    return position_data.live_details.funding_payment


def get_position_effective_margin(position_data: OpenPositionData) -> float:
    return position_data.live_details.effective_margin


def get_position_is_liquidatable(position_data: OpenPositionData) -> bool:
    return position_data.live_details.is_liquidatable


# Functions that require context


def close_position(
    context: PerpCityContext,
    perp_id: str,
    position_id: int,
    params: ClosePositionParams,
) -> ClosePositionResult:
    def _close() -> ClosePositionResult:
        contract_params = {
            "posId": position_id,
            "minAmt0Out": scale_6_decimals(params.min_amt0_out),
            "minAmt1Out": scale_6_decimals(params.min_amt1_out),
            "maxAmt1In": scale_6_decimals(params.max_amt1_in),
        }

        contract_fn = context._perp_manager.functions.closePosition(contract_params)
        receipt = context.execute_transaction(contract_fn, gas=500000)

        tx_hash = receipt["transactionHash"].hex()

        # Look for PositionOpened event (partial close creates new position)
        new_position_id: int | None = None
        for log in receipt.get("logs", []):
            try:
                events = context._perp_manager.events.PositionOpened().process_log(log)
                event_perp_id = events["args"]["perpId"]
                event_pos_id = events["args"]["posId"]
                event_perp_hex = (
                    "0x" + event_perp_id.hex()
                    if isinstance(event_perp_id, bytes)
                    else str(event_perp_id)
                )
                if event_perp_hex.lower() == perp_id.lower() and event_pos_id != position_id:
                    new_position_id = int(event_pos_id)
                    break
            except Exception:
                continue

        if new_position_id is None:
            return ClosePositionResult(position=None, tx_hash=tx_hash)

        live_details = get_position_live_details_from_contract(context, perp_id, new_position_id)
        return ClosePositionResult(
            position=OpenPositionData(
                perp_id=perp_id,
                position_id=new_position_id,
                live_details=live_details,
            ),
            tx_hash=tx_hash,
        )

    return with_error_handling(_close, f"close_position for position {position_id}")


def get_position_live_details_from_contract(
    context: PerpCityContext, perp_id: str, position_id: int
) -> LiveDetails:
    return context._fetch_position_live_details(perp_id, position_id)


# Pure calculation functions


def calculate_entry_price(raw_data: PositionRawData) -> float:
    perp_delta = raw_data.entry_perp_delta
    usd_delta = raw_data.entry_usd_delta

    if perp_delta == 0:
        return 0.0

    abs_perp = abs(perp_delta)
    abs_usd = abs(usd_delta)

    return abs_usd / abs_perp


def calculate_position_size(raw_data: PositionRawData) -> float:
    return raw_data.entry_perp_delta / 1e6


def calculate_position_value(raw_data: PositionRawData, mark_price: float) -> float:
    size = calculate_position_size(raw_data)
    return abs(size) * mark_price


def calculate_leverage(position_value: float, effective_margin: float) -> float:
    if effective_margin <= 0:
        return math.inf
    return position_value / effective_margin


def calculate_liquidation_price(raw_data: PositionRawData, is_long: bool) -> float | None:
    entry_price = calculate_entry_price(raw_data)
    position_size = abs(calculate_position_size(raw_data))

    if position_size == 0 or raw_data.margin <= 0:
        return None

    liq_margin_ratio = raw_data.margin_ratios.liq / 1e6
    entry_notional = position_size * entry_price

    margin_excess = raw_data.margin - liq_margin_ratio * entry_notional
    if is_long:
        liq_price = entry_price - margin_excess / position_size
        return max(0.0, liq_price)
    else:
        liq_price = entry_price + margin_excess / position_size
        return liq_price
