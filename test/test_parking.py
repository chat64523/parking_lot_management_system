"""Tests for the parking lot management system."""

from models import Vehicle, VehicleType
from parking_lot import ParkingLot


def test_empty_entry():
    """Test parking a vehicle in an empty parking lot."""
    lot = ParkingLot()
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 2,
        VehicleType.BUS: 1
    })

    result = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    assert result.ticket_id == "T001"
    assert result.plate == "C001"
    assert result.vehicle_type == VehicleType.CAR
    assert result.spot_ids == ["C-01"]


def test_full_lot():
    """Test that parking fails when no spots are available."""
    lot = ParkingLot()
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 1,
        VehicleType.BUS: 1
    })

    first = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    assert first.ticket_id == "T001"

    try:
        lot.park(
            Vehicle("C002", VehicleType.CAR)
        )
        assert False, "Expected parking to fail"
    except ValueError as error:
        assert str(error) == "No available car spots"


def test_bus_contiguous_spots():
    """Test that buses receive consecutive parking spots."""
    lot = ParkingLot()
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 1,
        VehicleType.BUS: 2
    })

    first_bus = lot.park(
        Vehicle("B001", VehicleType.BUS)
    )

    assert first_bus.ticket_id == "T001"
    assert first_bus.spot_ids == ["B-01", "B-02"]

    try:
        lot.park(
            Vehicle("B002", VehicleType.BUS)
        )
        assert False, "Expected parking to fail"
    except ValueError as error:
        assert str(error) == "No available bus spots"


def test_hourly_pricing():
    """Test hourly parking pricing."""
    lot = ParkingLot(pricing_type="hourly")
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 1,
        VehicleType.BUS: 1
    })

    result = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    assert result.ticket_id == "T001"

    exit_result = lot.exit_vehicle(
        result.ticket_id
    )

    assert exit_result.ticket_id == "T001"
    assert exit_result.fee == 100.0


def test_flat_pricing():
    """Test flat parking pricing."""
    lot = ParkingLot(pricing_type="flat")
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 1,
        VehicleType.BUS: 1
    })

    result = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    assert result.ticket_id == "T001"

    exit_result = lot.exit_vehicle(
        result.ticket_id
    )

    assert exit_result.ticket_id == "T001"
    assert exit_result.fee == 200.0


def test_history_multiple_cycles():
    """Test parking history across multiple visits."""
    lot = ParkingLot()
    lot.initialize({
        VehicleType.MOTORCYCLE: 1,
        VehicleType.CAR: 1,
        VehicleType.BUS: 1
    })

    first = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    lot.exit_vehicle(first.ticket_id)

    second = lot.park(
        Vehicle("C001", VehicleType.CAR)
    )

    lot.exit_vehicle(second.ticket_id)

    history = lot.get_history("C001")

    assert len(history) == 2
    assert history[0].plate == "C001"
    assert history[1].plate == "C001"
