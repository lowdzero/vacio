from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    initial_cash_eur: float = 2.50
    min_liquidity_ratio: float = 0.90
    max_position_ratio: float = 0.10
    max_drawdown_ratio: float = 0.05
    simulation_only: bool = True
    real_orders_enabled: bool = False


CONFIG = BotConfig()
