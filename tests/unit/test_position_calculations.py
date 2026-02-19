import math

from perpcity_sdk.functions.position import (
    calculate_entry_price,
    calculate_leverage,
    calculate_liquidation_price,
    calculate_position_size,
    calculate_position_value,
)
from perpcity_sdk.types import MarginRatios, PositionRawData


def _raw(
    margin: float = 100,
    perp_delta: int = 1_000_000,
    usd_delta: int = 50_000_000,
    liq_ratio: int = 50000,
) -> PositionRawData:
    return PositionRawData(
        perp_id="0x123",
        position_id=1,
        margin=margin,
        entry_perp_delta=perp_delta,
        entry_usd_delta=usd_delta,
        margin_ratios=MarginRatios(min=100000, max=500000, liq=liq_ratio),
    )


class TestCalculateEntryPrice:
    def test_long_position(self):
        raw = _raw(perp_delta=1_000_000, usd_delta=50_000_000)
        assert calculate_entry_price(raw) == 50

    def test_short_position(self):
        raw = _raw(perp_delta=-2_000_000, usd_delta=-100_000_000)
        assert calculate_entry_price(raw) == 50

    def test_zero_size(self):
        raw = _raw(perp_delta=0, usd_delta=0)
        assert calculate_entry_price(raw) == 0

    def test_large_values(self):
        raw = _raw(margin=10000, perp_delta=100_000_000, usd_delta=5_000_000_000)
        assert calculate_entry_price(raw) == 50

    def test_fractional_price(self):
        raw = _raw(perp_delta=10_000_000, usd_delta=123_450_000)
        assert abs(calculate_entry_price(raw) - 12.345) < 0.001


class TestCalculatePositionSize:
    def test_positive_long(self):
        raw = _raw(perp_delta=1_000_000)
        assert calculate_position_size(raw) == 1

    def test_negative_short(self):
        raw = _raw(perp_delta=-2_000_000)
        assert calculate_position_size(raw) == -2

    def test_zero(self):
        raw = _raw(perp_delta=0)
        assert calculate_position_size(raw) == 0

    def test_fractional(self):
        raw = _raw(perp_delta=500_000)
        assert calculate_position_size(raw) == 0.5

    def test_large(self):
        raw = _raw(perp_delta=100_000_000)
        assert calculate_position_size(raw) == 100


class TestCalculatePositionValue:
    def test_long(self):
        raw = _raw(perp_delta=1_000_000)
        assert calculate_position_value(raw, 60) == 60

    def test_short(self):
        raw = _raw(perp_delta=-2_000_000)
        assert calculate_position_value(raw, 55) == 110

    def test_zero_size(self):
        raw = _raw(perp_delta=0)
        assert calculate_position_value(raw, 50) == 0

    def test_fractional(self):
        raw = _raw(perp_delta=1_500_000)
        assert abs(calculate_position_value(raw, 52.75) - 79.125) < 0.001

    def test_always_positive(self):
        long_raw = _raw(perp_delta=1_000_000)
        short_raw = _raw(perp_delta=-1_000_000)
        assert calculate_position_value(long_raw, 60) == 60
        assert calculate_position_value(short_raw, 60) == 60
        assert calculate_position_value(long_raw, 60) > 0
        assert calculate_position_value(short_raw, 60) > 0


class TestCalculateLeverage:
    def test_normal(self):
        assert calculate_leverage(1000, 100) == 10

    def test_1x(self):
        assert calculate_leverage(100, 100) == 1

    def test_fractional(self):
        assert calculate_leverage(150, 100) == 1.5

    def test_zero_margin(self):
        assert calculate_leverage(1000, 0) == math.inf

    def test_negative_margin(self):
        assert calculate_leverage(1000, -50) == math.inf

    def test_high_leverage(self):
        assert calculate_leverage(10000, 50) == 200

    def test_zero_value(self):
        assert calculate_leverage(0, 100) == 0


class TestCalculateLiquidationPrice:
    def test_long(self):
        raw = _raw()
        liq_price = calculate_liquidation_price(raw, True)
        assert liq_price is not None
        assert liq_price >= 0

    def test_short(self):
        raw = _raw(perp_delta=-1_000_000, usd_delta=-50_000_000)
        liq_price = calculate_liquidation_price(raw, False)
        assert liq_price is not None
        assert liq_price > 50  # Higher than entry for shorts

    def test_zero_size(self):
        raw = _raw(perp_delta=0, usd_delta=0)
        assert calculate_liquidation_price(raw, True) is None

    def test_zero_margin(self):
        raw = _raw(margin=0, perp_delta=1_000_000_000_000_000_000)
        assert calculate_liquidation_price(raw, True) is None

    def test_high_leverage_long(self):
        raw = _raw(margin=10, perp_delta=1_000_000, usd_delta=50_000_000, liq_ratio=50000)
        liq_price = calculate_liquidation_price(raw, True)
        assert liq_price is not None
        assert liq_price >= 0
        assert liq_price < 50  # Below entry

    def test_low_leverage_long(self):
        raw = _raw(margin=500, perp_delta=10_000_000, usd_delta=500_000_000, liq_ratio=50000)
        liq_price = calculate_liquidation_price(raw, True)
        assert liq_price is not None
        assert liq_price >= 0

    def test_non_negative_long(self):
        raw = _raw(margin=1000, perp_delta=1_000_000, usd_delta=10_000_000, liq_ratio=50000)
        liq_price = calculate_liquidation_price(raw, True)
        assert liq_price is not None
        assert liq_price >= 0


class TestIntegrationMetrics:
    def test_profitable_long(self):
        raw = _raw()
        mark_price = 60
        effective_margin = 110

        assert calculate_entry_price(raw) == 50
        assert calculate_position_size(raw) == 1
        assert calculate_position_value(raw, mark_price) == 60
        assert abs(calculate_leverage(60, effective_margin) - 0.545) < 0.01
        assert calculate_liquidation_price(raw, True) is not None

    def test_losing_short(self):
        raw = _raw(perp_delta=-2_000_000, usd_delta=-100_000_000)
        mark_price = 60
        effective_margin = 80

        assert calculate_entry_price(raw) == 50
        assert calculate_position_size(raw) == -2
        assert calculate_position_value(raw, mark_price) == 120
        assert calculate_leverage(120, effective_margin) == 1.5
        liq_price = calculate_liquidation_price(raw, False)
        assert liq_price is not None
        assert liq_price > 60
