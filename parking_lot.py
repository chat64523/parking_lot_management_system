"""Core parking lot management logic."""

import threading
from dataclasses import replace
from datetime import datetime

from models import Spot, Ticket, Vehicle, Visit, VehicleType
from pricing import create_pricing
from storage import Storage
from vehicles import get_spots_required, get_vehicle_prefix,validate_vehicle_type

class ParkingLot:
    """Manage parking spots, tickets, vehicle entry, and exits."""

    def __init__(self, pricing_type=None):
        """Initialize an empty parking lot."""
        self.storage = Storage()
        self.pricing = None
        self.pricing_type = pricing_type
        self.initialized = False
        self.ticket_counter = 0
        self.lock = threading.Lock()

    @property
    def spots(self):
        """Return all parking spots."""
        return self.storage.spots

    @property
    def tickets(self):
        """Return all parking tickets."""
        return self.storage.tickets

    @property
    def history(self):
        """Return parking visit history."""
        return self.storage.history

    def _create_spots(self, vehicle_type, spot_count):
        """Create parking spots for a vehicle type."""
        validate_vehicle_type(vehicle_type)
        prefix = get_vehicle_prefix(vehicle_type)

        for number in range(1, spot_count + 1):
            spot_id = f"{prefix}-{number:02d}"
            self.storage.save_spot(
                Spot(
                    spot_id=spot_id,
                    vehicle_type=vehicle_type,
                )
            )

    def initialize(self, spot_config: dict, pricing_type=None):
        """Initialize parking spots and select the pricing strategy."""
        if not spot_config:
            raise ValueError("At least one vehicle type is required")

        if pricing_type is not None:
            self.pricing_type = pricing_type

        if self.pricing_type is None:
            self.pricing_type = "hourly"

        pricing = create_pricing(self.pricing_type)

        with self.lock:
            self.storage.spots.clear()
            self.storage.tickets.clear()
            self.storage.history.clear()
            self.ticket_counter = 0

            for vehicle_type, spot_count in spot_config.items():
                self._create_spots(vehicle_type, spot_count)

            self.pricing = pricing
            self.initialized = True

    def _require_initialized(self):
        """Ensure the parking lot has been initialized."""
        if not self.initialized:
            raise ValueError("Parking lot is not initialized")

    def _get_spot_number(self, spot_id):
        """Extract the numeric part of a parking spot ID."""
        try:
            return int(spot_id.split("-", 1)[1])
        except (IndexError, ValueError) as exc:
            raise ValueError(
                f"Invalid spot ID format: {spot_id}"
            ) from exc

    def _find_available_spots(self, vehicle_type):
        """Find available consecutive spots for a vehicle."""
        required = get_spots_required(vehicle_type)

        available_spots = sorted(
            (
                spot
                for spot in self.spots.values()
                if spot.vehicle_type == vehicle_type
                and not spot.occupied
            ),
            key=lambda spot: self._get_spot_number(spot.spot_id),
        )

        if len(available_spots) < required:
            raise ValueError(
                f"No available {vehicle_type.value} spots"
            )

        if required == 1:
            return [available_spots[0]]

        consecutive_spots = [available_spots[0]]

        for spot in available_spots[1:]:
            previous_number = self._get_spot_number(
                consecutive_spots[-1].spot_id
            )
            current_number = self._get_spot_number(
                spot.spot_id
            )

            if current_number == previous_number + 1:
                consecutive_spots.append(spot)

                if len(consecutive_spots) == required:
                    return consecutive_spots
            else:
                consecutive_spots = [spot]

        raise ValueError(
            f"No available consecutive {vehicle_type.value} spots"
        )

    def park(self, vehicle):
        """Park a vehicle and create a parking ticket."""
        self._require_initialized()
        validate_vehicle_type(vehicle.vehicle_type)

        with self.lock:
            selected_spots = self._find_available_spots(
                vehicle.vehicle_type
            )

            next_ticket_number = self.ticket_counter + 1
            ticket_id = f"T{next_ticket_number:03d}"
            entry_time = datetime.now()

            ticket = Ticket(
                ticket_id=ticket_id,
                plate=vehicle.plate,
                vehicle_type=vehicle.vehicle_type,
                spot_ids=[
                    spot.spot_id
                    for spot in selected_spots
                ],
                entry_time=entry_time,
            )

            self.storage.save_ticket(ticket)

            self.ticket_counter = next_ticket_number

            for spot in selected_spots:
                spot.occupied = True
                spot.ticket_id = ticket_id

            return ticket

    def exit_vehicle(self, ticket_id):
        """Exit a vehicle and calculate its parking fee."""
        self._require_initialized()

        with self.lock:
            ticket = self.tickets.get(ticket_id)

            if ticket is None or not ticket.active:
                raise ValueError(
                    "Invalid or already-closed ticket ID"
                )

            exit_time = datetime.now()
            duration = max(
                0,
                int(
                    (
                        exit_time - ticket.entry_time
                    ).total_seconds() // 60
                ),
            )

            fee = self.pricing.calculate(
                ticket.vehicle_type,
                duration,
            )

            completed_ticket = replace(
                ticket,
                exit_time=exit_time,
                fee=fee,
            )

            self.storage.save_ticket(completed_ticket)

            visit = Visit(
                ticket_id=completed_ticket.ticket_id,
                plate=completed_ticket.plate,
                vehicle_type=completed_ticket.vehicle_type,
                spot_ids=completed_ticket.spot_ids.copy(),
                entry_time=completed_ticket.entry_time,
                exit_time=completed_ticket.exit_time,
                duration_minutes=duration,
                fee=completed_ticket.fee,
            )

            self.storage.add_visit(visit)

            for spot_id in ticket.spot_ids:
                try:
                    spot = self.spots[spot_id]
                except KeyError as exc:
                    raise ValueError(
                        f"Spot not found: {spot_id}"
                    ) from exc

                spot.occupied = False
                spot.ticket_id = None

            return visit

    def status(self):
        """Return occupancy status for each vehicle type."""
        self._require_initialized()

        result = {
            vehicle_type.value: {
                "total": 0,
                "occupied": 0,
                "available": 0,
            }
            for vehicle_type in VehicleType
        }

        for spot in self.spots.values():
            vehicle_status = result[spot.vehicle_type.value]
            vehicle_status["total"] += 1

            if spot.occupied:
                vehicle_status["occupied"] += 1
            else:
                vehicle_status["available"] += 1

        return result

    def spot_status(self, spot_id):
        """Return the current status of a specific parking spot."""
        self._require_initialized()

        try:
            spot = self.spots[spot_id]
        except KeyError as exc:
            raise ValueError(
                f"Spot not found: {spot_id}"
            ) from exc

        return {
            "spot_id": spot.spot_id,
            "vehicle_type": spot.vehicle_type.value,
            "occupied": spot.occupied,
            "ticket_id": spot.ticket_id,
        }

    def get_history(self, plate):
        """Return completed visits for a specific vehicle plate."""
        self._require_initialized()

        return [
            visit
            for visit in self.storage.get_history()
            if visit.plate == plate
        ]

    def stress_test(
        self,
        concurrent=50,
        vehicle_type=VehicleType.CAR,
    ):
        """Test concurrent vehicle entry into the parking lot."""
        self._require_initialized()
        validate_vehicle_type(vehicle_type)

        results = []
        assigned_spots = []
        result_lock = threading.Lock()

        def worker(index):
            """Attempt to park one test vehicle."""
            try:
                ticket = self.park(
                    Vehicle(
                        plate=f"STRESS{index:03d}",
                        vehicle_type=vehicle_type,
                    )
                )

                with result_lock:
                    results.append(True)
                    assigned_spots.extend(ticket.spot_ids)

            except ValueError:
                with result_lock:
                    results.append(False)

        threads = [
            threading.Thread(
                target=worker,
                args=(index,),
            )
            for index in range(concurrent)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        successful = sum(results)
        rejected = concurrent - successful
        spot_conflicts = (
            len(assigned_spots) - len(set(assigned_spots))
        )

        return {
            "status": "ok",
            "successful": successful,
            "rejected": rejected,
            "spot_conflicts": spot_conflicts,
        }
