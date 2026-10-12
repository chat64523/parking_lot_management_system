"""Utility functions for validation."""

from datetime import datetime
from enum import Enum


def validate_vehicle_type(vehicle_type: Enum, vehicle_type_class: type[Enum]) -> None:
    """Validate that the vehicle type is valid."""
    try:
        if not isinstance(vehicle_type, vehicle_type_class):
            raise ValueError(
                "vehicle_type must be a valid VehicleType"
            )

    except ValueError as exc:
        raise exc


def validate_exit_time(entry_time: datetime, exit_time: datetime | None) -> None:
    """Validate that exit time is not before entry time."""
    try:
        if exit_time is not None and exit_time < entry_time:
            raise ValueError(
                "exit_time cannot be earlier than entry time"
            )

    except ValueError as exc:
        raise exc
