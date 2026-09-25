"""Data models for the parking lot management system."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from utils import validate_vehicle_type, validate_exit_time


class VehicleType(str, Enum):
    """Represent the supported vehicle types."""

    MOTORCYCLE = "motorcycle"
    CAR = "car"
    BUS = "bus"

@dataclass
class Vehicle:
    """Represent a vehicle entering the parking lot."""

    plate: str
    vehicle_type: VehicleType

    def __post_init__(self):
        """Validate the vehicle type."""
        validate_vehicle_type(self.vehicle_type, VehicleType)


@dataclass
class Spot:
    """Represent a parking spot."""

    spot_id: str
    vehicle_type: VehicleType
    occupied: bool = False
    ticket_id: str | None = None

    def __post_init__(self):
        """Validate the parking spot."""
        validate_vehicle_type(self.vehicle_type, VehicleType)

        if self.occupied and self.ticket_id is None:
            raise ValueError(
                "An occupied spot must have a ticket_id"
            )


@dataclass(frozen=True)
class Ticket:
    """Represent an active or completed parking ticket."""

    ticket_id: str
    plate: str
    vehicle_type: VehicleType
    spot_ids: list[str]
    entry_time: datetime
    exit_time: datetime | None = None
    fee: float | None = None

    def __post_init__(self):
        """Validate the parking ticket."""
        validate_vehicle_type(self.vehicle_type, VehicleType)
        validate_exit_time(self.entry_time, self.exit_time)

    @property
    def active(self) -> bool:
        """Return True when the ticket is still active."""
        return self.exit_time is None


@dataclass(frozen=True)
class Visit(Ticket):
    """Represent a completed parking visit."""

    duration_minutes: int = 0

    def __post_init__(self):
        """Validate the completed parking visit."""
        super().__post_init__()

        if self.exit_time is None:
            raise ValueError(
                "A completed visit must have an exit_time"
            )

        if self.duration_minutes < 0:
            raise ValueError(
                "duration_minutes cannot be negative"
            )
