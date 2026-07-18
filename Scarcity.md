- limited resources when demand exceeds supply
- finite connections, limited memory buffers, expensive resources only created once
- in database connection pool, what if request grabs connection and never returns it
	- blocks connection and prevents other requests from getting connections
- solutions:
	- semaphores: limit how many threads can hold resource simultaneously
	- resource pooling: actual resource objects, not just permissions
	- limit concurrent operations (download managers, API rate limiters)
	- limit aggregate consumption (bandwidth limiting, memory budgets)
	- reuse expensive objects like connection pools
	- maximization utilization through work stealing, batching
- semaphore:
	- limits how many threads do something
	- have a permit count that dictates how much chan run concurrently
	- threads acquire before starting and semaphore decrements counter
	- when finished, release, increment it back
	- counter hits zero, next thread blocks until permit released
	- using semaphore for sending requests over flight:
		- ```python
		  import threading
		  class APIClient:
			  def __init__(self):
				  self._semaphore = threading.Semaphore(5)
			  def make_request(self, endpoint):
				  with self._semaphore:
					  return self._http_client.get(endpoint)
		  ```
			* five requests in flight, request wanting to be sent goes to sleep
			* when one request comes back, we send it
	* issue:
		* what happens if exception throw, write code with finally block (try finally)
		* doesn't help w/ handing out specific objects (need resource pooling)
* resource pooling w/ blocking queue:
	* don't need to cap how many connections in use (need to hand out the actual connection objects themselves)
	* blocking queue:
		* thread needs connection, pulls from queue
		* if queue empty, thread blocks
		* if thread finishes, connection gets returned, waking up a waiting thread
	* use python's `queue.Queue`
		* `get()` blocks till item available
		* `put()` adds items
		* we can set a `maxSize` in the constructor
		* when all connections checked out, queue is empty
		* next thread takes on empty queue, blocks
		* when a thread returns its connection in the blocking queue (`put()`)
		* queue wakes up a blocked thread
		* hands connection and thread proceeds
	* can't use a semaphore in this context for resource distribution because it only counts concurrent operations
	* use `finally` (if something throws exception, lost forever)
	* issues:
		* initialization is slow (connection created up front during construction)
		* so startup slow, subsequent requests are fast
		* use lazy initialization, create connections on demand to max pool size
		* makes startup fast, but first few requests are slower
			* just go with startup (simpler, avoids race conditions, predictable performance once pool is running)
			* avoids lazy initialization race conditions
		* what if connections are stale or broken?
			* handed out, test first
			* if dead, then discard and create
		* make sure to always initialize to the queue capacity
		* if thread is sleeping forever on request path, blocking is dangerous because requests are expected by users to be seen immediately
			* instead of take use poll w/ timeout
	* fairness:
		* multiple threads blocked waiting for a resource, which one gets it when aavailable?
		* most times its FIFO, but for strict fairness guarantees
* common problems:
	* limiting concurrent operations
		* have operations that run concurrently, but need to cap how many run at once
		* limit comes from protecting downstream service or staying within memory bounds
		* ```python
		  import threading
		  from pathlib import Path
		  class DownloadManager:
			  def __init__(self):
				  self._semaphore = threading.Semaphore(3)
			  def download(self, url, destination):
				  with self._semaphore:
					  data = self._http_client.download(url)
					  destination.write_bytes(data)
		  ```
			* three downloads run at once.
			* if a thread needs to download, blocked until one finishes.
			* finally block ensures release when download completes/fails 
	* limit aggregate consumption:
		* threads complete for a shared budget, each operation consumes a variable amount
			* because of this, operations have different sizes
		* solution: use a semaphore where each permit represents unit of the resource
		* for disk i/o limits, want at most 100MB data, threads write files that track how much data is in flight
			* before writing, acquire permits equal to file size
			* not enough permits, wait until outgoing writes complete
		* each write acquires permits equal to size, rounded up to the nearest MB
		* files smaller than 1 MB acquire at least one permit to prevent tiny writes
		* so the idea is that operations consume different amounts of bandwidth, memory, IO
			* use a semaphore where permits represent resource units
			* each operation gets permits equal to what it consumes, releasing when done
	* reuse expensive objects:
		* constraint is that you have a fixed set of expensive objects costly to create but can be reused
		* database connections take time to establish, GPU contexts consume memory, etc.
		* we are actually managing actual stateful objects, not just counting # of connections
		* this is the blocking queue pattern:
			* threads take object form the queue, use it, and then return a finallyblock
			* handles all blocking, waiting automatically
		* we maintain a queue of usable objects that are expensive to create initially
	* maximizing utilization:
		* basic connection pool hands out connections on demand, waiting for them to return
		* these threads hold connections but the results are getting processed by something downstream
		* things finish quicker than others, they are blocked by something that's longer
		* solutions:
			* work stealing: instead of single queue that feeds all workers, each worker maintains own queue
			* worker queue empties: steals tasks from another worker's queue
				* all workers are busy even though task durations vary significantly
			* batching:
				* batch writes together, acquire one connection, write 100 rows, and then release
				* this prevents situation where 1000 small database writes made w/ acquiring and releasing a connection 1000 times wastes time on pool management.
				* pool: has less acquisitions, each does more useful work
					* we trade latency for throughput
					* individual items need to wait to be grouped but the total work per second goes up
			* adaptive sizing
				* adjust pool capacity based on demand
				* ten connections might just be too small during peak traffic
					* so we boost the number of connections
				* ten would also be wasteful during quiet periods
					* so we reduce the number of connections
				* issue:
					* we need to tune this boosting or reduction
					* growing too quickly, we overwhelm the DB during spikes
					* shrinking too quickly, we pay setup costs