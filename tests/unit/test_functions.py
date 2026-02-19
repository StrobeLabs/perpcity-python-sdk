from perpcity_sdk.functions.perp import (
    get_perp_beacon,
    get_perp_bounds,
    get_perp_fees,
    get_perp_mark,
    get_perp_tick_spacing,
)
from perpcity_sdk.functions.position import (
    get_position_effective_margin,
    get_position_funding_payment,
    get_position_id,
    get_position_is_liquidatable,
    get_position_is_long,
    get_position_is_maker,
    get_position_live_details,
    get_position_perp_id,
    get_position_pnl,
)
from perpcity_sdk.functions.user import (
    get_user_open_positions,
    get_user_usdc_balance,
    get_user_wallet_address,
)
from perpcity_sdk.types import (
    Bounds,
    Fees,
    LiveDetails,
    OpenPositionData,
    PerpData,
    UserData,
)


class TestPerpAccessors:
    def setup_method(self):
        self.perp = PerpData(
            id="0xabc",
            tick_spacing=60,
            mark=50.5,
            beacon="0xbeacon",
            bounds=Bounds(
                min_margin=10,
                min_taker_leverage=1.5,
                max_taker_leverage=20.0,
                liquidation_taker_ratio=0.05,
            ),
            fees=Fees(
                creator_fee=0.001,
                insurance_fee=0.0005,
                lp_fee=0.003,
                liquidation_fee=0.01,
            ),
        )

    def test_get_perp_mark(self):
        assert get_perp_mark(self.perp) == 50.5

    def test_get_perp_beacon(self):
        assert get_perp_beacon(self.perp) == "0xbeacon"

    def test_get_perp_bounds(self):
        bounds = get_perp_bounds(self.perp)
        assert bounds.min_margin == 10
        assert bounds.max_taker_leverage == 20.0

    def test_get_perp_fees(self):
        fees = get_perp_fees(self.perp)
        assert fees.creator_fee == 0.001
        assert fees.lp_fee == 0.003

    def test_get_perp_tick_spacing(self):
        assert get_perp_tick_spacing(self.perp) == 60


class TestPositionAccessors:
    def setup_method(self):
        self.pos = OpenPositionData(
            perp_id="0xabc",
            position_id=42,
            is_long=True,
            is_maker=False,
            live_details=LiveDetails(
                pnl=10.5,
                funding_payment=-0.3,
                effective_margin=110.5,
                is_liquidatable=False,
            ),
        )

    def test_get_position_perp_id(self):
        assert get_position_perp_id(self.pos) == "0xabc"

    def test_get_position_id(self):
        assert get_position_id(self.pos) == 42

    def test_get_position_is_long(self):
        assert get_position_is_long(self.pos) is True

    def test_get_position_is_maker(self):
        assert get_position_is_maker(self.pos) is False

    def test_get_position_live_details(self):
        details = get_position_live_details(self.pos)
        assert details.pnl == 10.5

    def test_get_position_pnl(self):
        assert get_position_pnl(self.pos) == 10.5

    def test_get_position_funding_payment(self):
        assert get_position_funding_payment(self.pos) == -0.3

    def test_get_position_effective_margin(self):
        assert get_position_effective_margin(self.pos) == 110.5

    def test_get_position_is_liquidatable(self):
        assert get_position_is_liquidatable(self.pos) is False


class TestUserAccessors:
    def setup_method(self):
        self.user = UserData(
            wallet_address="0xuser",
            usdc_balance=1000.5,
            open_positions=[
                OpenPositionData(
                    perp_id="0xabc",
                    position_id=1,
                    live_details=LiveDetails(
                        pnl=5.0, funding_payment=0.0, effective_margin=105.0, is_liquidatable=False
                    ),
                )
            ],
        )

    def test_get_user_usdc_balance(self):
        assert get_user_usdc_balance(self.user) == 1000.5

    def test_get_user_open_positions(self):
        positions = get_user_open_positions(self.user)
        assert len(positions) == 1
        assert positions[0].position_id == 1

    def test_get_user_wallet_address(self):
        assert get_user_wallet_address(self.user) == "0xuser"
