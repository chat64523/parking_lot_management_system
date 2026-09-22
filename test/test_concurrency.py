from parking_lot import ParkingLot
from models import Vehicle

def test_concurrency_stress():
    lot = ParkingLot()
    lot.initialize({
        "motorcycle": 0,
        "car": 20,
        "bus": 0
    })
    result = lot.stress_test(
        concurrent=50,
        vehicle_type="car"
    )
    assert result["successful"] == 20
    assert result["rejected"] == 30
    assert result["spot_conflicts"] == 0





    