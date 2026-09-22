"""Data models for the parking lot management system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# pylint: disable=too-many-instance-attributes


@dataclass
class Vehicle:
    """Represent a vehicle entering the parking lot."""

    plate: str
    vehicle_type: str


@dataclass
class Spot:
    """Represent a parking spot."""

    spot_id: str
    vehicle_type: str
    occupied: bool = False
    ticket_id: Optional[str] = None


@dataclass
class Ticket:
    """Represent an active or completed parking ticket."""

    ticket_id: str
    plate: str
    vehicle_type: str
    spot_ids: list[str]
    entry_time: datetime
    exit_time: Optional[datetime] = None
    fee: Optional[float] = None

    @property
    def active(self) -> bool:
        """Return True when the ticket is still active."""
        return self.exit_time is None


@dataclass
class Visit:
    """Represent a completed parking visit."""

    ticket_id: str
    plate: str
    vehicle_type: str
    spot_ids: list[str]
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    fee: float
