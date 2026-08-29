from enum import Enum

class RequestType(Enum):
    PICKUP_UP = 1
    PICKUP_DOWN = 2
    DESTINATION = 3

class Request:
    def __init__(self, floor, request_type):
        self.floor = floor
        self.type = request_type
    
    def get_floor(self):
        return self.floor

    def get_type(self):
        return self.type
    
    def __eq__(self, other):
        if not isinstance(other, Request):
            return False
        return self.floor == other.floor and self.type == other.type
    
    def __hash__(self):
        return hash((self.floor, self.type))
