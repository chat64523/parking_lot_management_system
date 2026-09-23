"""Pricing strategies for the parking lot management system."""

from abc import ABC, abstractmethod
from math import ceil
from models import VehicleType

HOURLY_RATES = {
    VehicleType.MOTORCYCLE: 50,
    VehicleType.CAR: 100,
    VehicleType.BUS: 200,
}

FLAT_RATES = {
    VehicleType.MOTORCYCLE: 100,
    VehicleType.CAR: 200,
    VehicleType.BUS: 400,
}


class PricingStrategy(ABC):
    """Define the interface for parking pricing strategies."""

    @abstractmethod
    def calculate(self, vehicle_type: VehicleType, minutes: int) -> float:
        """Calculate the parking fee."""
        raise NotImplementedError

    @abstractmethod
    def pricing_name(self) -> str:
        """Return the name of the pricing strategy."""
        raise NotImplementedError

class HourlyPricing(PricingStrategy):
    """Calculate parking fees based on hourly rates."""

    def calculate(self, vehicle_type: VehicleType, minutes: int) -> float:
        """Calculate the hourly parking fee."""
        hours = max(1, ceil(minutes / 60))
        return hours * HOURLY_RATES[vehicle_type]

    def pricing_name(self) -> str:
        """Return the pricing strategy name."""
        return "hourly"

class FlatPricing(PricingStrategy):
    """Calculate parking fees using fixed rates."""

    def calculate(self, vehicle_type: VehicleType, minutes: int) -> float:
        """Calculate the flat parking fee."""
        return FLAT_RATES[vehicle_type]

    def pricing_name(self) -> str:
        """Return the pricing strategy name."""
        return "flat"

def create_pricing(pricing_type: str = "hourly") -> PricingStrategy:
    """Create a pricing strategy based on the selected type."""
    if pricing_type == "hourly":
        return HourlyPricing()

    if pricing_type == "flat":
        return FlatPricing()

    raise ValueError(
        "Invalid pricing type. Use 'hourly' or 'flat'."
    )
