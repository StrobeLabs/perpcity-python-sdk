from perpcity_sdk.utils.errors import (
    ContractError,
    ErrorCategory,
    ErrorSource,
    InsufficientFundsError,
    PerpCityError,
    RPCError,
    TransactionRejectedError,
    ValidationError,
    _detect_error_source,
    _format_contract_error,
    parse_contract_error,
)


class TestErrorClasses:
    def test_perpcity_error(self):
        err = PerpCityError("test error")
        assert str(err) == "test error"
        assert err.cause is None

    def test_perpcity_error_with_cause(self):
        cause = ValueError("cause")
        err = PerpCityError("test", cause=cause)
        assert err.cause is cause

    def test_contract_error(self):
        err = ContractError("msg", error_name="InvalidMargin", args=(42,))
        assert str(err) == "msg"
        assert err.error_name == "InvalidMargin"
        assert err.args_data == (42,)

    def test_transaction_rejected_error(self):
        err = TransactionRejectedError()
        assert "rejected" in str(err).lower()

    def test_insufficient_funds_error(self):
        err = InsufficientFundsError()
        assert "insufficient" in str(err).lower()

    def test_rpc_error(self):
        err = RPCError("rpc failed")
        assert str(err) == "rpc failed"

    def test_validation_error(self):
        err = ValidationError("invalid input")
        assert str(err) == "invalid input"


class TestDetectErrorSource:
    def test_pool_manager_errors(self):
        pool_errors = [
            "CurrencyNotSettled",
            "PoolNotInitialized",
            "AlreadyUnlocked",
            "ManagerLocked",
            "SwapAmountCannotBeZero",
        ]
        for name in pool_errors:
            assert _detect_error_source(name) == ErrorSource.POOL_MANAGER

    def test_perp_manager_errors(self):
        perp_errors = [
            "InvalidMargin",
            "InvalidLevX96",
            "SwapReverted",
            "ZeroSizePosition",
            "Unauthorized",
        ]
        for name in perp_errors:
            assert _detect_error_source(name) == ErrorSource.PERP_MANAGER

    def test_unknown_errors(self):
        assert _detect_error_source("SomeUnknownError") == ErrorSource.UNKNOWN


class TestFormatContractError:
    def test_known_error_with_args(self):
        msg, debug = _format_contract_error("InvalidMargin", (42,))
        assert "42" in msg
        assert debug.category == ErrorCategory.USER_ERROR

    def test_known_error_no_args(self):
        msg, debug = _format_contract_error("SwapReverted", ())
        assert "Swap failed" in msg
        assert debug.category == ErrorCategory.STATE_ERROR

    def test_config_error(self):
        msg, debug = _format_contract_error("InvalidBeaconAddress", ("0xabc",))
        assert "0xabc" in msg
        assert debug.category == ErrorCategory.CONFIG_ERROR

    def test_system_error(self):
        msg, debug = _format_contract_error("CurrencyNotSettled", ())
        assert "settled" in msg.lower()
        assert debug.category == ErrorCategory.SYSTEM_ERROR

    def test_unknown_error(self):
        msg, debug = _format_contract_error("UnknownError", (1, 2))
        assert "Contract error: UnknownError" in msg
        assert "1, 2" in msg
        assert debug.source == ErrorSource.UNKNOWN

    def test_all_perp_manager_errors(self):
        perp_errors = [
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
        ]
        for name in perp_errors:
            msg, debug = _format_contract_error(name, ("arg0", "arg1", "arg2"))
            assert msg  # Non-empty message
            assert debug.source == ErrorSource.PERP_MANAGER

    def test_all_pool_manager_errors(self):
        pool_errors = [
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
        ]
        for name in pool_errors:
            msg, debug = _format_contract_error(name, ("arg0", "arg1"))
            assert msg
            assert debug.source == ErrorSource.POOL_MANAGER


class TestParseContractError:
    def test_already_perpcity_error(self):
        original = PerpCityError("already parsed")
        result = parse_contract_error(original)
        assert result is original

    def test_user_rejected(self):
        err = Exception("User rejected the transaction")
        result = parse_contract_error(err)
        assert isinstance(result, TransactionRejectedError)

    def test_insufficient_funds(self):
        err = Exception("insufficient funds for gas")
        result = parse_contract_error(err)
        assert isinstance(result, InsufficientFundsError)

    def test_execution_reverted_known(self):
        err = Exception("execution reverted: InvalidMargin")
        result = parse_contract_error(err)
        assert isinstance(result, ContractError)

    def test_execution_reverted_unknown(self):
        err = Exception("execution reverted: 0xdeadbeef")
        result = parse_contract_error(err)
        assert isinstance(result, ContractError)

    def test_generic_error(self):
        err = Exception("something went wrong")
        result = parse_contract_error(err)
        assert isinstance(result, PerpCityError)
