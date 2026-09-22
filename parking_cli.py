"""Command-line interface for the parking lot management system."""

import argparse
import json
import shlex
import sys

from models import Vehicle
from parking_lot import ParkingLot
from vehicles import VEHICLE_TYPES


def parse_spots(value):
    """Parse parking spot configuration from a command-line value."""
    result = {}

    try:
        for item in value.split(","):
            if ":" not in item:
                raise ValueError

            vehicle_type, count = item.split(":", 1)
            vehicle_type = vehicle_type.strip().lower()
            count = int(count.strip())

            if vehicle_type not in VEHICLE_TYPES:
                raise ValueError(
                    f"Invalid vehicle type: {vehicle_type}"
                )

            if count <= 0:
                raise ValueError(
                    "Spot count must be greater than 0"
                )

            result[vehicle_type] = count

    except ValueError as exc:
        if str(exc).startswith("Invalid vehicle type"):
            raise

        raise ValueError(
            "Invalid spots format. "
            "Example: motorcycle:5,car:20,bus:3"
        ) from exc

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

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--spots", required=True)
    init_parser.add_argument(
        "--pricing",
        required=True,
        choices=["hourly", "flat"],
    )

    subparsers.add_parser("status")

    status_spot_parser = subparsers.add_parser("status-spot")
    status_spot_parser.add_argument("--spot", required=True)

    enter_parser = subparsers.add_parser("enter")
    enter_parser.add_argument(
        "--type",
        required=True,
        choices=sorted(VEHICLE_TYPES),
    )
    enter_parser.add_argument("--plate", required=True)

    exit_parser = subparsers.add_parser("exit")
    exit_parser.add_argument("--ticket", required=True)

    history_parser = subparsers.add_parser("history")
    history_parser.add_argument("--plate", required=True)

    stress_parser = subparsers.add_parser("stress-test")
    stress_parser.add_argument(
        "--concurrent",
        type=int,
        default=50,
    )
    stress_parser.add_argument(
        "--type",
        default="car",
        choices=sorted(VEHICLE_TYPES),
    )

    return parser

# pylint: disable=too-many-return-statements
def run_command(parking_lot, args):
    """Execute a parsed command against the parking lot."""
    try:
        if args.command == "init":
            spots = parse_spots(args.spots)
            parking_lot.initialize(spots, args.pricing)

            return success(
                message="Parking lot initialized",
                pricing=args.pricing,
                total_spots=len(parking_lot.spots),
            )

        if args.command == "status":
            return success(
                pricing=parking_lot.pricing_type,
                **parking_lot.status(),
            )

        if args.command == "status-spot":
            return success(
                **parking_lot.spot_status(args.spot)
            )

        if args.command == "enter":
            vehicle = Vehicle(
                plate=args.plate,
                vehicle_type=args.type,
            )

            ticket = parking_lot.park(vehicle)

            return success(
                ticket_id=ticket.ticket_id,
                plate=ticket.plate,
                vehicle_type=ticket.vehicle_type,
                spot=ticket.spot_ids,
                entry_time=ticket.entry_time.isoformat(),
            )

        if args.command == "exit":
            visit = parking_lot.exit_vehicle(args.ticket)

            return success(
                duration_minutes=visit.duration_minutes,
                fee=visit.fee,
                spot_freed=visit.spot_ids,
            )

        if args.command == "history":
            visits = parking_lot.get_history(args.plate)

            return success(
                plate=args.plate,
                visits=[
                    {
                        "ticket_id": visit.ticket_id,
                        "vehicle_type": visit.vehicle_type,
                        "spot_ids": visit.spot_ids,
                        "entry_time": visit.entry_time.isoformat(),
                        "exit_time": visit.exit_time.isoformat(),
                        "duration_minutes": visit.duration_minutes,
                        "fee": visit.fee,
                    }
                    for visit in visits
                ],
            )

        if args.command == "stress-test":
            if args.concurrent <= 0:
                raise ValueError(
                    "Concurrent count must be greater than 0"
                )

            return parking_lot.stress_test(
                args.concurrent,
                args.type,
            )

        raise ValueError("Please provide a valid command")

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
