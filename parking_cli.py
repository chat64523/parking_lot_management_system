"""Command-line interface for the parking lot management system."""

import argparse
import json
import shlex
import sys

from models import Vehicle, VehicleType
from parking_lot import ParkingLot

COMMAND_INIT = "init"
COMMAND_STATUS = "status"
COMMAND_STATUS_SPOT = "status-spot"
COMMAND_ENTER = "enter"
COMMAND_EXIT = "exit"
COMMAND_HISTORY = "history"
COMMAND_STRESS_TEST = "stress-test"
VEHICLE_TYPE_CHOICES = [vehicle_type.value for vehicle_type in VehicleType]

def parse_spots(value):
    """Parse parking spot configuration from a command-line value."""
    result = {}

    for item in value.split(","):
        if ":" not in item:
            raise ValueError(
                "Invalid spots format. "
                "Example: motorcycle:5,car:20,bus:3"
            )
        vehicle_type_text, spot_count_text = item.split(":", 1)
        vehicle_type_text = vehicle_type_text.strip().lower()
        spot_count_text = spot_count_text.strip()

        try:
            vehicle_type = VehicleType(vehicle_type_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid vehicle type: {vehicle_type_text}"
            ) from exc

        try:
            spot_count = int(spot_count_text)
        except ValueError as exc:
            raise ValueError(
                "Invalid spots format. "
                "Example: motorcycle:5,car:20,bus:3"
            ) from exc

        if spot_count <= 0:
            raise ValueError("Spot count must be greater than 0")

        result[vehicle_type] = spot_count
    return result

def success(**data):
    """Create a successful command response."""
    return {"status": "ok", **data}

def error(message):
    """Create an error command response."""
    return {"status": "error", "message": message}

def create_parser():
    """Create and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Parking Lot Management System"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    init_parser = subparsers.add_parser(
        COMMAND_INIT,
        help="Initialize the parking lot.",
    )
    init_parser.add_argument(
        "--spots",
        required=True,
        help="Parking spot configuration, e.g. motorcycle:5,car:20,bus:3.",
    )
    init_parser.add_argument(
        "--pricing",
        required=True,
        choices=["hourly", "flat"],
        help="Pricing strategy to use.",
    )

    subparsers.add_parser(
        COMMAND_STATUS,
        help="Show the current parking lot status.",
    )

    status_spot_parser = subparsers.add_parser(
        COMMAND_STATUS_SPOT,
        help="Show the status of a specific parking spot.",
    )
    status_spot_parser.add_argument(
        "--spot",
        required=True,
        help="Parking spot ID.",
    )

    enter_parser = subparsers.add_parser(
        COMMAND_ENTER,
        help="Park a vehicle and create a ticket.",
    )
    enter_parser.add_argument(
        "--type",
        required=True,
        choices=VEHICLE_TYPE_CHOICES,
        help="Vehicle type.",
    )
    enter_parser.add_argument(
        "--plate",
        required=True,
        help="Vehicle plate number.",
    )

    exit_parser = subparsers.add_parser(
        COMMAND_EXIT,
        help="Exit a vehicle and complete its ticket.",
    )
    exit_parser.add_argument(
        "--ticket",
        required=True,
        help="Ticket ID.",
    )

    history_parser = subparsers.add_parser(
        COMMAND_HISTORY,
        help="Show completed visits for a vehicle.",
    )
    history_parser.add_argument(
        "--plate",
        required=True,
        help="Vehicle plate number.",
    )

    stress_parser = subparsers.add_parser(
        COMMAND_STRESS_TEST,
        help="Run a concurrent parking stress test.",
    )
    stress_parser.add_argument(
        "--concurrent",
        type=int,
        default=50,
        help="Number of concurrent parking attempts.",
    )
    stress_parser.add_argument(
        "--type",
        default=VehicleType.CAR.value,
        choices=VEHICLE_TYPE_CHOICES,
        help="Vehicle type for the stress test.",
    )

    return parser

def handle_init(parking_lot, args):
    """Handle the init command."""
    spots = parse_spots(args.spots)
    parking_lot.initialize(spots, args.pricing)

    return success(
        message="Parking lot initialized",
        pricing=args.pricing,
        total_spots=len(parking_lot.spots),
    )

def handle_status(parking_lot, _args):
    """Handle the status command."""
    return success(
        pricing=parking_lot.pricing_type,
        **parking_lot.status(),
    )

def handle_status_spot(parking_lot, args):
    """Handle the status-spot command."""
    return success(
        **parking_lot.spot_status(args.spot)
    )

def handle_enter(parking_lot, args):
    """Handle the enter command."""
    vehicle_type = VehicleType(args.type)

    vehicle = Vehicle(
        plate=args.plate,
        vehicle_type=vehicle_type,
    )
    ticket = parking_lot.park(vehicle)

    return success(
        ticket_id=ticket.ticket_id,
        plate=ticket.plate,
        vehicle_type=ticket.vehicle_type.value,
        spot=ticket.spot_ids,
        entry_time=ticket.entry_time.isoformat(),
    )

def handle_exit(parking_lot, args):
    """Handle the exit command."""
    visit = parking_lot.exit_vehicle(args.ticket)

    return success(
        duration_minutes=visit.duration_minutes,
        fee=visit.fee,
        spot_freed=visit.spot_ids,
    )

def handle_history(parking_lot, args):
    """Handle the history command."""
    visits = parking_lot.get_history(args.plate)

    return success(
        plate=args.plate,
        visits=[
            {
                "ticket_id": visit.ticket_id,
                "vehicle_type": visit.vehicle_type.value,
                "spot_ids": visit.spot_ids,
                "entry_time": visit.entry_time.isoformat(),
                "exit_time": visit.exit_time.isoformat(),
                "duration_minutes": visit.duration_minutes,
                "fee": visit.fee,
            }
            for visit in visits
        ],
    )

def handle_stress_test(parking_lot, args):
    """Handle the stress-test command."""
    if args.concurrent <= 0:
        raise ValueError(
            "Concurrent count must be greater than 0"
        )
    vehicle_type = VehicleType(args.type)

    return parking_lot.stress_test(
        args.concurrent,
        vehicle_type,
    )

COMMAND_HANDLERS = {
    COMMAND_INIT: handle_init,
    COMMAND_STATUS: handle_status,
    COMMAND_STATUS_SPOT: handle_status_spot,
    COMMAND_ENTER: handle_enter,
    COMMAND_EXIT: handle_exit,
    COMMAND_HISTORY: handle_history,
    COMMAND_STRESS_TEST: handle_stress_test,
}

def run_command(parking_lot, args):
    """Execute a parsed command against the parking lot."""
    handler = COMMAND_HANDLERS.get(args.command)
    if handler is None:
        return error("Please provide a valid command")

    try:
        return handler(parking_lot, args)
    except ValueError as exc:
        return error(str(exc))

def execute_line(parking_lot, command_line):
    """Execute one command entered in the interactive shell."""
    args = create_parser().parse_args(
        shlex.split(command_line)
    )
    return run_command(parking_lot, args)

def repl():
    """Run the interactive command-line interface."""
    parking_lot = ParkingLot()
    print("Parking Lot Management System")
    print("Type 'help' for commands or 'exit-repl' to quit.")

    while True:
        try:
            line = input("parking> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line.lower() == "exit-repl":
            break

        if line.lower() == "help":
            create_parser().print_help()
            continue

        try:
            result = execute_line(parking_lot, line)
        except SystemExit:
            result = error("Invalid command")

        print(json.dumps(result))

def main():
    """Run the command-line application."""
    parser = create_parser()

    if len(sys.argv) == 1:
        repl()
        return

    args = parser.parse_args()
    result = run_command(ParkingLot(), args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
