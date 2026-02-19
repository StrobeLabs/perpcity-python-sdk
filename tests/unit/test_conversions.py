import pytest

from perpcity_sdk.utils.constants import Q96
from perpcity_sdk.utils.conversions import (
    margin_ratio_to_leverage,
    price_to_sqrt_price_x96,
    price_to_tick,
    scale_6_decimals,
    scale_from_6_decimals,
    scale_from_x96,
    scale_to_x96,
    sqrt_price_x96_to_price,
)


class TestPriceToSqrtPriceX96:
    def test_normal_prices(self):
        result = price_to_sqrt_price_x96(100)
        assert isinstance(result, int)
        assert result > 0

    def test_price_of_1(self):
        result = price_to_sqrt_price_x96(1)
        assert result == Q96

    def test_decimal_prices(self):
        result = price_to_sqrt_price_x96(0.5)
        assert result > 0
        assert result < Q96

    def test_negative_prices(self):
        with pytest.raises(ValueError, match="Price must be positive"):
            price_to_sqrt_price_x96(-10)

    def test_zero_price(self):
        with pytest.raises(ValueError, match="Price must be positive"):
            price_to_sqrt_price_x96(0)


class TestScale6Decimals:
    def test_normal_amounts(self):
        assert scale_6_decimals(100) == 100_000_000

    def test_decimal_amounts(self):
        assert scale_6_decimals(100.5) == 100_500_000

    def test_zero(self):
        assert scale_6_decimals(0) == 0

    def test_very_small_amounts(self):
        assert scale_6_decimals(0.000001) == 1

    def test_floor_fractional(self):
        assert scale_6_decimals(100.5555555) == 100_555_555

    def test_negative_amounts(self):
        assert scale_6_decimals(-100) == -100_000_000


class TestScaleToX96:
    def test_normal_amounts(self):
        result = scale_to_x96(100)
        expected = 100 * Q96
        assert result == expected

    def test_amount_of_1(self):
        result = scale_to_x96(1)
        assert result == Q96

    def test_decimal_amounts(self):
        result = scale_to_x96(0.5)
        assert result < Q96
        assert result > 0


class TestScaleFromX96:
    def test_normal_values(self):
        value_x96 = 100 * Q96
        result = scale_from_x96(value_x96)
        assert result == 100

    def test_q96_value(self):
        result = scale_from_x96(Q96)
        assert result == 1

    def test_fractional_values(self):
        value_x96 = Q96 // 2
        result = scale_from_x96(value_x96)
        assert abs(result - 0.5) < 1e-5

    def test_zero(self):
        result = scale_from_x96(0)
        assert result == 0


class TestPriceToTick:
    def test_round_down(self):
        price = 1.0001**100
        result = price_to_tick(price, True)
        assert 99 <= result <= 100

    def test_round_up(self):
        price = 1.0001**100.5
        result = price_to_tick(price, False)
        assert result == 101

    def test_price_of_1(self):
        assert price_to_tick(1, True) == 0
        assert price_to_tick(1, False) == 0

    def test_prices_less_than_1(self):
        result = price_to_tick(0.9999, True)
        assert result < 0

    def test_very_high_prices(self):
        price = 1.0001**100000
        result = price_to_tick(price, True)
        assert result == 100000

    def test_very_low_prices(self):
        price = 1.0001**-100000
        result = price_to_tick(price, True)
        assert -100001 <= result <= -99999

    def test_zero_and_negative(self):
        with pytest.raises(ValueError, match="Price must be positive"):
            price_to_tick(0, True)
        with pytest.raises(ValueError, match="Price must be positive"):
            price_to_tick(-1, True)


class TestSqrtPriceX96ToPrice:
    def test_normal_conversion(self):
        sqrt_price_x96 = 10 * Q96
        result = sqrt_price_x96_to_price(sqrt_price_x96)
        assert result == 100

    def test_sqrt_price_of_1(self):
        result = sqrt_price_x96_to_price(Q96)
        assert result == 1

    def test_fractional(self):
        sqrt_price_x96 = Q96 // 2
        result = sqrt_price_x96_to_price(sqrt_price_x96)
        assert abs(result - 0.25) < 1e-5

    def test_zero(self):
        result = sqrt_price_x96_to_price(0)
        assert result == 0

    def test_round_trip(self):
        original = 100
        sqrt_price_x96 = price_to_sqrt_price_x96(original)
        result = sqrt_price_x96_to_price(sqrt_price_x96)
        assert abs(result - original) < 1e-5


class TestMarginRatioToLeverage:
    def test_normal_conversion(self):
        assert margin_ratio_to_leverage(100000) == 10

    def test_1x_leverage(self):
        assert margin_ratio_to_leverage(1000000) == 1

    def test_high_leverage(self):
        assert margin_ratio_to_leverage(50000) == 20

    def test_zero_ratio(self):
        with pytest.raises(ValueError, match="Margin ratio must be greater than 0"):
            margin_ratio_to_leverage(0)

    def test_negative_ratio(self):
        with pytest.raises(ValueError, match="Margin ratio must be greater than 0"):
            margin_ratio_to_leverage(-100000)


class TestScaleFrom6Decimals:
    def test_normal(self):
        assert scale_from_6_decimals(100_000_000) == 100

    def test_1e6(self):
        assert scale_from_6_decimals(1_000_000) == 1

    def test_zero(self):
        assert scale_from_6_decimals(0) == 0

    def test_fractional(self):
        assert scale_from_6_decimals(500_000) == 0.5

    def test_very_small(self):
        assert scale_from_6_decimals(1) == 0.000001

    def test_round_trip(self):
        original = 100
        scaled = scale_6_decimals(original)
        result = scale_from_6_decimals(scaled)
        assert result == original

    def test_negative(self):
        assert scale_from_6_decimals(-100_000_000) == -100


class TestRoundTrips:
    def test_price_round_trips(self):
        prices = [0.1, 1, 10, 100]
        for price in prices:
            sqrt_price_x96 = price_to_sqrt_price_x96(price)
            result = sqrt_price_x96_to_price(sqrt_price_x96)
            tolerance = 3 if price > 100 else 5
            assert abs(result - price) < 10 ** (-tolerance), (
                f"Round trip failed for price {price}: got {result}"
            )

    def test_tick_round_trips(self):
        ticks = [-1000, -100, 0, 10, 100, 1000]
        for tick in ticks:
            price = 1.0001**tick
            result_tick = price_to_tick(price, True)
            assert abs(result_tick - tick) <= 1, (
                f"Round trip failed for tick {tick}: got {result_tick}"
            )
