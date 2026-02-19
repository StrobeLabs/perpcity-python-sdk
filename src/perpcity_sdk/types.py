from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Bounds:
    min_margin: float
    min_taker_leverage: float
    max_taker_leverage: float
    liquidation_taker_ratio: float


@dataclass(frozen=True)
class Fees:
    creator_fee: float
    insurance_fee: float
    lp_fee: float
    liquidation_fee: float


@dataclass(frozen=True)
class LiveDetails:
    pnl: float
    funding_payment: float
    effective_margin: float
    is_liquidatable: bool


@dataclass(frozen=True)
class PerpData:
    id: str
    tick_spacing: int
    mark: float
    beacon: str
    bounds: Bounds
    fees: Fees


@dataclass(frozen=True)
class OpenPositionData:
    perp_id: str
    position_id: int
    live_details: LiveDetails
    is_long: bool | None = None
    is_maker: bool | None = None


@dataclass(frozen=True)
class MarginRatios:
    min: int
    max: int
    liq: int


@dataclass(frozen=True)
class PositionRawData:
    perp_id: str
    position_id: int
    margin: float
    entry_perp_delta: int
    entry_usd_delta: int
    margin_ratios: MarginRatios


@dataclass(frozen=True)
class UserData:
    wallet_address: str
    usdc_balance: float
    open_positions: list[OpenPositionData] = field(default_factory=list)


@dataclass(frozen=True)
class PoolKey:
    currency0: str
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str


@dataclass(frozen=True)
class PerpConfig:
    key: PoolKey
    creator: str
    vault: str
    beacon: str
    fees: str
    margin_ratios: str
    lockup_period: str
    sqrt_price_impact_limit: str


@dataclass(frozen=True)
class PerpCityDeployments:
    perp_manager: str
    usdc: str
    fees_module: str | None = None
    margin_ratios_module: str | None = None
    lockup_period_module: str | None = None
    sqrt_price_impact_limit_module: str | None = None


@dataclass
class OpenTakerPositionParams:
    is_long: bool
    margin: float
    leverage: float
    unspecified_amount_limit: int


@dataclass
class OpenMakerPositionParams:
    margin: float
    price_lower: float
    price_upper: float
    liquidity: int
    max_amt0_in: int
    max_amt1_in: int


@dataclass
class ClosePositionParams:
    min_amt0_out: float
    min_amt1_out: float
    max_amt1_in: float


@dataclass(frozen=True)
class ClosePositionResult:
    position: object | None
    tx_hash: str


@dataclass
class CreatePerpParams:
    starting_price: float
    beacon: str
    fees: str | None = None
    margin_ratios: str | None = None
    lockup_period: str | None = None
    sqrt_price_impact_limit: str | None = None
