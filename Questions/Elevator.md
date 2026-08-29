- structure questions to cover four areas: error handling, boundaries of system, whether we have to handle future extensions
	- fixed number of elevators and floors, 3 elevators serving 10 floors from 0 to 9
	- up/down hall calls, system should pick elevator intelligently
	- elevators need to handle multiple destination requests, not just one at a time
	- two types of stops: 
		- hall calls with a direction (UP/DOWN)
		- destination requests without direction
	- reject invalid requests (return false), requesting the same floor as they are, no-op
	- this is a simulation with `step()` logic
- types of entities:
	- Floor: not really a entity b/c its just a number 
	- Request: could potentially just be a wrapper over primitives without actual behavior
	- Elevator: maintain state (floor, direction, what floors to stop at) and enforce rules (service stops along path can't go below floor 0)
	- ElevatorController: determine what elevator to dispatch, do orchestration (own system level view of elevators)
		- when building a simulation, have a controller that owns `step()` function
- class design:
	- ElevatorController:
		- state:
			- needs to track the elevators it controls (maintains an internal elevator list)
			- doesn't maintain queue of requests, keeps it stateless
		- behavior:
			- request an elevator from any floor: `requestElevator(floor, type)`
			- `step()` to advance all elevators one tick
	- Elevator:
		- state:
			- current floor position
			- current direction of travel
			- collection of floors to stop at
				- should this just be a set of floor numbers
					- when we add requests we add this to a set
					- and then when we step, if the requests contain the current floor we remove it
					- issue when passenger sees opposite direction elevator (should they ride and/or hope it comes back)
				- instead a class that just floor + request type
					- ```
					  class Request:
						  floor: int
						  type: RequestType
						  +request(floor, type)
					  ```
					* hash computed based on the floor and type
					* add request adds a request w/ floor and type
					* then we formulate two types of floor requests:
						* one for the direction and one for the direction
						* if either exists in the request stop at this floor by removing them from the requests
				* so Elevator is 
					* ```
					  class Elevator:
						- currentFloor: int
						- direction: Direction // can be either Up, Down, Idle
						- requests: Set<Request>
					  ```
					- behavior:
						- `addRequest(request)`: to add stop to queue
						- step(): to execute one tick of movement
						- `getCurrentFloor()`: return current position
						- `getDirection()`: get the current direction
				- all elevators get initialized at the ground floor
					- `addRequest`: used by the controller for hall calls as well as passengers inside the elevator
					- `.requestElevator(floor, type)` and `addRequest` are fundamentally different methods that do different things
- implementation:
	- elevator controller request
	- ```
	  requestElevator(floor, type):
		  if floor < 0 || floor > 9:
			  return False # invalid
		  if type == DESTINATION: 
			  return false # destination makes sense within elevator, but these are for hall calls
		  
		  request = Request(floor, type)
		  best = selectBestElevator(request)
		  return best.addRequest(request)
	  ```
		* what is the best elevator for the request?
			* nearest elevator based on floor
			* ```
			  floor = request.getFloor()
			  nearest = elevators[0]
			  minDistance = abs(elevators[0].getCurrentFloor() - floor)
			  for e in elevators:
				  distance = abs(e.getCurrentFloor() - floor)
				  if distance < minDistance:
					  minDistance = distance
					  nearest = e
				  return nearest				  
			  ```
			* bad because we don't account for direction
		* direction aware:
			* select best elevator based on what's moving towards you
			* then find whats nearest to you that's idle
			* and then any elevator
			* ```
			  findMovingToward(request):
				  floor = request.getFloor()
				  direction = UP if request.getType() == PICKUP_UP else DOWN
				  nearest = null
				  minDistance = Integer.MAX_VALUE
				  for e in elevators:
					  if e.getDirection() != direction:
						  continue # not in the same direction as we want to go
					  if (direction == UP && e.getCurrentFloor() > floor) || (direction == DOWN && e.getCurrentFloor() < floor) # if we are going up and the elevator goes beyond or if you are going down and the elevator goes beyond
					  continue 
					  
					  distance = abs(e.getCurrentFloor() - floor)
					  if distance < minDistance:
						  minDistance = distance
						  nearest = e
			  ```
				* issue w/ this: we don't check if the elevator's existing requests take it past the request floor
		* better approach:
			* see if there are any requests that go beyond the requested floor such that it can be reached
			* ```
			  for req in requests:
				  if dir == UP && request.getFloor() >= floor:
					  if request.getType() == PICKUP_UP || request.getType() == DESTINATION:
						  return True
				  if dir == DOWN && request.getFloor() <= floor:
					  if request.getType() == PICKUP_DOWN || request.getType() == destination:
						  return True
				return False
			  ```
	* elevator:
		* easiest solution: FIFO
			* look at the oldest request, move towards it
			* remove the request when we arrive to it
			* issue: this is inefficient and very random
		* better: use nearest-first movement
			* find the nearest request
			* for each request, calculate the distance between current floor and the request floor
			* if its less than the current or the request is the same distance but the floor is lesser, adjust
			* then move towards the floor
			* stop if we have arrived there
			* issue: still changing directions
		* best: 
			* SCAN algorithm
			* if requests is empty, direction is idle
			* if the direction is Idle, pick direct towards the nearest request
			* if we should stop at a floor, remove current requests 
				* if requests is empty, direction is Idle
				* return
			* if there are no requests ahead we reverse direction
			* move one floor
			* better:
				* even though there is one more floor, we have minimized direction changes and passenger wait times
			* cases:
				* if requests is empty, IDLE and return
				* pick direction if Idle: pick direction before checking for stops, find nearest request to establish direction breaking ties w/ lower floor number
				* check for stops: removing a request check for more requests, if there are we don't move on, else we return
				* no requests ahead: if there aren't requests ahead in the same direction as movement, flip direction and return
				* else move one floor in the current direction
				* ```
				  hasRequestsAhead(dir):
					  for request in requests:
						  if dir == UP && request.getFloor() > currentFloor:
							  return True
						  if dir == DOWN && request.getFloor() < currentFloor:
							  return true
					  return false 
				  ```
					 *  go towards any request regardless of type
					 * this is b/c elevator travels towards all requests but only stops for matching ones
					 * this means that someone on Floor 6 waits if the elevator has to go to 8 and then reverses and then returns to Floor 6
					* don't explicitly check for 0 and 9 because above function takes care of these edge cases
			* ```
			  addRequest(request)
			  if request.getFloor < 0 || request.getFloor() > 9:
				  return false
			  if request.getFloor() == currentFloor
				  return true
			  return requests.add(request)
			  ```
			* we validate floor number and then deduplicate requests based on the hash
	* extensibility:
		* can add a priority field to the request class and use a priority queue but this breaks sweep-in-one-direction
		* keep standard movement logic for normal elevator and add a seperate express flag
		* dispatch logic: if request is for priority floor, send express elevator
			* has a restricted `addRequest` that only accepts 0, 5, 9 but that particular elevator only validates/accepts particular floors
			* `addRequest`for express elevator: if the request contains non-express floor, reject
			* for selection in the controller, if the express elevator is idle, return that if the floor requested is priority
		* undo:
			* just delete the request from the set through removeRequest
		* multiple hall calls come in:
			* two calls hit request elevator and they both select the best elevator
			* both see elevator as idle and dispatch (selection + add needs to be atomic)
			* add a lock around requestElevator() and step() -> prevents concurrent access to the set , but both block each other
			* or concurrent queue, add request will write to a thread safe queue instead of a set
				* start of each tick, `step()` drains queue into working set
				* step only touches set