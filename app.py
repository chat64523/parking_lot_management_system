"""Application startup and command-line interface."""

import shlex
from parking_system.cli.parking_cli import build_parser, run_command
from parking_system.core.parking_lot import ParkingLot


def run_app():
    """Start the interactive parking lot application."""
    lot = ParkingLot()
    parser = build_parser()
    print("Parking Lot Management System")
    print("Type 'help' to see available commands.")
    print("Type 'exit-repl' to quit.")
    while True:
        try:
            command_line = input("parking> ").strip()

            if not command_line:
                continue

            command_args = parser.parse_args(shlex.split(command_line))
            run_command(lot, parser, command_args)

        except SystemExit as exc:
            if exc.code != 0:
                print("Invalid command. Type 'help' for usage.")

        except (ValueError, TypeError) as exc:
            print(f"Error: {exc}")

        except KeyboardInterrupt:
            print("\nOperation interrupted.")

        except EOFError:
            print("\nExiting parking system.")
            return

        if command_line == "exit-repl":
            print("Exiting parking system.")
            return


if __name__ == "__main__":
    run_app()
