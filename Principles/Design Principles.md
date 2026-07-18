- KISS: Keep it Simple, Stupid
	- simplest solution that works is typically the right one
	- pick the most straightforward pattern
	- only add complexity when simplicity stops working
- DRY: Don't Repeat Yourself
	- logic in multiple places, pull it into one place
	- helps w/ maintenance:  validation rules change, update one method instead of every single place in the codebase
	- don't take it too far: two pieces of code look similar but different purposes, duplication is fine
	- DRY can conflict w/ KISS, simplest solution is to duplicate code in two places rather than abstraction
		- acknowledge both sides
- YAGNI:
	- build what's necessary now, not what might be needed later
	- don't enable extensibility in every aspect
- Separation of concerns:
	- code should handle different responsibilities
	- shouldn't know about each other's internals
	- UI shouldn't have business logic for example
	- TicTacToe:
		- don't have display logic, input handling, and game rules being explicitly handled in a single play method
		- separate each responsibility into its own class (Board class, Display class, InputHandler class)
			- logic changes happen at each class
				- console to GUI: InputHandler
				- change how board gets displayed: change Display
				- new win conditions: update Board
- Law of Demeter:
	- principle of least knowledge
	- method should only talk to its immediate friends not reach objects through chaining
		- avoid `order.getCustomer().getAddress().getZipCode()`
	- method on `Order` called `getCustomerZipCode()` that handles navigation internally
	- comes up when defining class methods: instead of returning complex objects, return specific data
- Object Oriented Design:
	- SOLID:
		- Single Responsibility Principle:
			- class has one reason to change, mixes multiple concerns, split them
			- `Report` class: handles content generation, PDF formatting, and file storage all in one place
			- split into separate classes:
				- `Report` for generating content
				- `PDFPrinter`, formating
				- `FileStorage`, handles saving
		- OCP: Open Closed Principle
			- open for extension, closed for modification
			- add new behavior without changing existing code
				- use interfaces/abstract classes to add new implementations without touching OG code
			- any modification to existing code, we risk breaking things that already work
			- old code never changes, so can't break it
				- instead of having if statements chained to do payments, implement abstract methods that can then be extended
		- Liskov Substitution Principle:
			- subclasses should work even when the base class works
			- method that accepts Bird, passing in Penguin shouldn't break things even though penguins can't fly
			- code uses parent class/interface, should be able to use any subclass without knowing what specific subclass
				- throws exception for method that parent class provides, red flag you're violating LSP
			- things that not all subclasses can use can be put into an interface that only certain subclasses can implement
				- `Bird`: has an abstract method `eat`
				- Because not all birds can fly, there's a class `FlyingBird` that extends `Bird` but also has a `fly` method
				- So things that don't fly directly inherit from `Bird` 
				- Things that do fly inherit from `FlyingBird`
		- Interface Segregation Principle:
			- Prefer small focused interfaces over large general purpose ones
			- Don't force classes to implement all methods
			- Instead, break it up into smaller interfaces/abstract classes that can then be inherited from/implemented for specific behaviors
			- `Worker` class:
				- has `work, eat, sleep` methods
				- Robot inherits from this. 
					- but it doesn't eat or sleep so it would no-op or throw exception.
				- Better:
					  Have Workable, Feedable, Restable classes and have Human implement all of them, but Robot only Workable
		* Dependency Inversion Principle:
			* Code should work on generics.
			* Depend on abstractions not concrete implementations.
			* Define interface based on business logic needs, have implementations conform to that interface. 
			* Enables better testability and flexibility:
				* If a `NotificationService` class depends on a concrete `EmailSender`,  can't unit test without real emails
				* depends on an interface, can inject a mock for testing
				* instead, just have `NotificationService` depend on a generic `MessageSender` interface that `EmailSender` extends from 
					* `MessageSender`: implements `send`
					* `EmailSender`: extends from `MessageSender`, and implements `send`
					* `NotificationService`: accepts a type of MessageSender
					* enables swapping of anything that implements `MessageSender`