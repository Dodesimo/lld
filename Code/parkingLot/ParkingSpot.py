from enum import Enum

class SpotType(Enum):
    MOTORCYCLE = 1
    CAR = 2
    LARGE = 3

class ParkingSpot:
    def __init__(self, id, spot_type):
        self._id = id
        self._spot_type = spot_type
    
    def get_spot_type(self):
        return self._spot_type
    
    def get_id(self):
        return self._id
    
    # details about the parking spot