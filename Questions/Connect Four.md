- requirements:
	- build OOD for two-layer Connect Four Game, players take turns dropping discs into 7 column, 6 row board
	- first to align four of their own discs vertically, horizontally, diagonally wins 
- clarifying questions:
	- what are core actions
		- players choose column from 0 to 6
		- disc falls to lowest spot
		- game ends when four in a row wins
		- if board fills up without a winner, draw
	- how errors should be handled
		- return false or raise error for invalid moves
		- out of turn, reject
	- boundaries of system
		- one game at a time
		- only backend logic
	- plan for future extensions
		- no move history or support undo
		- board size is always 7 by 6
- core entities and relationships:
	- Game:
		- holds board, tracks what player's turn
		- manages Game state (in progress, won, draw), enforces turn-based rules
		- player makes a move, validates it, tells board to place Disc, check if move won, switches turn
	- Board:
		- 7 by 6 grid where discs live
		- Owns grid state, handles disc placement
		- Check if column is full, where disc should fall
		- whether four discs are connected
	- Person:
		- Simple data holder w/ name and disc color
- Class Design:
	- Game:
		- Design Game class, then work down to board and player.
		- Needs to track two players, whose turn it is, the board.
		- Also the game state (in progress, won, draw)
		- Who won. 
		- how do we maintain this information?
			- can have three boolean flags
				- ```isOver
					  hasWinner
					  isDraw
				  ```
			- but this can result in inconsistent together flags
		- better: 
			- have a GameState enum:
				- ```
				  enum GameState:
						IN_PROGRESS
						WON
						DRAW
				  ```
				* this enforces the correct game state
				* when someone wins, correctly set the state
				* can't represent both a win and a draw
				* issue:
					* have a seperate `winner` field
					* can still represent `STATE=IN_PROGRESS` w/ `winner = somePlayer`
				* best solution: enum w/ `WON` state that has the winner
		* so game class has:
			* ```
			  class Game:
				- board: Board
				- player1: Player
				- player2: Player
				- currentPlayer: Player
				- state: GameState (either IN_PRORGESS, WON, DRAW)
				- winner: Player? // could be null
				+ Game(player1, player2) // constructor
				+ makeMove(player, column) -> bool // only method that mutates game state
				+ getCurrentPlayer() -> Player
				+ getGameState() -> GameState
				+ getWinner() -> Player?
				+ getBoard() -> Board
	 
			  ```
	- Board:
		- owns grid, knows where discs are, whether column has space, how discs fall, etc.
			- more specifically need to know the dimensions
			- the current occupancy of each column
			- whether there's at least one empty cell left
			- enough information in the grid to check contiguous disks
		- ```
		  class Board:
		      - rows: int
		      - cols: int
		      - grid: DiscColor?[rows][cols]
		      - Board() // constructor
		      - getRows() -> int
		      - getCols() - > int
		      - canPlace(column) -> bool
		      - placeDisc(column, color) -> int (returns the row where the disc lands)
		      - isFull() -> bool
		      - checkWin(row, column, color) -> bool
		      - getCell(row, column) -> DiscColor? // return the color of the disc there 
		  ```
	- Player:
		- we just need to track the name/ID, and disc color
		- ```class Player:
		  - name: string
		  - color: DiscColor
		  
		  + Player(name, color)
		  + getName() -> string
		  + getColor() -> DiscColor
		  ```
- Implementation:
	- Game:
		- for makeMove:
			- place the disk w/ `board.placeDisc(column, player.getColor())`
			- check for win through `board.checkWin(row, column, player.getColor())`
			- switch turn to other player
			- return true
			- edge case to handle:
				- game is over
				- wrong player's turn
				- invalid column or column is full
			- `placeDisc` handles all board-related validation, return -1 if move is invalid
				- Game handles game rules, Board handles grid rules
				- so we don't explicitly check column bounds and if column is full
			- alternatives:
				- `makeMove` throws exceptions instead of returning booleans (boolean is just clearer)
				- `makeMove` implicitly uses `currentPlayer` without taking player as argument (but this causes issues in a networked setting where moves arrived w a player)
	- Board:
		- `placeDisc`:
			- find lowest empty row in that column from rows - 1 and move upward until we find a null spot
			- place disc, set `grid[row][column] = color`
			- literally iterate and change the color and return the row
		- `checkWin`:
			- define four directions (`(0, 1), (1, 0), (1, 1), (-1, 1)`)
			- for each direction, count the contiguous discs
			- if any of them reaches four or more, return true
			- edge case: row or column out of bounds, return false
			- a cell that doesn't match the given color, return false
			- don't create checkers that inherit for a base Checker and then implement individual check logic and then apply it
				- this doesn't make sense because the win conditions never change, the game has four directions and will always 
				- creating four separate checker classes creates extensibility that doesn't make sense
				- all four checkers do exactly the same w/ different numbers
			- instead:
				- unified directional vector approach:
				- given a list of directions
				- maintain a count, and then go in all the directions, count in those directions
					- go in the negative and positive versions of the direction
				- if the count is greater >= 4, return true
				- count function:
					- while r and c are in bounds and the grid is the correct color, increment count
- extensibility:
	- different board sizes:
		- just change the board constructor to accept different values
	- undo:
		- add a stack that keeps track of moves (player, row, column)
		- undo:
			- pops move, clears cell, reverts currentPlayer, recalculates state
	- bot:
		- rules don't change, Game still enforces turns and Board has grid logic
		- for the game, the bot can just call make move
		- bot engine has a method called `chooseMove` that takes a game
		- get the game board
		- iterate through columns
		- find the first column to place in
		- then return that
		- we don't change Board at all or makeMove
		- thin layer on top that picks a Column
	- can make Player an interface w/ HumanPlayer and BotPlayer implementations
	- Human player doesn't do anything (just data), so making Player adds abstraction w/o any value.