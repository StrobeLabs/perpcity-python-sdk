from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ClosePositionParams, ClosePositionResult, LiveDetails
from ..utils.conversions import scale_6_decimals
from ..utils.errors import with_error_handling

if TYPE_CHECKING:
    from ..context import PerpCityContext


class OpenPosition:
    def __init__(
        self,
        context: PerpCityContext,
        perp_id: str,
        position_id: int,
        is_long: bool | None = None,
        is_maker: bool | None = None,
        tx_hash: str | None = None,
    ) -> None:
        self.context = context
        self.perp_id = perp_id
        self.position_id = position_id
        self.is_long = is_long
        self.is_maker = is_maker
        self.tx_hash = tx_hash

    def close_position(self, params: ClosePositionParams) -> ClosePositionResult:
        def _close() -> ClosePositionResult:
            contract_params = {
                "posId": self.position_id,
                "minAmt0Out": scale_6_decimals(params.min_amt0_out),
                "minAmt1Out": scale_6_decimals(params.min_amt1_out),
                "maxAmt1In": scale_6_decimals(params.max_amt1_in),
            }

            contract_fn = self.context._perp_manager.functions.closePosition(contract_params)
            receipt = self.context.execute_transaction(contract_fn, gas=500000)

            tx_hash = receipt["transactionHash"].hex()

            new_position_id: int | None = None
            for log in receipt.get("logs", []):
                try:
                    event = self.context._perp_manager.events.PositionOpened().process_log(log)
                    event_perp_id = event["args"]["perpId"]
                    event_pos_id = event["args"]["posId"]
                    event_perp_hex = (
                        "0x" + event_perp_id.hex()
                        if isinstance(event_perp_id, bytes)
                        else str(event_perp_id)
                    )
                    if (
                        event_perp_hex.lower() == self.perp_id.lower()
                        and event_pos_id != self.position_id
                    ):
                        new_position_id = int(event_pos_id)
                        break
                except Exception:
                    continue

            if new_position_id is None:
                return ClosePositionResult(position=None, tx_hash=tx_hash)

            return ClosePositionResult(
                position=OpenPosition(
                    self.context,
                    self.perp_id,
                    new_position_id,
                    self.is_long,
                    self.is_maker,
                    tx_hash,
                ),
                tx_hash=tx_hash,
            )

        pos_type = "maker" if self.is_maker else "taker"
        return with_error_handling(
            _close, f"close_position for {pos_type} position {self.position_id}"
        )

    def live_details(self) -> LiveDetails:
        return self.context._fetch_position_live_details(self.perp_id, self.position_id)
