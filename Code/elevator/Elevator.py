from enum import Enum

class Direction(Enum):
    UP = 1
    DOWN = 2
    IDLE = 3

class Elevator:
    def __init__(self):
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.requsets = set()
    
    def add_request(self, request):
        if request.get_floor() < 0 or request.get_floor() > 9:
            return False # invalid
        if request.get_floor() == self.current_floor:
            return True # already at this
        if request in self.requests:
            return False # request already present
        self.requests.add(request)
        return True
    
    def step(self):
        if not self.requests:
            self.direction = Direction.idle
            return # no requests so direction stays the same
        if self.direction == Direction.IDLE:
            # find the nearest request to establish a direction
            nearest = None
            min_distance = float('inf')
            for req in self.requests:
                distance = abs(req.get_floor() - self.current_floor)
                if distance < min_distance or (distance == min_distance and (nearest is None or req.get_floor() < nearest.get_floor())):
                    # so if the calculated distance is less than the min distance or the distance is equal and we haven't found a nearest or the request one has a floor that's smaller 
                    min_distance = distance
                    nearest = req
            self.direction = Direction.UP if nearest.get_floor() > self.current_floor else Direction.DOWN
        
        pickup_type = RequestType.PICKUP_UP if self.direction == Direction.UP else RequestType.PICKUP_DOWN # type of request pickup_types we care about depending on the direction
        # we care about pick ups here as well as destinations in this floor
        pickup_request = Request(self.current_floor, pickup_type)
        destination_request = Request(self.current_floor, RequestType.DESTINATION)

        if pickup_request in self.requests or destination_request in self.requests:
            self.requests.discard(pickup_request)
            self.requests.discard(destination_request)
            if not self.requests:
                self.direction = Direction.IDLE
            return
        
        if not self.has_requests_ahead(self.direction):
            # if we don't have any requests in that direction, we will switch direction
            self.direction = Direction.DOWN if self.direction == Direction.UP else Direction.UP
            return
        
        if self.direction == Direction.UP:
            self.current_floor += 1
        elif self.direction == Direction.DOWN:
            self.current_floor -= 1
        
    def has_requests_ahead(self, direction):
        if request in self.requests:
            if direction == Direction.UP and request.get_floor() > self.current_floor:
                # there's something beyond in this floor in that direction
                return True
            if direction == Direction.DOWN and request.get_floor() < self.current_floor:
                #if we are going down, there something beyond my floor
                return True
        return False
    
    def has_requests_at_or_beyond(self, floor, direction):
        # see if there are any destinations here or after
        for request in self.requests:
            if direction == Direction.UP and request.get_floor() >= floor:
                if request.get_type() in (RequestType.PICKUP_UP, RequestType.DESTINATION):
                    # so if there are requests on floors that exceed the current, we return true
                    return True
            if direction == Direction.DOWN and request.get_floor() <= floor:
                if request.get_type() in (RequestType.PICKUP_DOWN, RequestType.DESTINATION):
                    return True
        return False
    
    def get_current_floor(self):
        return self.current_floor
    
    def get_direction(self):
        return self.direction