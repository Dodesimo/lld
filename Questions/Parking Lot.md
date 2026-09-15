- requirements:
	- system supports Motorcycle, Car, Large Vehicle
	- Vehicle enters, system gives available compatible spot
	- System issues ticket at entry
	- Vehicle exits, user provides ticket id
		- system validates ticket
		- calculates fee on time spent
		- frees spot for next use
	- pricing is hourly w/ same rate for all vehicles
	- system rejects entry if no compatible spot is found
	- system rejects exit if ticket invalid or already used
- types of core entities/relations:
	- vehicle: don't need to worry about because its external to system, don't manage it
		- known its type to match to compatible spot
	- parking spot: id, type to match vehicle types, and maintain occupancy
	- ticket: holds ticket ID, spot assigned, type of vehicle, when they entered
		- internal state to system
	- parking lot: orchestrate the whole system: 
		- vehicle enters, find available spot, generate ticket, mark spot occupied
- relationships:
	- simple: parking lot owns parking spots, parking lot creates tickets when vehicles enter, parking lot tracks active tickets
- class design:
	- ParkingLot:
		- where should spot occupancy be tracked?
		- if we track occupied as boolean field in ParkingSpot, search logic is simple and direct since spot knows its own state and you can just ask it
			- simple b/c we know state, just ask for it through iteration
			- issues: denormalization since occupancy is in both flag on the spot and activeTickets map (ticket references spot, occupied)
				- need to maintain consistency
				- design question: what does occupancy represent (spot's size and ID are permanent characteristics, but occupancy is dictated by the ParkingLot)
			- manage this occupancy as an intrinsic/extrinsic property 
		- better:
			- tickets tell you if a spot is occupied
			- if there's an active ticket referencing a spot, skip it
			- issues:
				- computing occupied set over and over again (if later we want concurrency, causes headaches since we have to lock the map)
				- still the cleanest since there's no denormalization 
		- another approach:
			- have a set that's technically redundant w/ the ticket data that maintains the occupied spot ids
			- set provides a clean concurrency boundary: when adding multi-entrance support later, becomes important
	- occupancy can be treated as a physical intrinsic property or a relational one 
		- here, occupancy is relational since its derived from a ticket referencing a spot
		- orchestrator manages tickets so manage occupancy
		- but occupancy can be physical state such as Amazon Locker where its a flag on the entity
		-  ```
	  class ParkingLot:
		  - spots: List<ParkingSpot> # the lot owns all spots
		  - occupiedSpotIds: Set<String> # 
		  - activeTickets: List<Ticket> # the lot needs to validate the ticket id string it gets
		  - hourlyRateCents: long # pricing is a system level policy, allows for creation of multiple different lots w/ different prices
			```
		* behaviors:
			* vehicle enters, system assigns a spot: enter(vehicleType) returns a Ticket
			* vehicle exists, validate ticket and calculate a fee exitTicketId() returns feed
		* constructor takes a list of spots and a rate
	* ParkingSpot
		* maintains track of id and spotType (type of vehicle can be in)
		* behavior: return the spot type (getSpotType()) and issues a ticket at entry (getId())
		* two different types of enums:
			* ```
			  enum SpotType:
				  MOTORCYCLE
				  CAR
				  LARGE
			  
			  enum VehicleType:
				  MOTORCYCLE
				  CAR
				  LARGE
			  ```
			 * two types of different enums even though they have the same value because they are semantically different things (one refers to the vehicle coming in the other the type of spot)
	* ticket:
		* tracks a id, spot id, vehicle type, entry time in MS
		* ```
		  class Ticket:
		   - id: string
		   - spotId: string
		   - vehicleType: VehicleType
		   - entryTimeMs: long
		  ```
		* spot id is a string not a reference to a parking spot to prevent accidental methods on spots
		* why is time a long?
			* arithmetic w/ longs, could use native language's time such as Python Datetime
		* where should the fee calculation logic be?
			* not the ticket as that violates single responsibility principle:
				* ticket is now a record of parking session and pricing calculator
				* if we change what data a ticket stores or fee calculation, have to change it there
				* pricing is not a property of ticket, is of the parking lot
				* ticket is now mutable, what if someone changes the rate when someone is parked, how to track that state
		* keep the ticket as a pure data holder, maintain the calculation logic in ParkingLot where all other business rules live
			* ticket stays immutable, just a record without business logic (parking lot orchestrates everything)
			* call exit ParkingLot gets entry time from ticket and calculates the fee 
			* when pricing gets complex, change it in one place
		* better:
			* separate the pricing strategy into an interface
			* extract pricing into its own abstraction w/ Strategy pattern
				* polymorphic logic
			* have an interface PricingStrategy that is then implemented by exact strategies (hourly pricing, dynamic pricing)
				* each must implement the Calculate Fee method
			* and then the parking lot owns a pricing strategy
			* and when exit is called, we get the active ticket, and then calculate price based on the Calculate Fee method
		* ticket is ultimately immutable, once ticket is issued, no changes
* implementation:
	* active tickets is better as a Map of String, Ticket
		* allows for lookup by Id to be quicker and clearer
	* enter:
		* find spot that matches type, no spot, throw error, add spot to occupiedSpotIds, generate unique ticket w/ spot id, vehicle type, and current timestamp
		* store in activeTickets map
		* return ticket
		* ```
		  enter(vehicleType):
			  spot = findAvailableSpot(vehicleType)
			  if spot == null:
				  return error
			  occupiedSpotIds.add(spot.id)
			  ticket = createTicket(generateId(), spot.id, vehicleType, currentTime())
			  activeTickets[ticket.id] = ticket
			  return ticket
		  ```
	* exit:
		* lookup the ticket by ID
		* not found, throw error 
		* calculate fee based on entry and current time
		* remove from occupied spot Ids
		* remove ticket from active tickets
		* return fee
		* ```
		  exit(ticketId):
			  if ticketId == null:
				  return error
			  ticket = activeTickets[ticketId]
			  if ticket == null:
				  return error
			  exitTime = currentTime()
			  fee = computeFee(ticket.entryTime, exitTime)
			  occupiedSpotIds.remove(ticket.spotId)
			  activeTickets.remove(ticketId)
			  return fee
		  ```
		* we treat ticket never existed and ticket already used as the same error
	* find available spot:
		* ```
		  mapVehicleTypeToSpotType(vehicleType):
			if vehicleType == MOTORCYCLE
				return MOTORCYCLE
			if vehicleType == CAR
				return CAR
			if vehicleType == LARGE
				return LARGE
			return error
			
			
			findAvailableSpot:
				requiredSpotType = mapVehicleTypeToSpotType(vehicleType)
				for spot in spots:
					if spot.spotType == requiredSpotType and spot.id not in occupiedSpotIds:
					return spot
				return null
			```
	* duration time:
		* ```
		  computeFee(entryTime, exitTime):
			  durationMillis = exitTime - entryTime
			  durationHours = durationMillis / (1000 * 60 * 60)
			  
			  if durationMillis % (100 * 60 * 60) > 0:
				  # we have a remainder
				  durationHours++
			  
			  return durationHours * hourlyRateCents
		  ```
	* parking spot:
		* trivial getters setters
	* ticket:
		* trivial getters setters
* extensibility:
	* extend to multifloor parking lot:
		* parking floor entity, each floor owns collection of spots, lot owns a collection of floors
		* floor becomes part of spot's identity, so spot IDs become something like 3-A15 for floor 3 section A, spot 15
		* finding available spot:
			* iterate through floors, find available spot and if not null return spot
		* with ten floors, smarter allocation based on even strategy pattern:
			* fill the lower floors first (simple iteration)
			* balance across floors: spread vehicles evenly so no floor gets congested, track spot counts per floor and prefer floors w/ more availability
		* proximity to destination: diff floors might be closer to diff stores, assign them to closest floor
	* add different pricing for different vehicle types:
		* maintain a map of vehicle type to rate in parking lot (allows us to store multiple rates)
		* in computeFee, look up the rate based on the vehicle type from the ticket
	* multiple entrances w/ concurrent access:
		* race condition where multiple threads find the same available spot and assign it, tickets have the same spot
		* solution: 
			* coarse lock enter so that only one vehicle can enter in a time
				* serialize all entrance requests
				* if each entry takes 100 milliseconds, find, generate, update can process 10 vehicles per second
			* great:
				* read-write lock, multiple threads can read the occupiedSpotIds concurrently but writes require exclusive access
				* use a read lock to search for spots, and a write lock to claim
				* ```
				  def _find_available_spot(self, vehicle_type):
					  with self._lock: # read with the lock
						  for spot in self._spots:
							  if (spot.spot_type == vehicle_type and spot.id not in self._occupied_spot_ids):
							  return spot
						  return None
				  def enter(self, vehicle_type):
					  while True: 
						  spot = self._find_available_spot(vehicle)
						  if spot is None:
							  raise Exception("no available spots")
						  with self._lock:
							  if spot.id not in self._occupied:
							  self._occupied_spots_ids.add(spot.id) # write lock to claim space
				  ```
				* better concurrency b/c multiple entrances can search for spots simultaneously