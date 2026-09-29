"""Utility functions for validation."""


def validate_vehicle_type(vehicle_type, vehicle_type_class):
    """Validate that the vehicle type is valid."""
    if not isinstance(vehicle_type, vehicle_type_class):
        raise ValueError(
            "vehicle_type must be a valid VehicleType"
        )

def validate_exit_time(entry_time, exit_time):
    """Validate that exit time is not before entry time."""
    if exit_time is not None and exit_time < entry_time:
        raise ValueError(
            "exit_time cannot be earlier than entry time"
        )
