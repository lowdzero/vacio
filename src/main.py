from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Portfolio:
    cash: float = 2.50
    positions: dict[str, float] = field(default_factory=dict)
    transactions: list[dict] = field(default_factory=list)

    @property
    def total_value(self) -> float:
        return self.cash + sum(self.positions.values())

    @property
    def liquidity_ratio(self) -> float:
        total = self.total_value
        return self.cash / total if total else 1.0

    def snapshot(self) -> dict:
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "cash_eur": round(self.cash, 2),
            "invested_eur": round(sum(self.positions.values()), 2),
            "total_eur": round(self.total_value, 2),
            "liquidity_ratio": round(self.liquidity_ratio, 4),
        }


def main() -> None:
    portfolio = Portfolio()
    print("TR Portfolio Bot — V1 SIMULATION")
    print("WARNING: no real broker connection or orders are enabled.")
    print(portfolio.snapshot())
    print("Strategy status: HOLD / preserve capital")
    print("Liquidity target: 90–100%")


if __name__ == "__main__":
    main()
