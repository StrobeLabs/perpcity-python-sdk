import math

from .constants import NUMBER_1E6, Q96


def price_to_sqrt_price_x96(price: float) -> int:
    if price <= 0:
        raise ValueError("Price must be positive")

    scaled_sqrt_price = math.sqrt(price) * NUMBER_1E6
    return (int(math.floor(scaled_sqrt_price)) * Q96) // NUMBER_1E6


def scale_6_decimals(amount: float) -> int:
    return int(math.floor(amount * NUMBER_1E6))


def scale_from_6_decimals(value: int) -> float:
    return value / NUMBER_1E6


def scale_to_x96(amount: float) -> int:
    return (scale_6_decimals(amount) * Q96) // NUMBER_1E6


def scale_from_x96(value_x96: int) -> float:
    value_scaled = (value_x96 * NUMBER_1E6) // Q96
    return value_scaled / NUMBER_1E6


def price_to_tick(price: float, round_down: bool) -> int:
    if price <= 0:
        raise ValueError("Price must be positive")
    log_price = math.log(price) / math.log(1.0001)
    return math.floor(log_price) if round_down else math.ceil(log_price)


def tick_to_price(tick: int) -> float:
    return 1.0001**tick


def sqrt_price_x96_to_price(sqrt_price_x96: int) -> float:
    price_x96 = (sqrt_price_x96 * sqrt_price_x96) // Q96
    return scale_from_x96(price_x96)


def margin_ratio_to_leverage(margin_ratio: int) -> float:
    if margin_ratio <= 0:
        raise ValueError("Margin ratio must be greater than 0")
    return NUMBER_1E6 / margin_ratio
