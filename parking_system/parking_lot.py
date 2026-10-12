"""Core parking lot management logic."""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from parking_system.models import (
    Spot,
    Ticket,
    Vehicle,
    Visit,
    VehicleType,
)
from parking_system.pricing import create_pricing
from parking_system.storage import Storage
from parking_system.utils import validate_vehicle_type
from parking_system.vehicles import (
    get_spots_required,
    get_vehicle_prefix,
)


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

    def _validate_spot_config(self, spot_config):
        """Validate the parking spot configuration."""
        try:
            if not isinstance(spot_config, dict) or not spot_config:
                raise ValueError(
                    "At least one vehicle type is required"
                )
            for vehicle_type, spot_count in spot_config.items():
                validate_vehicle_type(vehicle_type, VehicleType)
                if (not isinstance(spot_count, int)
                    or isinstance(spot_count, bool)
                    or spot_count < 0
                    ):
                    raise ValueError(
                        "Spot count must be a non-negative integer"
                    )
            if not any(count > 0 for count in spot_config.values()):
                raise ValueError(
                    "At least one parking spot is required"
                )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid spot configuration: {exc}"
            ) from exc

    def _require_initialized(self):
        """Ensure the parking lot has been initialized."""
        if not self.initialized:
            raise ValueError("Parking lot is not initialized")

    def _get_spot_number(self, spot_id):
        """Extract the numeric part of a parking spot ID."""
        try:
            prefix, number = spot_id.split("-", 1)
            if not prefix or not number:
                raise ValueError("Incomplete spot ID")
            return int(number)

        except (AttributeError, ValueError) as exc:
            raise ValueError(
                f"Invalid spot ID format: {spot_id}"
            ) from exc

    @staticmethod
    def _create_vehicle_spots(vehicle_type, spot_count):
        """Create spots for one vehicle type."""
        prefix = get_vehicle_prefix(vehicle_type)
        return {
            f"{prefix}-{number:02d}": Spot(
                spot_id=f"{prefix}-{number:02d}",
                vehicle_type=vehicle_type,
            )
            for number in range(1, spot_count + 1)
        }

    def _create_spots(self, spot_config):
        """Create all parking spots from the configuration."""
        new_spots = {}
        for vehicle_type, spot_count in spot_config.items():
            vehicle_spots = self._create_vehicle_spots(
                vehicle_type,
                spot_count,
            )
            new_spots.update(vehicle_spots)
        return new_spots

    def initialize(self, spot_config: dict, pricing_type=None):
        """Initialize parking spots and select a pricing strategy."""
        self._validate_spot_config(spot_config)
        selected_pricing_type = (
            pricing_type
            if pricing_type is not None
            else self.pricing_type
        )
        if selected_pricing_type is None:
            selected_pricing_type = "hourly"

        new_pricing = create_pricing(selected_pricing_type)
        new_spots = self._create_spots(spot_config)

        with self.lock:
            active_tickets = [
                ticket
                for ticket in self.tickets.values()
                if ticket.active
            ]

            if active_tickets:
                raise ValueError(
                    "Cannot reinitialize while active tickets exist"
                )

            self.storage.spots.clear()
            self.storage.spots.update(new_spots)
            self.storage.tickets.clear()
            self.storage.history.clear()
            self.ticket_counter = 0
            self.pricing_type = selected_pricing_type
            self.pricing = new_pricing
            self.initialized = True

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
            key=lambda spot: self._get_spot_number(
                spot.spot_id
            ),
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
        if not isinstance(vehicle, Vehicle):
            raise ValueError(
                "A valid Vehicle object is required"
            )
        validate_vehicle_type(vehicle.vehicle_type, VehicleType)
        self._require_initialized()

        with self.lock:
            selected_spots = self._find_available_spots(
                vehicle.vehicle_type
            )

            next_ticket_number = self.ticket_counter + 1
            ticket_id = f"T{next_ticket_number:03d}"
            ticket = Ticket(
                ticket_id=ticket_id,
                plate=vehicle.plate,
                vehicle_type=vehicle.vehicle_type,
                spot_ids=[
                    spot.spot_id for spot in selected_spots
                ],
                entry_time=datetime.now(),
            )

            try:
                self.storage.save_ticket(ticket)
                for spot in selected_spots:
                    spot.occupied = True
                    spot.ticket_id = ticket_id

            except Exception as exc:
                for spot in selected_spots:
                    if spot.ticket_id == ticket_id:
                        spot.occupied = False
                        spot.ticket_id = None

                self.storage.tickets.pop(ticket_id, None)

                raise RuntimeError(
                    "Failed to park vehicle"
                ) from exc

            self.ticket_counter = next_ticket_number
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

            try:
                spots_to_free = [
                    self.spots[spot_id]
                    for spot_id in ticket.spot_ids
                ]
            except KeyError as exc:
                raise ValueError(
                    f"Spot not found: {exc.args[0]}"
                ) from exc

            for spot in spots_to_free:
                if not spot.occupied or spot.ticket_id != ticket_id:
                    raise ValueError(
                        f"Spot state is inconsistent: {spot.spot_id}"
                    )

            exit_time = datetime.now()
            duration = max(0, int((exit_time - ticket.entry_time).total_seconds() // 60),)
            fee = self.pricing.calculate(
                ticket.vehicle_type,
                duration,
            )

            completed_ticket = replace(
                ticket,
                exit_time=exit_time,
                fee=fee,
            )

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

            self.storage.save_ticket(completed_ticket)

            try:
                self.storage.add_visit(visit)
            except Exception as exc:
                self.storage.save_ticket(ticket)
                raise RuntimeError(
                    "Failed to save visit history"
                ) from exc

            for spot in spots_to_free:
                spot.occupied = False
                spot.ticket_id = None

            return visit

    def status(self):
        """Return occupancy status for each vehicle type."""
        self._require_initialized()

        with self.lock:
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
        """Return the status of a specific parking spot."""
        self._require_initialized()

        with self.lock:
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

        with self.lock:
            return [
                visit
                for visit in self.storage.get_history()
                if visit.plate == plate
            ]

    def stress_test(self, concurrent=50, vehicle_type=VehicleType.CAR):
        """Test concurrent vehicle entry into the parking lot."""
        self._require_initialized()

        if (not isinstance(concurrent, int) or isinstance(concurrent, bool) or concurrent <= 0):
            raise ValueError(
                "Concurrent count must be a positive integer"
            )
        validate_vehicle_type(vehicle_type, VehicleType)

        def worker(index):
            """Attempt to park one test vehicle."""
            vehicle = Vehicle(
                plate=f"STRESS{index:03d}",
                vehicle_type=vehicle_type,
            )

            try:
                ticket = self.park(vehicle)
            except ValueError as exc:
                if str(exc).startswith("No available"):
                    return False, []

                raise

            return True, ticket.spot_ids

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            results = list(
                executor.map(worker, range(concurrent))
            )

        successful = sum(1 for parked, _ in results if parked)
        rejected = concurrent - successful

        assigned_spots = [
            spot_id
            for _, spot_ids in results
            for spot_id in spot_ids
        ]

        spot_conflicts = (len(assigned_spots) - len(set(assigned_spots)))

        return {
            "status": "ok",
            "successful": successful,
            "rejected": rejected,
            "spot_conflicts": spot_conflicts,
        }
