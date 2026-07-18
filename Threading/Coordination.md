* threads need to communicate and hand off work
* thread produces task, another consumes
* independent execution paths need to signal without burning CPU or corrupting state
* background tasks:
	* API handlers enqueue tasks, pool of worker threads process them asynchronously
* what if workers are ready to run but there's no work
	* busy waiting: each worker spins burning CPU
* can sleep them when there's no work
	* introduces latency
	* task arriving 1ms after worker goes to sleep waits nearly 100MS before being processed
* on the other hand:
	* what if producers are faster than consumers
	* each request enqueues background work
	* workers process 100 tasks per second, draining a queue of thousands takes minutes
	* but you're limited by memory
		* every task on queue is heap-memory object
	* queue unbounded, grows and grows till we hit a `OutOfMemoryError`
* things to solve:
	* efficient waiting: consumers should sleep when there's no work (but wake up when work arrives)
	* back pressure: producers should slow down when consumers can't keep up (prevent memory exhaustion)
	* thread safety: coordination mechanism needs to handle concurrent access without corruption
* two solutions:
	* shared state coordination: uses data structures multiple threads access directly
	* message passing coordination: avoids shared state, each component has its own input and communicates by sending messages
* shared state coordination:
	* threads communicate by reading/writing to same memory
	* producer adds item to queue, consumer removes it
	* queue is shared, synchronization primitives (locks, condition variables) ensure threads don't interfere
	* use condition variables:
		* lock protects a shared state
		* condition variable attatched to lock
		* thread needs condition to be true, calls `wait`
		* two things happen:
			* thread releases and goes to sleep
			* thread stops consuming CPU entirely, parked until explicitly woken
		* another thread changes shared state, signals condition variable to wake waiting threads
		* ```python
		  with condition:
			  while not condition_is_met():
				  condition.wait() # releases lock, sleep until notified
			  do_work()
			  condition.notify_all() # wakes all waiting threads
		  ```
		* `while` is important because we need to recheck condition (another thread may have consumed what was waiting for)
		* benefit over polling: sleep-based polling, workers waste CPU or have high latency
		* wait/notify: workers consume zero CPU when idle and wake immediately when work arrives
		* issue:
			* do we need to wake one thread or all thread
			* queue with producers/consumers waiting on the same condition variable
			* consumer finishes processing item, frees space
				* signals condition variable to pick a waiting thread to wake up
			* what to do?
				* if you wake up just one like a consumer when queue is empty, nothing happens
			* if you wake up everything, then you waste a lot of checks
			* solution: have separate condition variables (one for queue not empty that consumers wake up on, and the other is queue not full that producers wake up on)
	* use blocking queues:
		* thread-safe queue w/ special behavior when empty/full
		* remove item, call blocks instead of returning if empty
		* thread goes to sleep using condition variables under the hood
		* when another thread adds item, wakes you up and you get item
		* same thing in reverse when queue full
		* use `queue.Queue` from Python to do blocking operations
		* `put()`: blocks if queue full
		* `get()`: blocks if queue empty
		* ```python
		  def submit_task(self, task) -> None:
			  self._queue.put(task)
		def worker_loop(self) -> None:
			while True:
				task = self._queue.get()
				task()
		  ```
			* returns once an item becomes available (will block indefinitely until item is available)
		* `maxsize`: bounds queue
		* blocking queue is default answer for producer-consumer problems
		* always have a bound for the queue
			* pass a capacity 
			* size buffer based on expected burst tolerance (workers handle 100 tasks per second, want to absorb a 10 second spike, then make it 100 * 10 = 1000 tasks)
		* what to do when the queue fills up?
			* block w/ `put()`
				* slowing down is acceptable
			* timeout and reject w/ `offer(timeout)`
				* request paths where you can't stall
			* drop and log w/ `offer()`
				* lossy workloads like analytics where dropping under load is acceptable
			* interrupted exception:
				* both `put()` and `take()` throw this
				* thrown when another thread interrupts thread while its blocked waiting
				* propagate it up by acknowledging a throw
				* or if needed to be caught, restore interrupt status by calling `Thread.currentThread().interrupt()`
			* graceful shutdown
				* workers are blocked for tasks, how to stop them
				* interrupt worker threads: 
					* so it will throw an `InterruptedException` and we just catch it and break out of worker loop.
				* `take()` blocks forever, so use `poll(timeout)`: 
					* allows us to check for a shutdown flag periodically when the worker is woken up
				* poison pill:
					* special task that means shut down
					* submit a pill per worker int he queue, each process will shut down when processing that task
					* works well without interrupting threads or not wanting to use timeouts
	* message passing coordination:
		* actor model:
			* has three things
				* mailbox (queue of incoming messages)
				* processes messages one at a time
				* sends messages to others
			* a Python actor has `queue.Queue`for mailbox and runs on a dedicated thread
			* one message is processed at a time so there's no concurrency checks in the message handler
			* since multiple threads could be modifying the the message queue its a blocking queue
		* useful when multiple independent entities that need to occasionally communicate
		* scales well: actors don't share state, distribute them across machines
		* actors aren't always right choice
			* blocking queue is simpler and more direct for simple producer-consumer problem
			* actors add overhead in terms of message types, actor lifecycles, and message delivery guarantees
		* so:
			* "process tasks in background": have a blocking queue
			* "coordinate many independent entities with own state": consider actors 
		* need to worry about mailbox overflow
			* fill up if producers are faster than actor can process result in overflow (but can fix this by configuring mailbox size, overflow behavior)
		* message ordering (messages from actor A to B are in order, but if A and C send to B, interleaving is undefined)
		* debugging: if something is wrong, bug might be in how messages flow rather than a single piece of code
		* request-response patterns: actors communicate asynchronously so if you need to send message and wait for reply, build pattern yourself
			* send message with callback address and wait for response message
* when is this used in?
	* process requests async.
	* users make requests, but most of the work is slow
	* api handler is producer (receives request, does minimum work to respond to user, hands off task for background processing)
		* workers or actors are consumers
	* in context of EmailService:
		* add a queue
		* save user to database
		* then enqueue to EmailQueue
		* Worker thread consumes from EmailQueue and then sends appropriate email
	* where else:
		* image upload:
			* users upload PFPs, upload API saves original, enqueues processing task, returns success immediately
			* Workers: pull tasks and process them
		* payment processing:
			* complete a checkout
			* need to charge card, send reciept, etc.
			* don't block entire flow, enqueue a task
		* report generation:
			* generating a report takes 10 minutes
			* so queue something downstream
			* tell user that its pending
			* when it gets processed, tell the user
	* handling bursty traffic
		* when a lot of traffic happens, can just naively scale but that wastes servers
		* add a buffer: requests pile up in the queue, workers churn through them
		* after burst ends, workers drain the queue
		* the queue is set to the max capacity burst size
		* this smooths out traffic and maintains the same rate of downstream worker event processing
		* use `offer(timeout)` when queue is full and blocking is unacceptable