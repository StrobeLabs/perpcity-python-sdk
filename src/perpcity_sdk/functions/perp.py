from ..types import Bounds, Fees, PerpData


def get_perp_mark(perp_data: PerpData) -> float:
    return perp_data.mark


def get_perp_beacon(perp_data: PerpData) -> str:
    return perp_data.beacon


def get_perp_bounds(perp_data: PerpData) -> Bounds:
    return perp_data.bounds


def get_perp_fees(perp_data: PerpData) -> Fees:
    return perp_data.fees


def get_perp_tick_spacing(perp_data: PerpData) -> int:
    return perp_data.tick_spacing
