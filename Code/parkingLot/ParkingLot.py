import uuid
import time

class ParkingLot:
    # master orchestrator
    def __init__(self, spots, hourly_rate_cents):
        self._spots = spots # list
        self._active_tickets = {} # map of ticket id to ticket
        self._occupied_spot_ids = set() # id of spots not the actual spots to avoid accidental operations
        self._hourly_rate_cents = hourly_rate_cents # the charge per hour flat
    
    def enter(self, vehicle_type):
        # we get a spot, add it to the occupied, create a ticket, add it to the map
        spot = self._find_available_spot() 
        if not spot:
            raise Exception("spot not found")
        self._occupied_spot_ids.add(spot.id)
        ticketId = str(uuid.uuid4())
        ticket = Ticket(ticketId, spotId, vehicle_type, time.time())
        self._active_tickets[ticketId] = ticket
        return ticket

    def exit(self, ticketId):
        if len(ticketId) == 0:
            raise Exception("invalid ticket id")
        
        ticket = self._active_tickets[ticketId] # find the ticket
        fee = self._compute_fee(ticket.get_entry_time(), time.time()) # compute fee
        self._occupied_spot_ids.discard(ticket.get_spot_id()) # get rid of spot id
        del self._active_tickets[ticketId] # get rid of ticket
        return fee
    
    def _find_available_spot(self, vehicle_type):
        required_spot = self._map_vehicle_type_to_spot_type(vehicle_type)
        for spot in spots:
            if spot.get_spot_type() == required_spot and spot.get_id() not in self._occupied_spot_ids:
                return spot
        return None
    
    def _map_vehicle_type_to_spot_type(self, vehicle_type):
        if vehicle_type == VehicleType.MOTORCYCLE:
            return SpotType.MOTORCYCLE
        elif vehicle_type == VehicleType.CAR:
            return SpotType.CAR
        else:
            return SpotType.LARGE
        
    def _compute_fee(self, entry_time, exit_time):
        entry_time = int(entry_time) * 1000
        exit_time = int(exit_time) * 1000
        hours = (exit_time - entry_time) // (1000 * 60 * 60)
        if ((exit_time - entry_time) / (1000 * 60)) % 60 > 0: # we have minutes running over
            hours += 1
        return hours * hourly_rate_cents