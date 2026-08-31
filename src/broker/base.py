from abc import ABC, abstractmethod


class BrokerAdapter(ABC):
    """Interface for broker data access. V1 never sends real orders."""

    @abstractmethod
    def get_account(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> list[dict]:
        raise NotImplementedError

    def place_order(self, *args, **kwargs):
        raise RuntimeError("Real order execution is disabled in V1")
