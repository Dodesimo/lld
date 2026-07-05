- prevent data corruption when multiple threads access a shared state
- the pattern that shows up:
	- rate limiters checking if under limit before allowing request
	- connection pools checking if connection is free before handing it out
	- caches checking if there's room before adding item
	- when validity of check changes before we can act on it, correctness problem
- solutions:
	- coarse-grained locking
		- thread acquires a lock, every thread trying to acquire same lock waits till first thread releases
		- ```python
		  with self._lock:
			  if seat_id in self._seat_owners:
				  return False
				self._seat_owners[seat_id] = visitor_id
				return True
		  ```
		* python: `with` is a context manager
		* lock acquired at the start of the block, automatically released when block exits, even if exception happens. 
		* creating a critical section where only one thread executes at a time
		* check and update happens together, doesn't interleave
		* can't let go of the lock too early (this breaks atomicity)
		* operations that need to be atomic together needs to have the same lock object
		* all operations that maintain an invariant needs to be protected by the same lock
		* best solution when critical section is short, contention is moderate
		* tradeoff of throughput:
			* booking operations: single lock makes others wait while someone else currently booking
			* what if Bob is booking seat 12B and Alice is booking seat 7A?
				* operations don't actually conflict, but lock doesn't know that
			* fine-grained locking
		* read/write locks:
			* if a workload is very skewed towards reads, cache gets queried thousands of time but only updated once a minute
			* no need to block on every single read
			* use a read-write lock: read (shared) and write (exclusive) operations
			* multiple threads hold read lock, but write lock is exclusive
				* thread wants to write waits for all readers to finish, then blocks everyone till write completes
				* ```python
				  def get(self, key):
					  with self._read_count_lock:
						  self.read_count += 1
						  if self._read_count == 1:
							  self._lock.acquire() # if there's readers don't allow for any writes
					try:
						return self._data.get(key)
					finally:
						with self._read_count_lock:
							self._read_count -= 1
							if self._read_count == 0: # only when we don't have any readers
								self._lock.release()
				  ```
	* fine-grained locking:
		* uses multiple locks where each lock protects a smaller piece of state
		* ```python
		  def _get_lock(self, seat_id: str) -> threading.Lock:
			  with self._locks_lock:
				  if seat_id not in self._seat_locks:
					  self._seat_locks[seat_id] = threading.Lock()
				  return self.seat_locks[seat_id]
				  # this creates a lock per seat id. 
				  # there will be parallel requests, with a lock for each seat
		  ```
		* this is far more scalable, contention issues happen at the per-seat level
		* issues:
			* easier to deadlock
			* if users want to swap, we need to lock both seats, but this can introduce a deadlock
			* the fix is to acquire locks in a consistent order, threads lock smaller seat ID first
			* fine-grained locking introduces practical overhead
			* creating locks dynamically, so map holding them grows w/ each new seat
		* ultimate decision:
			* have a coarse-grained lock (works most of the time when a human is triggered the operation)
	* atomic variables:
		* lock contended, threads can't do anything useful (spinning or parked by the OS)
		* atomic variables: allow ready modify writes in a single step without lock
			* CAS: compare and swap
				* CAS: set variable to new value but only if currently equals expected value
				* if another thread changed value between read/write attempt, CAS fails and we retry
		* python's GIL (Global Interpreter Lock) doesn't make operations atomic, Python lacks built-in atomics
			* C++ has `std::atomic` that can get updated w/ `compare_exchange_strong` and `compare_exchange_weak`
		* so you would have to build an atomic integer though a `threading.Lock`
		* for complex updates, use a CAS loop:
			* read current value, compute to set, and CAS to change it
			* ```c++
			  int expected = counter.load(); // 1. Read the initial value
			  int desired;
			  do {
				  desired = expected + 1; // compute the new desired state
			  } while (!counter.compare_exchange_weak(expected, desired));
			  // see if counter is equal to expected, if so changed to desired
			  // if its not set counter's value to expected
			  ```
		* optimistic concurrency: assume no one interferes and retry when assumption wrong
			* most times CAS succeeds, making it faster than acquiring a loop
		* atomics only work for single variables
			* can't have multiple values change in terms of updates standing on their own
	* thread confinement:
		* don't share data across threads in the first place
		* partition data so thread owns a slice
		* so in a booking system, 
			* Thread 1 handles section A to M
			* Thread 2 handles section N to Z
			* each thread has a private seat map
		* pattern shows up in DragonFly (Redis alternative), Actor systems like Akka, and Database connection pools that give each thread own connection
		* operations across multiple partitions require coordination
		* load imbalance: issue if some partitions are hotter than others
		* confinement needs to be strictly enforced
		* overkill for the most part, so just mention it
* bugs:
	* check then act:
		* you check and another thread invalidates check between when read and acted upon
		* for example w/ a rate limiter
			* bug between check and update
			* thread A reads count as 99
			* thread B reads count as 99
			* seeds under limit, proceeds to update
			* both increment 99 to 100
			* so we end up making a 101 requests when limit is 100
		* fix: make check and act atomic
		* connection pools: benefit from fine-grained locking (have locks on each connection)
			* different connections don't conflict
			* throughput demands are high enough to make coarse-grained locking
	* read modify write:
		* get a value, compute, and write it back
		* issue: two threads read the same value, both compute from it, both write back
		* there maybe an interleaving of instructions that cause a issue (loss of an increment)
		* just use a lock (updating complex balance, modifying data structure, keeping multiple fields in sync) or atomic (just for incrementation)
		* 