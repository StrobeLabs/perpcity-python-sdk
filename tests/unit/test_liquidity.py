import pytest

from perpcity_sdk.utils.liquidity import estimate_liquidity


class TestEstimateLiquidity:
    def test_normal_tick_range(self):
        liquidity = estimate_liquidity(-1000, 1000, 1_000_000_000)
        assert liquidity > 0
        assert isinstance(liquidity, int)

    def test_around_current_price(self):
        liquidity = estimate_liquidity(-100, 100, 100_000_000)
        assert liquidity > 0

    def test_zero_to_positive(self):
        liquidity = estimate_liquidity(0, 1000, 1_000_000_000)
        assert liquidity > 0

    def test_negative_range(self):
        liquidity = estimate_liquidity(-2000, -1000, 500_000_000)
        assert liquidity > 0

    def test_very_wide_range(self):
        liquidity = estimate_liquidity(-10000, 10000, 10_000_000_000)
        assert liquidity > 0

    def test_very_narrow_range(self):
        liquidity = estimate_liquidity(0, 10, 100_000_000)
        assert liquidity > 0

    def test_small_usd(self):
        liquidity = estimate_liquidity(-100, 100, 1_000_000)
        assert liquidity > 0

    def test_very_small_usd(self):
        liquidity = estimate_liquidity(-100, 100, 1000)
        assert isinstance(liquidity, int)

    def test_large_usd(self):
        liquidity = estimate_liquidity(-1000, 1000, 1_000_000_000_000)
        assert liquidity > 0

    def test_zero_usd(self):
        liquidity = estimate_liquidity(-100, 100, 0)
        assert liquidity == 0

    def test_invalid_range_lower_gt_upper(self):
        with pytest.raises(
            ValueError,
            match=r"Invalid tick range: tick_lower \(1000\) must be less than tick_upper \(-1000\)",
        ):
            estimate_liquidity(1000, -1000, 1_000_000_000)

    def test_invalid_range_equal(self):
        with pytest.raises(
            ValueError,
            match="Invalid tick range: tick_lower \\(100\\) must be less than tick_upper \\(100\\)",
        ):
            estimate_liquidity(100, 100, 1_000_000_000)

    def test_extreme_positive_ticks(self):
        liquidity = estimate_liquidity(100000, 200000, 1_000_000_000)
        assert liquidity > 0

    def test_extreme_negative_ticks(self):
        liquidity = estimate_liquidity(-200000, -100000, 1_000_000_000)
        assert liquidity > 0

    def test_narrower_range_higher_liquidity(self):
        usd = 1_000_000_000
        wide = estimate_liquidity(-1000, 1000, usd)
        narrow = estimate_liquidity(-100, 100, usd)
        assert narrow > wide

    def test_proportional_usd(self):
        liq_1x = estimate_liquidity(-500, 500, 1_000_000_000)
        liq_2x = estimate_liquidity(-500, 500, 2_000_000_000)
        ratio = liq_2x / liq_1x
        assert abs(ratio - 2.0) < 0.1

    def test_tick_spacing_boundaries(self):
        tick_spacing = 60
        liquidity = estimate_liquidity(-1000 * tick_spacing, 1000 * tick_spacing, 1_000_000_000)
        assert liquidity > 0

    def test_asymmetric_range(self):
        liquidity = estimate_liquidity(-5000, 1000, 1_000_000_000)
        assert liquidity > 0


class TestGetSqrtRatioAtTickIndirect:
    def test_symmetric_ticks(self):
        usd = 1_000_000_000
        liq_pos = estimate_liquidity(0, 1000, usd)
        liq_neg = estimate_liquidity(-1000, 0, usd)
        assert liq_pos > 0
        assert liq_neg > 0

    def test_tick_zero(self):
        liquidity = estimate_liquidity(-100, 100, 1_000_000_000)
        assert liquidity > 0

    def test_bit_flags(self):
        test_ticks = [10, 100, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
        for tick in test_ticks:
            liquidity = estimate_liquidity(0, tick, 1_000_000_000)
            assert liquidity >= 0
            assert isinstance(liquidity, int)


class TestEdgeCases:
    def test_minimum_liquidity(self):
        liquidity = estimate_liquidity(-100, 100, 1)
        assert isinstance(liquidity, int)

    def test_precision(self):
        liquidity = estimate_liquidity(-1000, 1000, 123_456_789)
        assert liquidity > 0
        assert len(str(liquidity)) > 1
