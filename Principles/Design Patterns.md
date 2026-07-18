- Patterns: ways to solve design problems
- Three categories: creational, structural, behavioral
- Creational patterns:
	- Control how objects get created
	- Factory Method:
		- helper that makes right kind of object for you so you don't have to decide which to create
		- hide creation logic and keep code flexible when exact type you need can change
		- useful for when supporting different types of something
			- different notification types
			- when making new EmailNotification, don't directly create
			- call `NotificationFactory.create(type)`
			- can just change your factory to handle different types of notifications
	- Builder:
		- create complex object step by step without worrying about order/construction details
		- used when an object has many optional parts or config choices
		- good for designing things like HTTP requests, DB queries, or configuration objects
		- makes construction more readable, handles optionals cleanly
		- but rarely used in LLD interviews unless designing API clients or complex configs
	- Singleton:
		- One instance of a class exists.
		- Use it when needed only one shared resource like a config manager or logger.
		- Not always needed, can just pass shared objects through constructors.
		- Singletons aren't idiomatic in Python, modules themselves are singletons (only imported once)
			- So create a module-level instance instead of the pattern.
		- Singleton needed when explicitly wanted a single-shared instance across the entire system.

- Structural Patterns:
	- Flexible relationships without tight coupling.
	- Decorator:
		- Behavior to an object without changing class.
		- Needed when requirements say add logging for specific operations or certain messages.
		- Instead of creating subclasses for every combination, wrap base object w/ decorators.
		- Have a `DataSource`class, and have a `FileDataSource` that extends upon the `DataSource`
		- Then have decorators that take in `DataSource`: `EncryptionDecorator` encrypts data before writing and reading. 
			- But uses the `send` methods of the wrapped class.
		- Useful when behavior gets added at runtime based on conditions.
		- Layer optional, combinable features without modifying underlying class.
		- In cases where there's a predefined type different, use subclass
		- Else, use decorator if dependent on run-time conditions.
	- Facade:
		- Coordinating class that hides complexity.
		- Useful pattern when wrapping messy code like inheriting complex subsystems

* Behavioral Patterns:
	* Control how objects interact and distribute responsibilities.
	* Strategy:
		* Conditional logic is replaced with polymorphism.
		* Different ways of doing the same thing, want to swap at runtime.
		* We create a base class.
		* Have subclasses implement on top of this.
		* Then use the base class to do manipulations based on the predefined contract. 
		* For payment methods, instead of doing `if/else` check for every single method, use polymorphism with subclasses that have a method that's in the central base class and just call that method. 
	* Observer:
		* Useful when designing systems where multiple components care about state changes.
		* For example:
			* Stock price changes and multiple displays update.
		* Create `Observer` abstract class that has `update` method.
		* Create `Subject` abstract class that has `attach`, `detach`, `notify_observers` method.
			* attaching and detaching adds the subject to the observer  
		* Stock class inherits from Subject, has a list of observers, has `attach` and `detach` method implemented
		* then for notify observers, invoke update by iterating over the list. 
		* then for all listeners (`PriceDisplay`, `PriceUpdate`), have them extend `Observer` and them override update with some sort of function that gets triggered.
		* then when the Subject does something and notifies observers, all subscribers get updated.
	* State Machine:
		* Handles transitions cleanly.
		* Object behavior has internal state, complex state transition rules.
		* Vending machine, document workflow, game states.