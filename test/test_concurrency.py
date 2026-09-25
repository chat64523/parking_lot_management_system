"""Tests for parking lot concurrency."""

from models import VehicleType
from parking_lot import ParkingLot


def test_concurrency_stress():
    """Test concurrent vehicle parking."""
    lot = ParkingLot()

    lot.initialize({
        VehicleType.MOTORCYCLE: 0,
        VehicleType.CAR: 20,
        VehicleType.BUS: 0
    })

    result = lot.stress_test(
        concurrent=50,
        vehicle_type=VehicleType.CAR
    )

    assert result["successful"] == 20
    assert result["rejected"] == 30
    assert result["spot_conflicts"] == 0
