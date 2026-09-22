"""Pricing strategies for the parking lot management system."""

from abc import ABC, abstractmethod
from math import ceil

# pylint: disable=too-few-public-methods

RATES = {
    "motorcycle": 50,
    "car": 100,
    "bus": 200,
}


class PricingStrategy(ABC):
    """Define the interface for parking pricing strategies."""

    @abstractmethod
    def calculate(self, vehicle_type: str, minutes: int) -> float:
        """Calculate the parking fee."""
        raise NotImplementedError


class HourlyPricing(PricingStrategy):
    """Calculate parking fees based on hourly rates."""

    def calculate(self, vehicle_type: str, minutes: int) -> float:
        """Calculate the hourly parking fee."""
        hours = max(1, ceil(minutes / 60))
        return hours * RATES[vehicle_type]


class FlatPricing(PricingStrategy):
    """Calculate parking fees using fixed rates."""

    def calculate(self, vehicle_type: str, minutes: int) -> float:
        """Calculate the flat parking fee."""
        flat_rates = {
            "motorcycle": 100,
            "car": 200,
            "bus": 400,
        }
        return flat_rates[vehicle_type]


def create_pricing(pricing_type: str = "hourly") -> PricingStrategy:
    """Create a pricing strategy based on the selected type."""
    if pricing_type == "hourly":
        return HourlyPricing()

    if pricing_type == "flat":
        return FlatPricing()

    raise ValueError("Invalid pricing type. Use 'hourly' or 'flat'.")
