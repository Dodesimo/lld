from enum import Enum

class VehicleType(Enum):
    MOTORCYCLE  = 1
    CAR = 2
    LARGE = 3

class Ticket:
    def __init__(self, id, spot_id, vehicle_type, entry_time):
        self._id = id
        self._spot_id = spot_id
        self._vehicle_type = vehicle_type
        self._entry_time = entry_time 
        # just internal state of the ticket
    
    def get_id(self):
        return self._id
    
    def get_spot_id(self):
        return self_spot_id
    
    def get_vehicle_type(self):
        return self._vehicle_type
    
    def get_entry_time(self):
        return self._entry_time
    
    # getters setters for the ticket
