"""Pricing strategies for the parking lot management system."""

from abc import ABC, abstractmethod
from math import ceil
from parking_system.models import VehicleType
from parking_system.utils import validate_vehicle_type


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
        try:
            validate_vehicle_type(vehicle_type, VehicleType)
            if not isinstance(minutes, int) or isinstance(minutes, bool):
                raise TypeError("minutes must be an integer")

            if minutes < 0:
                raise ValueError("minutes cannot be negative")

            hours = max(1, ceil(minutes / 60))
            fee = hours * HOURLY_RATES[vehicle_type]

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Unable to calculate hourly fee: {exc}"
            ) from exc

        return float(fee)

    def pricing_name(self) -> str:
        """Return the pricing strategy name."""
        return "hourly"


class FlatPricing(PricingStrategy):
    """Calculate parking fees using fixed rates."""

    def calculate(self, vehicle_type: VehicleType, minutes: int) -> float:
        """Calculate the flat parking fee."""
        try:
            validate_vehicle_type(vehicle_type, VehicleType)
            if not isinstance(minutes, int) or isinstance(minutes, bool):
                raise TypeError("minutes must be an integer")

            if minutes < 0:
                raise ValueError("minutes cannot be negative")

            fee = FLAT_RATES[vehicle_type]

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Unable to calculate flat fee: {exc}"
            ) from exc

        return float(fee)

    def pricing_name(self) -> str:
        """Return the pricing strategy name."""
        return "flat"


def create_pricing(pricing_type: str = "hourly") -> PricingStrategy:
    """Create a pricing strategy based on the selected type."""
    try:
        if not isinstance(pricing_type, str):
            raise TypeError("pricing_type must be a string")

        if pricing_type == "hourly":
            strategy = HourlyPricing()
        elif pricing_type == "flat":
            strategy = FlatPricing()
        else:
            raise ValueError(
                "Invalid pricing type. Use 'hourly' or 'flat'."
            )

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Unable to create pricing strategy: {exc}"
        ) from exc

    return strategy
