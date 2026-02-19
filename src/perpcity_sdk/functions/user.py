from ..types import OpenPositionData, UserData


def get_user_usdc_balance(user_data: UserData) -> float:
    return user_data.usdc_balance


def get_user_open_positions(user_data: UserData) -> list[OpenPositionData]:
    return user_data.open_positions


def get_user_wallet_address(user_data: UserData) -> str:
    return user_data.wallet_address
