from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class ErrorCategory(str, Enum):
    USER_ERROR = "USER_ERROR"
    STATE_ERROR = "STATE_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"


class ErrorSource(str, Enum):
    PERP_MANAGER = "PERP_MANAGER"
    POOL_MANAGER = "POOL_MANAGER"
    UNKNOWN = "UNKNOWN"


@dataclass
class ErrorDebugInfo:
    source: ErrorSource
    category: ErrorCategory
    error_selector: str | None = None
    raw_data: str | None = None
    can_retry: bool | None = None
    retry_guidance: str | None = None


class PerpCityError(Exception):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class ContractError(PerpCityError):
    def __init__(
        self,
        message: str,
        error_name: str | None = None,
        args: tuple[Any, ...] | None = None,
        debug: ErrorDebugInfo | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause)
        self.error_name = error_name
        self.args_data = args
        self.debug = debug


class TransactionRejectedError(PerpCityError):
    def __init__(
        self, message: str = "Transaction rejected by user", cause: Exception | None = None
    ) -> None:
        super().__init__(message, cause)


class InsufficientFundsError(PerpCityError):
    def __init__(
        self,
        message: str = "Insufficient funds for transaction",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause)


class RPCError(PerpCityError):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, cause)


class ValidationError(PerpCityError):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, cause)


_POOL_MANAGER_ERRORS = {
    "CurrencyNotSettled",
    "PoolNotInitialized",
    "AlreadyUnlocked",
    "ManagerLocked",
    "TickSpacingTooLarge",
    "TickSpacingTooSmall",
    "CurrenciesOutOfOrderOrEqual",
    "UnauthorizedDynamicLPFeeUpdate",
    "SwapAmountCannotBeZero",
    "NonzeroNativeValue",
    "MustClearExactPositiveDelta",
}

_PERP_MANAGER_ERRORS = {
    "InvalidBeaconAddress",
    "InvalidTradingFeeSplits",
    "InvalidMaxOpeningLev",
    "InvalidLiquidationLev",
    "InvalidLiquidationFee",
    "InvalidLiquidatorFeeSplit",
    "InvalidClose",
    "InvalidCaller",
    "InvalidLiquidity",
    "InvalidMargin",
    "InvalidLevX96",
    "MakerPositionLocked",
    "MaximumAmountExceeded",
    "MinimumAmountInsufficient",
    "PriceImpactTooHigh",
    "SwapReverted",
    "ZeroSizePosition",
    "InvalidFundingInterval",
    "InvalidPriceImpactBand",
    "InvalidMarketDeathThreshold",
    "InvalidTickRange",
    "MarketNotKillable",
    "InvalidStartingSqrtPriceX96",
    "AccountBalanceOverflow",
    "BalanceQueryForZeroAddress",
    "NotOwnerNorApproved",
    "TokenAlreadyExists",
    "TokenDoesNotExist",
    "TransferFromIncorrectOwner",
    "TransferToNonERC721ReceiverImplementer",
    "TransferToZeroAddress",
    "NewOwnerIsZeroAddress",
    "NoHandoverRequest",
    "Unauthorized",
    "TransferFromFailed",
    "TransferFailed",
    "ApproveFailed",
    "AlreadyInitialized",
    "FeesNotRegistered",
    "FeeTooLarge",
    "MarginRatiosNotRegistered",
    "LockupPeriodNotRegistered",
    "SqrtPriceImpactLimitNotRegistered",
    "ModuleAlreadyRegistered",
    "InvalidAction",
    "InvalidMarginRatio",
    "MakerNotAllowed",
    "PositionLocked",
    "ZeroDelta",
    "NotPoolManager",
    "NoLiquidityToReceiveFees",
}


def _detect_error_source(error_name: str) -> ErrorSource:
    if error_name in _POOL_MANAGER_ERRORS:
        return ErrorSource.POOL_MANAGER
    if error_name in _PERP_MANAGER_ERRORS:
        return ErrorSource.PERP_MANAGER
    return ErrorSource.UNKNOWN


def _format_contract_error(error_name: str, args: tuple[Any, ...]) -> tuple[str, ErrorDebugInfo]:
    source = _detect_error_source(error_name)

    error_map: dict[str, tuple[str, ErrorDebugInfo]] = {
        "InvalidBeaconAddress": (
            f"Invalid beacon address: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidTradingFeeSplits": (
            f"Invalid trading fee splits. Insurance split: {args[0] if args else ''}, "
            f"Creator split: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidMaxOpeningLev": (
            f"Invalid maximum opening leverage: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidLiquidationLev": (
            f"Invalid liquidation leverage: {args[0] if args else ''}. "
            f"Must be less than max opening leverage: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidLiquidationFee": (
            f"Invalid liquidation fee: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidLiquidatorFeeSplit": (
            f"Invalid liquidator fee split: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidClose": (
            f"Cannot close position. Caller: {args[0] if args else ''}, "
            f"Holder: {args[1] if len(args) > 1 else ''}, "
            f"Is Liquidated: {args[2] if len(args) > 2 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidCaller": (
            f"Invalid caller. Expected: {args[1] if len(args) > 1 else ''}, "
            f"Got: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidLiquidity": (
            f"Invalid liquidity amount: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidMargin": (
            f"Invalid margin amount: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidLevX96": (
            f"Invalid leverage: {args[0] if args else ''}. "
            f"Maximum allowed: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "MakerPositionLocked": (
            f"Maker position is locked until timestamp {args[1] if len(args) > 1 else ''}. "
            f"Current time: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "MaximumAmountExceeded": (
            f"Maximum amount exceeded. Maximum: {args[0] if args else ''}, "
            f"Requested: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "MinimumAmountInsufficient": (
            f"Minimum amount not met. Required: {args[0] if args else ''}, "
            f"Received: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "PriceImpactTooHigh": (
            f"Price impact too high. Current price: {args[0] if args else ''}, "
            f"Min acceptable: {args[1] if len(args) > 1 else ''}, "
            f"Max acceptable: {args[2] if len(args) > 2 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "SwapReverted": (
            "Swap failed. This may be due to insufficient liquidity or slippage tolerance.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "ZeroSizePosition": (
            f"Cannot create zero-size position. Perp delta: {args[0] if args else ''}, "
            f"USD delta: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidFundingInterval": (
            f"Invalid funding interval: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidPriceImpactBand": (
            f"Invalid price impact band: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidMarketDeathThreshold": (
            f"Invalid market death threshold: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidTickRange": (
            f"Invalid tick range. Lower: {args[0] if args else ''}, "
            f"Upper: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "MarketNotKillable": (
            f"Market health ({args[0] if args else ''}) is above death threshold "
            f"({args[1] if len(args) > 1 else ''}). Market cannot be killed yet.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "InvalidStartingSqrtPriceX96": (
            f"Invalid starting sqrt price: {args[0] if args else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "CurrencyNotSettled": (
            "Currency balance not settled after operation. "
            "The pool manager requires all currency deltas to be settled before unlocking.",
            ErrorDebugInfo(
                source=source,
                category=ErrorCategory.SYSTEM_ERROR,
                retry_guidance="Issue with the transaction flow. Please try again.",
            ),
        ),
        "PoolNotInitialized": (
            "Pool does not exist or has not been initialized. "
            "Ensure the pool has been created before attempting to interact with it.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "AlreadyUnlocked": (
            "Pool manager is already unlocked. This indicates a potential reentrancy issue.",
            ErrorDebugInfo(
                source=source,
                category=ErrorCategory.SYSTEM_ERROR,
                can_retry=True,
                retry_guidance="This is a temporary state. Please retry your transaction.",
            ),
        ),
        "ManagerLocked": (
            "Uniswap V4 Pool Manager is currently locked. "
            "This is a temporary state during transaction processing.",
            ErrorDebugInfo(
                source=source,
                category=ErrorCategory.STATE_ERROR,
                can_retry=True,
                retry_guidance="Please retry your transaction in a moment.",
            ),
        ),
        "TickSpacingTooLarge": (
            f"Tick spacing ({args[0] if args else ''}) exceeds the maximum allowed value. "
            "Please use a smaller tick spacing.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "TickSpacingTooSmall": (
            f"Tick spacing ({args[0] if args else ''}) is below the minimum allowed value. "
            "Please use a larger tick spacing.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "CurrenciesOutOfOrderOrEqual": (
            f"Currencies must be ordered (currency0 < currency1) and not equal. "
            f"Got currency0: {args[0] if args else ''}, "
            f"currency1: {args[1] if len(args) > 1 else ''}",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "UnauthorizedDynamicLPFeeUpdate": (
            "Unauthorized attempt to update dynamic LP fee. "
            "Only authorized addresses can modify fees.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "SwapAmountCannotBeZero": (
            "Swap amount cannot be zero. Please specify a valid swap amount.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "NonzeroNativeValue": (
            "Native ETH was sent with the transaction when none was expected. "
            "Do not send ETH with this operation.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "MustClearExactPositiveDelta": (
            "Must clear exact positive delta. "
            "The transaction must settle the exact amount owed to the pool.",
            ErrorDebugInfo(source=source, category=ErrorCategory.SYSTEM_ERROR),
        ),
        "AccountBalanceOverflow": (
            "Account balance overflow detected. "
            "This is a critical error that should not occur under normal conditions.",
            ErrorDebugInfo(source=source, category=ErrorCategory.SYSTEM_ERROR),
        ),
        "BalanceQueryForZeroAddress": (
            "Cannot query balance for the zero address.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "NotOwnerNorApproved": (
            "Caller is not the owner or an approved operator for this position.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TokenAlreadyExists": (
            "A position with this ID already exists.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "TokenDoesNotExist": (
            "The specified position does not exist.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TransferFromIncorrectOwner": (
            "Attempting to transfer position from incorrect owner.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TransferToNonERC721ReceiverImplementer": (
            "Cannot transfer position to a contract that does not implement "
            "ERC721 receiver interface.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TransferToZeroAddress": (
            "Cannot transfer position to the zero address.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "NewOwnerIsZeroAddress": (
            "New owner cannot be the zero address.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "NoHandoverRequest": (
            "No pending ownership handover request exists.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "Unauthorized": (
            "Unauthorized access. Caller does not have permission to perform this operation.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TransferFromFailed": (
            "ERC20 transferFrom operation failed. "
            "Ensure you have approved sufficient tokens and have enough balance.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "TransferFailed": (
            "ERC20 transfer operation failed. "
            "This may indicate insufficient balance or a token contract issue.",
            ErrorDebugInfo(source=source, category=ErrorCategory.SYSTEM_ERROR),
        ),
        "ApproveFailed": (
            "ERC20 approve operation failed. Please check the token contract.",
            ErrorDebugInfo(source=source, category=ErrorCategory.SYSTEM_ERROR),
        ),
        "AlreadyInitialized": (
            "Contract has already been initialized. Initialization can only occur once.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "FeesNotRegistered": (
            "Fees module has not been registered for this pool. "
            "Please register the fees module before proceeding.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "FeeTooLarge": (
            "The specified fee exceeds the maximum allowed value.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "MarginRatiosNotRegistered": (
            "Margin ratios module has not been registered for this pool. "
            "Please register the module before proceeding.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "LockupPeriodNotRegistered": (
            "Lockup period module has not been registered for this pool. "
            "Please register the module before proceeding.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "SqrtPriceImpactLimitNotRegistered": (
            "Sqrt price impact limit module has not been registered for this pool. "
            "Please register the module before proceeding.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "ModuleAlreadyRegistered": (
            "This module has already been registered and cannot be registered again.",
            ErrorDebugInfo(source=source, category=ErrorCategory.CONFIG_ERROR),
        ),
        "InvalidAction": (
            f"Invalid action type: {args[0] if args else ''}. Please specify a valid action.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "InvalidMarginRatio": (
            f"Invalid margin ratio: {args[0] if args else ''}. "
            "The margin ratio must be within acceptable bounds.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "MakerNotAllowed": (
            "Maker positions are not allowed for this operation.",
            ErrorDebugInfo(source=source, category=ErrorCategory.USER_ERROR),
        ),
        "PositionLocked": (
            "This position is currently locked. "
            "Maker positions have a time-based lockup period to ensure liquidity stability.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "ZeroDelta": (
            "Position has zero size. Cannot perform operation on a position with no open size.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
        "NotPoolManager": (
            "Only the Uniswap V4 Pool Manager can call this function. "
            "This indicates an architectural issue.",
            ErrorDebugInfo(source=source, category=ErrorCategory.SYSTEM_ERROR),
        ),
        "NoLiquidityToReceiveFees": (
            "No liquidity available to receive fees. "
            "Ensure there is sufficient liquidity in the pool.",
            ErrorDebugInfo(source=source, category=ErrorCategory.STATE_ERROR),
        ),
    }

    if error_name in error_map:
        return error_map[error_name]

    args_str = ", ".join(str(a) for a in args) if args else ""
    suffix = f" ({args_str})" if args_str else ""
    return (
        f"Contract error: {error_name}{suffix}",
        ErrorDebugInfo(source=ErrorSource.UNKNOWN, category=ErrorCategory.SYSTEM_ERROR),
    )


def parse_contract_error(error: Exception) -> PerpCityError:
    if isinstance(error, PerpCityError):
        return error

    message = str(error)

    # Check for user rejection patterns
    if "User rejected" in message or "user denied" in message.lower():
        return TransactionRejectedError(message, cause=error)

    # Check for insufficient funds
    if "insufficient funds" in message.lower():
        return InsufficientFundsError(message, cause=error)

    # Try to extract custom error name from web3.py ContractLogicError messages
    # web3.py format: "execution reverted: ErrorName" or includes error selector
    if "execution reverted" in message.lower():
        # Try to find a known error name in the message
        all_known = _POOL_MANAGER_ERRORS | _PERP_MANAGER_ERRORS
        for error_name in all_known:
            if error_name in message:
                formatted_msg, debug = _format_contract_error(error_name, ())
                return ContractError(formatted_msg, error_name, (), debug, cause=error)
        return ContractError(message, cause=error)

    return PerpCityError(message, cause=error)


def with_error_handling(fn: Callable[[], T], context: str) -> T:
    try:
        return fn()
    except PerpCityError:
        raise
    except Exception as e:
        parsed = parse_contract_error(e)
        raise PerpCityError(f"{context}: {parsed}", cause=e) from e
