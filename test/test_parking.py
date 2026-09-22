from parking_lot import ParkingLot
from models import Vehicle

def test_empty_entry():
    lot = ParkingLot()
    lot.initialize({
        "motorcycle": 1,
        "car": 2,
        "bus": 1
    })
    result = lot.park(Vehicle("C001", "car"))
    assert result.ticket_id == "T001"
    assert result.plate == "C001"
    assert result.vehicle_type == "car"
    assert result.spot_ids == ["C-01"]

def test_full_lot():
    lot = ParkingLot()
    lot.initialize({
        "motorcycle": 1,
        "car": 1,
        "bus": 1
    })

    first = lot.park(Vehicle("C001", "car"))
    assert first.ticket_id == "T001"

    try:
        lot.park(Vehicle("C002", "car"))
        assert False, "Expected parking to fail"
    except ValueError as error:
        assert str(error) == "No available car spot"

def test_bus_contiguous_spots():
    lot = ParkingLot()
    lot.initialize({
        "motorcycle": 1,
        "car": 1,
        "bus": 2
    })

    first_bus = lot.park(
        Vehicle("B001", "bus")
    )
    assert first_bus.ticket_id == "T001"
    assert first_bus.spot_ids == ["B-01", "B-02"]

    try:
        lot.park(Vehicle("B002", "bus"))
        assert False, "Expected parking to fail"
    except ValueError as error:
        assert str(error) == "No available bus spots"

def test_hourly_pricing():
    lot = ParkingLot(pricing_type="hourly")
    lot.initialize({
        "motorcycle": 1,
        "car": 1,
        "bus": 1
    })
    result = lot.park(
        Vehicle("C001", "car")
    )
    assert result.ticket_id == "T001"
    exit_result = lot.exit_vehicle(
        result.ticket_id
    )
    assert exit_result.ticket_id == "T001"
    assert exit_result.fee == 100.0

def test_flat_pricing():
    lot = ParkingLot(pricing_type="flat")
    lot.initialize({
        "motorcycle": 1,
        "car": 1,
        "bus": 1
    })
    result = lot.park(
        Vehicle("C001", "car")
    )
    assert result.ticket_id == "T001"
    exit_result = lot.exit_vehicle(
        result.ticket_id
    )
    assert exit_result.ticket_id == "T001"
    assert exit_result.fee == 200.0

def test_history_multiple_cycles():
    lot = ParkingLot()
    lot.initialize({
        "motorcycle": 1,
        "car": 1,
        "bus": 1
    })
    first = lot.park(
        Vehicle("C001", "car")
    )
    lot.exit_vehicle(
        first.ticket_id
    )
    second = lot.park(
        Vehicle("C001", "car")
    )
    lot.exit_vehicle(
        second.ticket_id
    )
    history = lot.get_history("C001")

    assert len(history) == 2
    assert history[0].plate == "C001"
    assert history[1].plate == "C001"