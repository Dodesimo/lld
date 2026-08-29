class ElevatorController:
    def __init__(self):
        self.elevators = [Elevator(), Elevator(), Elevator()]
    
    def request_elevator(self, floor, request_type):
        if floor < 0 or floor > 9:
            # invalid
            return False
        if request_type == RequestType.DESTINATION:
            # request type needs to be pick up if external to elevator
            return False
        
        request = Request(floor, request_type)
        best = self.select_best_elevator(request)
        if best is None:
            # no elevator available
            return False
        return best.add_request(request)
    
    def step(self):
        for elevator in self.elevators:
            elevator.step()
        
    def select_best_elevator(self, request):
        best = self.find_committed_to_floor(request)
        if best is not None:
            return best
        
        best = self.find_nearest_idle(request.get_floor())
        if best is not None:
            return best

        return self.find_nearest(request.get_floor())
    
    def find_committed_to_floor(self, request):
        floor = request.get_floor()
        direction = Direction.UP if request.get_type() == RequestType.PICKUP_UP else Direction.DOWN

        nearest = None
        min_distance = float('inf')
        for e in self.elevators:
            # direction needs to be the same as request
            if e.get_direction() != direction:
                continue
            
            # find a floor in the same direction that has sensible requests (elevator going down, request is down)
            if (direction == Direction.UP and e.get_current_floor() > floor) or (direction == Direction.DOWN and e.get_current_floor < floor):
                continue
            
            # if there aren't requests that are going to be in that direction the elevator its going to switch direction so fade
            if not e.has_requests_at_or_beyond(floor, direction):
                continue
                
            distance = abs(e.get_current_floor() - floor)
            if distance < min_distance:
                min_distance = distance
                nearest = e
        return nearest
    
    def find_nearest_idle(self, floor):
        nearest = None
        min_distance = float('inf')
        for e in self.elevators:
            if e.get_direction() != Direction.IDLE:
                continue # need idle
            distance = abs(e.get_current_floor() - floor)
            if distance < min_distance:
                nearest = e
                min_distance = distance
        return nearest
    
    def find_nearest(self, floor):
        nearest = self.elevators[0]
        min_distance = abs(self.elevators[0].get_current_floor() - floor)
        for e in self.elevators:
            distance = abs(e.get_current_floor() - floor) 
            if distance < min_distance:
                nearest = e
                min_distance = distance
        return nearest

