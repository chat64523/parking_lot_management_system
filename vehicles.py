"""Vehicle types and validation for the parking lot system."""

from models import VehicleType

VEHICLE_TYPES = {
    VehicleType.MOTORCYCLE: {
        "prefix": "M",
        "spots_required": 1,
    },
    VehicleType.CAR: {
        "prefix": "C",
        "spots_required": 1,
    },
    VehicleType.BUS: {
        "prefix": "B",
        "spots_required": 2,
    },
}

def validate_vehicle_type(vehicle_type: VehicleType) -> None:
    """Validate that the vehicle type is supported."""
    if not isinstance(vehicle_type, VehicleType):
        raise ValueError(
            f"Invalid vehicle type: {vehicle_type}. "
            "Use motorcycle, car, or bus."
        )

def get_vehicle_prefix(vehicle_type: VehicleType) -> str:
    """Return the prefix assigned to a vehicle type."""
    validate_vehicle_type(vehicle_type)
    return VEHICLE_TYPES[vehicle_type]["prefix"]

def get_spots_required(vehicle_type: VehicleType) -> int:
    """Return the number of parking spots required."""
    validate_vehicle_type(vehicle_type)
    return VEHICLE_TYPES[vehicle_type]["spots_required"]
