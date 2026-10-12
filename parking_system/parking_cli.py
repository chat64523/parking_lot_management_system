"""Command-line helpers for the parking lot management system."""

import argparse
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from parking_system.models import Vehicle, VehicleType


def json_default(value):
    """Convert unsupported values into JSON-serializable values."""
    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    raise TypeError(
        f"Object of type {type(value).__name__} "
        "is not JSON serializable"
    )


def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=json_default))


def parse_spots(value):
    """Parse a configuration such as motorcycle:5,car:20,bus:3."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Spot configuration cannot be empty")

    spot_config = {}

    for item in value.split(","):
        item = item.strip()

        if not item or ":" not in item:
            raise ValueError(
                "Use the format motorcycle:5,car:20,bus:3"
            )

        vehicle_name, count_text = item.split(":", 1)
        vehicle_name = vehicle_name.strip().lower()
        count_text = count_text.strip()

        try:
            vehicle_type = VehicleType(vehicle_name)
        except ValueError as exc:
            valid_types = ", ".join(
                vehicle.value for vehicle in VehicleType
            )
            raise ValueError(
                f"Invalid vehicle type '{vehicle_name}'. "
                f"Choose from: {valid_types}"
            ) from exc

        if vehicle_type in spot_config:
            raise ValueError(
                f"Duplicate vehicle type: {vehicle_name}"
            )

        try:
            spot_count = int(count_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid spot count for {vehicle_name}"
            ) from exc

        if spot_count < 0:
            raise ValueError("Spot counts cannot be negative")

        spot_config[vehicle_type] = spot_count

    if not any(spot_config.values()):
        raise ValueError(
            "At least one parking spot is required"
        )

    return spot_config


def build_parser():
    """Create the argument parser for parking commands."""
    parser = argparse.ArgumentParser(
        description="Parking Lot Management System"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize the parking lot",
    )
    init_parser.add_argument(
        "--spots",
        required=True,
        help="Example: motorcycle:5,car:20,bus:3",
    )
    init_parser.add_argument(
        "--pricing",
        choices=["hourly", "flat"],
        default="hourly",
        help="Pricing strategy",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Show parking status",
    )
    status_parser.add_argument(
        "--spot",
        dest="spot_id",
        help="Show the status of a specific spot",
    )

    enter_parser = subparsers.add_parser(
        "enter",
        help="Park a vehicle",
    )
    enter_parser.add_argument(
        "--plate",
        required=True,
        help="Vehicle registration plate",
    )
    enter_parser.add_argument(
        "--type",
        dest="vehicle_type",
        choices=[vehicle.value for vehicle in VehicleType],
        required=True,
        help="Type of vehicle",
    )

    exit_parser = subparsers.add_parser(
        "exit",
        help="Exit a vehicle using its ticket ID",
    )
    exit_parser.add_argument(
        "--ticket",
        dest="ticket_id",
        required=True,
        help="Parking ticket ID",
    )

    history_parser = subparsers.add_parser(
        "history",
        help="Show completed visits for a vehicle",
    )
    history_parser.add_argument(
        "--plate",
        required=True,
        help="Vehicle registration plate",
    )

    stress_parser = subparsers.add_parser(
        "stress-test",
        help="Test concurrent parking requests",
    )
    stress_parser.add_argument(
        "--concurrent",
        type=int,
        default=50,
        help="Number of concurrent requests",
    )
    stress_parser.add_argument(
        "--type",
        dest="vehicle_type",
        choices=[vehicle.value for vehicle in VehicleType],
        default=VehicleType.CAR.value,
        help="Vehicle type for the stress test",
    )

    subparsers.add_parser(
        "help",
        help="Show available commands",
    )
    subparsers.add_parser(
        "exit-repl",
        help="Exit the interactive application",
    )

    return parser


def _handle_init(lot, command_args):
    """Initialize the parking lot."""
    spot_config = parse_spots(command_args.spots)

    lot.initialize(
        spot_config,
        pricing_type=command_args.pricing,
    )

    print("Parking lot initialized successfully.")
    print_json(lot.status())


def _handle_status(lot, command_args):
    """Display parking lot or individual spot status."""
    if command_args.spot_id:
        print_json(lot.spot_status(command_args.spot_id))
        return

    print_json(lot.status())


def _handle_enter(lot, command_args):
    """Park a vehicle and display its ticket."""
    vehicle = Vehicle(
        plate=command_args.plate,
        vehicle_type=VehicleType(command_args.vehicle_type),
    )

    ticket = lot.park(vehicle)

    print("Vehicle parked successfully.")
    print_json(ticket)


def _handle_exit(lot, command_args):
    """Exit a vehicle and display its visit record."""
    visit = lot.exit_vehicle(command_args.ticket_id)

    print("Vehicle exited successfully.")
    print_json(visit)


def _handle_history(lot, command_args):
    """Display completed visits for a vehicle."""
    visits = lot.get_history(command_args.plate)
    print_json(visits)


def _handle_stress_test(lot, command_args):
    """Run concurrent parking requests."""
    if command_args.concurrent <= 0:
        raise ValueError(
            "Concurrent count must be a positive integer"
        )

    result = lot.stress_test(
        concurrent=command_args.concurrent,
        vehicle_type=VehicleType(command_args.vehicle_type),
    )

    print_json(result)


def run_command(lot, parser, command_args):
    """Execute a parsed parking command."""
    command = command_args.command

    if command == "help":
        parser.print_help()
        return

    if command == "exit-repl":
        return

    handlers = {
        "init": _handle_init,
        "status": _handle_status,
        "enter": _handle_enter,
        "exit": _handle_exit,
        "history": _handle_history,
        "stress-test": _handle_stress_test,
    }

    handler = handlers.get(command)

    if handler is None:
        raise ValueError(f"Unknown command: {command}")

    handler(lot, command_args)
