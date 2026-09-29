# Parking Lot Management System

A simple command-line Parking Lot Management System built in Python.
The system supports multiple vehicle types, parking spot allocation, vehicle entry and exit, parking history, different pricing strategies, and concurrent parking requests.

## Requirements

* Python 3.14.2
* pytest 9.1.1

## Python Standard Libraries

The project uses the following built-in Python libraries:

* **argparse** – Used to handle command-line arguments and commands.
* **json** – Used for storing and loading parking data in JSON format.
* **threading** – Used to handle concurrent parking requests.
* **datetime** – Used to record entry and exit times and calculate parking duration.
* **shlex** – Used to parse command-line input correctly.

## Installation

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

#### Windows

```bash
.venv\Scripts\activate
```

#### Linux/macOS

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses `pytest` for testing.

## Running the CLI

Start the application with:

```bash
python parking_cli.py
```

The application opens an interactive command-line interface:

```text
Parking Lot Management System
Type 'help' for commands or 'exit-repl' to quit.
parking>
```

Commands are entered after the `parking>` prompt.

## CLI Commands

The CLI provides the following commands:

```text
init
status
status-spot
enter
exit
history
stress-test
help
exit-repl
```

---

## 1. Initialize the Parking Lot

### Syntax

```text
init --spot "motorcycle:5,car:20,bus:3" --pricing hourly
```

### Example

```text
parking> init --spot "motorcycle:5,car:6,bus:4" --pricing hourly
```

Example output:

```json
{
  "status": "ok",
  "message": "Parking lot initialized",
  "pricing": "hourly",
  "total_spots": 15
}
```

This creates:

* 5 motorcycle spots
* 6 car spots
* 4 bus spots

Available pricing options are:

```text
hourly
flat
```

---

## 2. Check Overall Parking Status

### Syntax

```text
status
```

### Example

```text
parking> status
```

Example output:

```json
{
  "status": "ok",
  "pricing": "hourly",
  "motorcycle": {
    "total": 5,
    "occupied": 0,
    "available": 5
  },
  "car": {
    "total": 6,
    "occupied": 0,
    "available": 6
  },
  "bus": {
    "total": 4,
    "occupied": 0,
    "available": 4
  }
}
```

The status command shows the total, occupied, and available spots for each vehicle type.

---

## 3. Check a Specific Parking Spot

The command is **`status-spot`**, not `status --spot`.

### Syntax

```text
status-spot SPOT_ID
```

### Example

```text
parking> status-spot C-14
```

This displays the status of the selected parking spot.

Example output:

```json
{
  "status": "ok",
  "spot_id": "C-14",
  "vehicle_type": "car",
  "occupied": false,
  "ticket_id": null
}
```

---

## 4. Enter a Vehicle

### Syntax

```text
enter --plate PLATE_NUMBER --type VEHICLE_TYPE
```

### Car Example

```text
parking> enter --plate ABC123 --type car
```

### Motorcycle Example

```text
parking> enter --plate MOTO123 --type motorcycle
```

### Bus Example

```text
parking> enter --plate BUS123 --type bus
```

When a vehicle successfully enters, the system creates a ticket and assigns the required parking spot or spots.

---

## 5. Exit a Vehicle

### Syntax

```text
exit --ticket TICKET_ID
```

### Example

```text
parking> exit --ticket T001
```

When a vehicle exits, the system:

1. Finds the ticket.
2. Calculates the parking duration.
3. Calculates the parking fee.
4. Frees the assigned parking spots.
5. Adds the completed visit to parking history.

---

## 6. View Parking History

### Syntax

```text
history --plate PLATE_NUMBER
```

### Example

```text
parking> history --plate ABC123
```

This returns completed visits for the specified vehicle during the current session.

The history includes information such as:

* Entry time
* Exit time
* Parking duration
* Assigned spots
* Parking fee

---

## 7. Run the Concurrency Stress Test

### Syntax

```text
stress-test --concurrent NUMBER --type VEHICLE_TYPE
```

### Example

```text
parking> stress-test --concurrent 50 --type car
```

The stress test creates multiple concurrent vehicle-entry requests.

The result includes:

* Number of successful entries
* Number of rejected entries
* Number of spot conflicts

Example output:

```json
{
  "status": "ok",
  "successful": 20,
  "rejected": 30,
  "spot_conflicts": 0
}
```

`spot_conflicts: 0` means that no two successful requests were assigned the same parking spot.

---

## Vehicle Types

The system supports three vehicle types:

| Vehicle Type | Spots Required | Prefix |
| ------------ | -------------: | ------ |
| motorcycle   |              1 | M      |
| car          |              1 | C      |
| bus          |  2 (consecutive) | B      |

A bus requires **two consecutive available bus spots**.

For example:

```text
B-01 = available
B-02 = occupied
B-03 = available
```

There are two free bus spots in this example, but the bus cannot enter because the available spots are not consecutive.

---

## Pricing Strategies

The system supports two pricing strategies: **hourly pricing** and **flat pricing**.

### Hourly Pricing

For hourly pricing, the system calculates the parking fee based on the parking duration.

The hourly rates are:

| Vehicle Type | Hourly Rate |
| ------------ | ----------: |
| Motorcycle   |          50 |
| Car          |         100 |
| Bus          |         200 |

The duration is rounded up to the next whole hour, with a minimum charge of one hour.

For example, if a car stays for 90 minutes, it is charged for 2 hours.

### Flat Pricing

For flat pricing, a fixed fee is charged based on the vehicle type, regardless of the parking duration.

| Vehicle Type | Flat Rate |
| ------------ | --------: |
| Motorcycle   |       100 |
| Car          |       200 |
| Bus          |       400 |

### Pricing Design

The project uses the **Strategy Design Pattern** for pricing.

The `PricingStrategy` abstract class defines the `calculate_fee()` method, while `HourlyPricing` and `FlatPricing` provide their own implementations.

The `create_pricing()` factory function selects the appropriate pricing strategy based on the selected pricing type:

```text
hourly → HourlyPricing
flat   → FlatPricing
```

This keeps pricing logic separate from the main `ParkingLot` class and makes the system easier to extend with additional pricing strategies in the future.


---

## Concurrency Handling

Parking spot assignment is protected using Python's `threading.Lock`.

The critical section checks for available spots and assigns them while holding the lock. This prevents multiple threads from checking and assigning the same parking spot at the same time.

The selected spots are marked as occupied before the lock is released.

The concurrency stress test verifies the behavior by checking for duplicate assigned spot IDs.

A result of:

```text
spot_conflicts: 0
```

means that no two successful concurrent requests were assigned the same parking spot.

---

## Data Storage

The current implementation uses an in-memory `Storage` class.

It stores:

* Parking spots
* Tickets
* Parking history

The storage logic is separated from the parking logic making it easier to replace the in-memory implementation with a database or another persistent storage solution in the future.

---

## Error Handling

The application handles different invalid operations and returns clear error messages.

Examples include:

* Parking lot is not initialized
* Invalid vehicle type
* Invalid spot configuration
* No available parking spot
* No consecutive spots available for a bus
* Invalid ticket
* Already-closed ticket
* Spot not found

The CLI converts these errors into error responses instead of allowing the application to terminate unexpectedly.

---

## Project Structure

```text
parking_lot_management_system/
│
├── parking_cli.py
├── parking_lot.py
├── models.py
├── vehicles.py
├── pricing.py
├── storage.py
│
├── tests/
│   └── test_parking.py
|   └── test_concurrency.py
│
├── README.md
└── requirements.txt
```

---

## Running Tests

Run the complete test suite with:

```bash
 PYTHONPATH=. pytest -q
```

The tests cover:

* Entry into an empty lot
* Entry into a full lot
* Bus entry when two consecutive spots are unavailable
* Hourly pricing
* Flat pricing
* Multiple entry and exit cycles
* Parking history
* Concurrent vehicle entries
* Spot conflict detection

Example:

```text
7 passed
```

---

## Design Overview

The application separates responsibilities into different components:

```text
parking_cli.py
       │
       ▼
  ParkingLot
       │
       ├── vehicles.py
       ├── pricing.py
       ├── storage.py
       └── models.py
```

### Components

**`parking_cli.py`**

Handles the interactive command-line interface and user commands.

**`parking_lot.py`**

Contains the main parking lot operations such as vehicle entry, exit, spot allocation and history.

**`vehicles.py`**

Contains vehicle types, vehicle validation, required spot counts, and spot prefixes.

**`pricing.py`**

Contains pricing strategies and the pricing factory.

**`storage.py`**

Manages in-memory parking spots, tickets, and visit history.

**`models.py`**

Contains the main data models such as vehicles, parking spots, tickets, and visits.

---

## Technologies

* Python 3.14.2
* Pytest 9.1.1
* Python Standard Library
* Object-Oriented Programming
* Strategy Design Pattern
* Threading and Locks
* Command-Line Interface

---

## License

This project was developed as a coding assignment for educational and demonstration purposes.