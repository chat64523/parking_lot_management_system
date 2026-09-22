"""Vehicle types and validation for the parking lot system."""

VEHICLE_TYPES = {
    "motorcycle": {
        "prefix": "M",
        "spots_required": 1,
    },
    "car": {
        "prefix": "C",
        "spots_required": 1,
    },
    "bus": {
        "prefix": "B",
        "spots_required": 2,
    },
}


def validate_vehicle_type(vehicle_type: str) -> None:
    """Validate that the vehicle type is supported."""
    if vehicle_type not in VEHICLE_TYPES:
        raise ValueError(
            f"Invalid vehicle type: {vehicle_type}. "
            "Use motorcycle, car, or bus."
        )


def get_vehicle_prefix(vehicle_type: str) -> str:
    """Return the prefix assigned to a vehicle type."""
    validate_vehicle_type(vehicle_type)
    return VEHICLE_TYPES[vehicle_type]["prefix"]


def get_spots_required(vehicle_type: str) -> int:
    """Return the number of parking spots required."""
    validate_vehicle_type(vehicle_type)
    return VEHICLE_TYPES[vehicle_type]["spots_required"]
