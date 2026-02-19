from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import PerpCityContext

DEFAULT_CONFIRMATIONS = 2


def approve_usdc(
    context: PerpCityContext,
    amount: int,
    confirmations: int = DEFAULT_CONFIRMATIONS,
) -> None:
    deployments = context.deployments()

    contract_fn = context._usdc.functions.approve(deployments.perp_manager, amount)
    context.execute_transaction(contract_fn)
