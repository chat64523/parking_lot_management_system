"""In-memory storage for the parking lot management system."""

from models import Spot, Ticket, Visit

class Storage:
    """Store parking spots, tickets, and visit history in memory."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.spots: dict[str, Spot] = {}
        self.tickets: dict[str, Ticket] = {}
        self.history: list[Visit] = []

    def save_spot(self, spot: Spot) -> None:
        """Save or update a parking spot."""
        self.spots[spot.spot_id] = spot

    def save_ticket(self, ticket: Ticket) -> None:
        """Save or update a parking ticket."""
        self.tickets[ticket.ticket_id] = ticket

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Return a ticket by its ID."""
        return self.tickets.get(ticket_id)

    def add_visit(self, visit: Visit) -> None:
        """Add a completed visit to the history."""
        self.history.append(visit)

    def get_history(self) -> list[Visit]:
        """Return all completed parking visits."""
        return self.history
        