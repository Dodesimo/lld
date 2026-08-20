- requirements:
	- different sized compartments: small, medium, large, match size exactly
	- if there are no compartments of the right size, you reject
	- package is already at the locker location
	- code is returned
	- wrong code, return error no lock out
	- one customer can have multiple packages in the system at once, each gets own token/id
	- code expires after seven days, expired code usage gets rejected
	- if all compartments are full when driver tries to deposit, return error
- in total:
	- carrier deposits package by specifying size (small, medium, large)
		- assigns an available compartment of matching size, opens and returns access token
	- access token generated and returned
		- one access token per package
	- user gets the package by entering access token 
		- system validates and throws error if necessary
	- access tokens expire after 7 days
		- expired codes are rejected if used for pickup
		- package remains in compartment till staff removes it
	- staff can open all expired compartments to manually handle packages
		- staff physically removes packages sends them back to the sender
	- invalid access tokens rejected with clear error messages
- core entities:
	- don't need to have package as a specific entity, just care about the size
	- compartment: container w/ size and ID
		- physical locker slot (ID, size, tracks occupancy state)
	- locker: whole system, scan compartments, find available one, generate a code, and tie it together
		- orchestrator, owns all compartments and access token lookup map
	- access token: not just a code, token with expiration time (owns expiration logic and the mapping to the compartment)
		- bearer token for compartment access, holds code, expiration timestamp, reference to the compartment it unlocks
- class design:
	- Locker:
		- state:
			- needs to track the collection of all compartments, which ones are occupied
			- map from access token code to access token object to get expiration details and such
			- determining where state belongs, ask whether physical or relational (physical state lives on the entity, relational state lives in the orchestrator b/c system managed relationship)
		- operations:
			- `depositPackage(size)`: opens compartment, returns access token code
			- generate/lookup access tokens
			- `pickup(tokenCode)`: opens compartments or throws error
			- `openExpiredCompartments()`
		- ```
		  class Locker:
		  - compartments: Compartment[]
		  - accessTokenMapping: Map<string, AccessToken>
		  + Locker(compartments)
		  + depositPackage(size) -> string | error (return product id)
		  + pickup(tokenCode) -> void | error (return nothing if sucess)
		  + openExpiredCompartments() -> void (timeout)
		  ```
			* `depositPackage`: returns the token code, compartment automatically opens when called
			* `pickup`: returns void, the door opens so we don't need the number
	* Access Token:
		* needs to track actual code string, the expiration timestamp, reference to the compartment the access token unlocks
		* behavior:
			* see if expired, get the compartment, get the code
		* ```
		  class AccessToken:
			- code: string
			- expiration: timestamp
			- compartment: Compartment
			
			+ AccessToken(code, expiration, compartment)
			+ isExpired() -> boolean
			+ getCompartment() -> Compartment
			+ getCode() -> string
		  ```
			* `getCode()` returns to caller during deposit
			* `isExpired()`: lets callers check validity
			* `getCompartment()`: gets access to compartment reference
	* Compartment:
		* ```
		  class Compartment:
			  - size: Size
			  - occupied: boolean
			  
			  + Compartment(size)
			  + getSize() -> Size
			  + isOccupied() -> boolean
			  + markOccupied() -> void
			  + markFree() -> void
			  + open() -> void
			    
		  enum SIZE:
			  SMALL
			  MEDIUM
			  LARGE
		  ```
- implementation:
	- ```
	  depositPackage(size)
		  compartment = getAvailableCompartment(size)
		  if compartment == null
			  throw Error
		  compartment.open()
		  compartment.markOccupied()
		  accessToken = generateAccessToken(compartment)
		  accessTokenMapping[accessToken.getCode()] = accessToken
		  return accessToken.getCode()
	  ```
	* how does getAvailableCompartment work?
		*  bad: iterate through and find compartments that don't have a token 
			* tokens expire after 7 days but can't immediately delete from the mapping
			* need to keep the token around to differentiate between invalid token and a token that has expired
		* good: maintain a queue of compartments based on size that can be dequeued when needed and enqueued back when done
			* however, overly complex
		* great: 
			* just iterate through each compartment and use a isOccupied() flag tied to the compartment
			* iterate through and return compartment that has size and has occupancy
	* ```
	  pickup(tokenCode)
		  if tokenCode == null || tokenCode.isEmpty()
			  throw Error("Invalid")
		  accessToken = accessTokenMapping[tokenCode]
		  if accessToken == null:
			  throw Error("Invalid access token code")
		  if accessToken.isExpired():
			  throw Error("Access token has expired")
		  compartment = accessToken.getCompartment()
		  compartment.open()
		  clearDeposit(accessToken)
	  ```
	* generate token
	* ```
	  generateAccessToken(compartment)
		  code = generateRandomCode() // uuid
		  expiration = now() + 7.days()
		  return AccessToken(code, expiration, compartment)
	  ```
	* ```
	  clearDeposit(accessToken):
		  compartment = accessToken.getCompartment()
		  compartment.markFree()
		  accessTokenMapping.remove(accessToken.getCode())
	  ```
	* opening expired components:
		* ```
		  openExpiredCompartments()
		  for tokenCode, accessToken, in accessTokenMapping:
			  if accessToken.isExpired()
				  compartment = accessToken.getCompartment()
				  compartment.open()
		  ```
		* doesn't call clearDeposit because when staff marks packages removed, separate method gets called to mark them as removed
	* access token implementation:
		* ```
		  isExpired()
			  return now() >= expiration
		  getCompartment()
			  return compartment
		  getCode()
			  return code
		  ```
	* compartment:
		* ```
		  getSize()
			  return size
		  isOccupied()
			  return occupied
		  markOccupied()
			  occupied = True
		  markFree()
			  occurpied = False
		  ```
* extensibility:
	* size fallback:
		* we iterate through sizes that are greater than equal to the exact size
		* ```
		  sizesInOrder = [SMALL, MEDIUM, LARGE]
		  startIndex = indexOf(requestedSize)
		  for i in range(startIndex):
			  size = sizesInOrder[i]
			  for c in compartments:
				  if c.getSize() == size && !c.isOccupied():
					  return c
		  return null
		  ```
	* handle compartments that are broken or under maintenance:
		* add a status field to track operational
		* skip ones that are broken
		* ```
		  enum CompartmentStatus:
			  AVAILABLE
			  OCCUPIED
			  OUT_OF_SERVICE
		  
		  class Compartment:
			  -size: Size
			  -status: CompartmentStatus
			  +isAvailable() -> boolean
			  +markOccupied()
			  +markAvailable()
			  +markOutOfService()
			  +markInService()
			  // these all change the internal state/status of the compartment 
		  ```
	* ensure packages get deposited before generating access tokens:
		* two phase
			* reserveCompartment: get a compartment and unlock it, place package, call confirm
			* confirm deposit: generates access tokens and marks it occupied
			* add new state (RESERVED) and track reservations separate from access tokens
			* timeout logic: if driver reserves but never confirms 2-3 minutes, system should auto-cancel and free up compartment
			* rest of code with the state remains the same (since we add another invalid state)
	* notes:
		* when you clear for the staff (open expired compartments) don't do clear because that would remove the token and we can't differentiate between expired and invalid tokens