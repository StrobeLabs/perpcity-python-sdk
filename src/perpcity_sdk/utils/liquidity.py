import math

from .conversions import sqrt_price_x96_to_price, tick_to_price


def get_sqrt_ratio_at_tick(tick: int) -> int:
    abs_tick = abs(tick)

    ratio = (
        0xFFFCB933BD6FAD37AA2D162D1A594001
        if abs_tick & 0x1
        else 0x100000000000000000000000000000000
    )
    if abs_tick & 0x2:
        ratio = (ratio * 0xFFF97272373D413259A46990580E213A) >> 128
    if abs_tick & 0x4:
        ratio = (ratio * 0xFFF2E50F5F656932EF12357CF3C7FDCC) >> 128
    if abs_tick & 0x8:
        ratio = (ratio * 0xFFE5CACA7E10E4E61C3624EAA0941CD0) >> 128
    if abs_tick & 0x10:
        ratio = (ratio * 0xFFCB9843D60F6159C9DB58835C926644) >> 128
    if abs_tick & 0x20:
        ratio = (ratio * 0xFF973B41FA98C081472E6896DFB254C0) >> 128
    if abs_tick & 0x40:
        ratio = (ratio * 0xFF2EA16466C96A3843EC78B326B52861) >> 128
    if abs_tick & 0x80:
        ratio = (ratio * 0xFE5DEE046A99A2A811C461F1969C3053) >> 128
    if abs_tick & 0x100:
        ratio = (ratio * 0xFCBE86C7900A88AEDCFFC83B479AA3A4) >> 128
    if abs_tick & 0x200:
        ratio = (ratio * 0xF987A7253AC413176F2B074CF7815E54) >> 128
    if abs_tick & 0x400:
        ratio = (ratio * 0xF3392B0822B70005940C7A398E4B70F3) >> 128
    if abs_tick & 0x800:
        ratio = (ratio * 0xE7159475A2C29B7443B29C7FA6E889D9) >> 128
    if abs_tick & 0x1000:
        ratio = (ratio * 0xD097F3BDFD2022B8845AD8F792AA5825) >> 128
    if abs_tick & 0x2000:
        ratio = (ratio * 0xA9F746462D870FDF8A65DC1F90E061E5) >> 128
    if abs_tick & 0x4000:
        ratio = (ratio * 0x70D869A156D2A1B890BB3DF62BAF32F7) >> 128
    if abs_tick & 0x8000:
        ratio = (ratio * 0x31BE135F97D08FD981231505542FCFA6) >> 128
    if abs_tick & 0x10000:
        ratio = (ratio * 0x9AA508B5B7A84E1C677DE54F3E99BC9) >> 128
    if abs_tick & 0x20000:
        ratio = (ratio * 0x5D6AF8DEDB81196699C329225EE604) >> 128
    if abs_tick & 0x40000:
        ratio = (ratio * 0x2216E584F5FA1EA926041BEDFE98) >> 128
    if abs_tick & 0x80000:
        ratio = (ratio * 0x48A170391F7DC42444E8FA2) >> 128

    if tick > 0:
        ratio = (1 << 256) // ratio

    return ratio >> 32


def estimate_liquidity(tick_lower: int, tick_upper: int, usd_scaled: int) -> int:
    if tick_lower >= tick_upper:
        raise ValueError(
            f"Invalid tick range: tick_lower ({tick_lower}) "
            f"must be less than tick_upper ({tick_upper})"
        )

    if usd_scaled == 0:
        return 0

    q96 = 1 << 96

    sqrt_price_lower_x96 = get_sqrt_ratio_at_tick(tick_lower)
    sqrt_price_upper_x96 = get_sqrt_ratio_at_tick(tick_upper)

    sqrt_price_diff = sqrt_price_upper_x96 - sqrt_price_lower_x96

    if sqrt_price_diff == 0:
        raise ValueError(
            f"Division by zero: sqrt_price_diff is 0 for ticks {tick_lower} to {tick_upper}. "
            f"sqrt_lower={sqrt_price_lower_x96}, sqrt_upper={sqrt_price_upper_x96}"
        )

    return (usd_scaled * q96) // sqrt_price_diff


def calculate_liquidity_for_target_ratio(
    margin_scaled: int,
    tick_lower: int,
    tick_upper: int,
    current_sqrt_price_x96: int,
    target_margin_ratio: float,
) -> int:
    if tick_lower >= tick_upper:
        raise ValueError(
            f"Invalid tick range: tick_lower ({tick_lower}) "
            f"must be less than tick_upper ({tick_upper})"
        )

    if margin_scaled == 0:
        return 0

    if target_margin_ratio <= 0:
        raise ValueError(f"Invalid target margin ratio: {target_margin_ratio} must be positive")

    price_lower = tick_to_price(tick_lower)
    price_upper = tick_to_price(tick_upper)
    current_price = sqrt_price_x96_to_price(current_sqrt_price_x96)

    sqrt_current = math.sqrt(current_price)
    sqrt_lower = math.sqrt(price_lower)
    sqrt_upper = math.sqrt(price_upper)

    if current_price <= price_lower:
        amount0_per_l = 1 / sqrt_lower - 1 / sqrt_upper
        debt_per_l = amount0_per_l * current_price
    elif current_price >= price_upper:
        debt_per_l = sqrt_upper - sqrt_lower
    else:
        amount0_per_l = 1 / sqrt_current - 1 / sqrt_upper
        amount1_per_l = sqrt_current - sqrt_lower
        debt_per_l = amount0_per_l * current_price + amount1_per_l

    if debt_per_l <= 0:
        raise ValueError("Calculated debt per unit liquidity is zero or negative")

    margin = margin_scaled / 1e6
    target_debt = margin / target_margin_ratio
    liquidity = target_debt / debt_per_l

    if liquidity <= 0:
        raise ValueError("Calculated liquidity is zero or negative")

    return int(math.floor(liquidity))
