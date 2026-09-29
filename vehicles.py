"""Vehicle types and validation for the parking lot system."""

from models import VehicleType
from utils import validate_vehicle_type

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

def get_vehicle_prefix(vehicle_type: VehicleType) -> str:
    """Return the prefix assigned to a vehicle type."""
    validate_vehicle_type(vehicle_type, VehicleType)
    return VEHICLE_TYPES[vehicle_type]["prefix"]

def get_spots_required(vehicle_type: VehicleType) -> int:
    """Return the number of parking spots required."""
    validate_vehicle_type(vehicle_type, VehicleType)
    return VEHICLE_TYPES[vehicle_type]["spots_required"]
