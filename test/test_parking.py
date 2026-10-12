"""Tests for the parking lot management system."""

import pytest
from parking_system.parking_lot import ParkingLot
from parking_system.models import Vehicle, VehicleType


def test_empty_entry():
    """Test parking a vehicle in an empty parking lot."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 2})
    vehicle = Vehicle("C001", VehicleType.CAR)
    ticket = lot.park(vehicle)

    assert ticket is not None
    assert ticket.ticket_id is not None


def test_full_lot():
    """Test that parking fails when no car spots are available."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1})
    lot.park(Vehicle("C001", VehicleType.CAR))
    with pytest.raises(ValueError, match="No available car spot"):
        lot.park(Vehicle("C002", VehicleType.CAR))


def test_bus_contiguous_spots():
    """Test that a bus requires two consecutive parking spots."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1, VehicleType.BUS: 1})
    with pytest.raises(ValueError, match="No available bus spots"):
        lot.park(Vehicle("B001", VehicleType.BUS))


def test_hourly_pricing():
    """Test hourly pricing."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1}, pricing_type="hourly")
    ticket = lot.park(Vehicle("C001", VehicleType.CAR))
    visit = lot.exit_vehicle(ticket.ticket_id)

    assert visit.fee == 100.0


def test_flat_pricing():
    """Test flat-rate pricing."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1}, pricing_type="flat")
    ticket = lot.park(Vehicle("C001", VehicleType.CAR))
    visit = lot.exit_vehicle(ticket.ticket_id)

    assert visit.fee == 200.0


def test_history_multiple_cycles():
    """Test that multiple completed visits appear in history."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1})
    for _ in range(2):
        ticket = lot.park(Vehicle("C001", VehicleType.CAR))
        lot.exit_vehicle(ticket.ticket_id)
    history = lot.get_history("C001")

    assert len(history) == 2
    assert all(visit.plate == "C001" for visit in history)


def test_invalid_spot_configuration():
    """Test that an empty parking configuration raises an error."""
    lot = ParkingLot()
    with pytest.raises(
        ValueError,
        match="At least one vehicle type is required",
    ):
        lot.initialize({})


def test_exit_ticket_twice():
    """Test that a completed ticket cannot be used again."""
    lot = ParkingLot()
    lot.initialize({VehicleType.CAR: 1})
    ticket = lot.park(Vehicle("C001", VehicleType.CAR))
    lot.exit_vehicle(ticket.ticket_id)
    with pytest.raises(
        ValueError,
        match="Invalid or already-closed ticket ID",
    ):
        lot.exit_vehicle(ticket.ticket_id)
