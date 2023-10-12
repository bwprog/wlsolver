# wlsolver
Solve world lists games

- This program will solve a word game like squaredle if the board is a true square (3x3, 4x4, etc.).
- There are two solving methods, 'brute force' and 'optimized'.
- You can specify the min and max word length.
- There is a verbose option to view more details on each step.
- It will take any word list file as long as there is a single word on each line and ignores case. The unix words list is provided as are several Moby II project files. The default combines Moby II crossword and crossword delta along with a few inclusions as they are found missing.
- There is an 8 way logic movement function defining valid moves and guards against squares only. This may be extended in the future for non-standard puzzle shapes.
- This requires python 3.11, and 3rd party modules typer, and rich (and their dependency 3rd party modules).
- Development uses ruff (with almost everything enabled) and pytest though tests have not yet been implemented.
- This should be fully type annotated. This was incredibly helpful with things like the ints within lists within lists as values in dictionaries. A lot of needless troubleshooting was avoided by the linter telling me I was trying to do things like assign a list of ints to a list of lists of ints, or when I lost track of which variable was a letter and which an int and tried to use the wrong one when slicing.

## Solving Methods

### Brute Force
- This method creates a dictionary of lists of lists and populates it with every possible move available, from single digit through to the max word length specified (or board size, whichever is larger).
- it then converts those digits to letters and puts them into a dictionary of sets.
- the potential words sets are then '&' to the real word sets with the entries in both being playable words as the output.

##### Pros:
- This was very easy to implement.
- It works and is accurate.
- A backup check to ensure the same output as the optimized method.

##### Cons:
- It is fast on an AMD 6850U with 16GB RAM with single digit word lengths and is acceptable speed up to about a maximum word length of 10 on a 4x4 board.
- it becomes progressively slower as the board size or word length increase, and huge amounts of RAM start being consumed. Originally it took 28 minutes to solve a 4x4 board up to 12 length words. I've optimized it as much as I could switching lists that don't rely upon order over to sets and then changing if/elses to match/cases. Now that same 28 min solve happens in 28 seconds.
- It is unbounded so you may run out of resources and your OS crash, or incredible slowdown as the OS pages out to disk if you try to solve too big a puzzle.

### Optimized
- This creates a dictionary of valid moves from an existing board placement.
- This takes all words that were available (already pruned via min/max length) and further removes any words containing non-playable letters. Letter counts are not factored so 'that' with two 't's would still be in the list even if the board only has one 't'.
- This starts with the first letter of the word and builds lists of possible moves and keeps adding to those moves with each additional letter in the word until the whole word has been proven valid or breaks out of the loop. For 'that', it starts with 't' as a key and creates a list of a list of 't' positions (say spot 14). Then if finds 'h' spot (13) and confirms it is a valid move from 14 so creates a 'th' key with a list of [[14, 13]]. It moves on to 'a' spot (9) which is also valid so creates a 'tha' key containing [[14, 13, 9]]. Finally it finds 't' at 14, but is prevented from adding it since 14 is already in the list so it breaks the loop with the word being unplayable. Lists of lists are used since letters may be on the board in multiple spots so there could be multiple pathways to attempt to make the word.
- I think I may have inadvertently implemented a form of b-tree or Trie logic. My intent was to follow human thought of building the word from start to finish via available paths.

##### Pros:
- Incredibly fast. It can process a 7x7 board with max word length, find 983 valid words out of 102,000 and print it all out in half a second. The Rich progress bars I copied from the Brute Force method only serve to slow down the Optimized method.
- light memory use.
- It *finally* works.

##### Cons:
- It was very difficult (as a novice programmer) to create the logic to implement. After a lot of spare time troubleshooting and rewriting over and over, I finally added print statements everywhere. It took 17 tabbed print statements (preserving indented for loop structure) nested among the 5 for loops, 4 if logics, the bool flag statements, and the break and continue statements and created a small word list test file, in order to identify where the logic was failing and move steps around until it worked.

## Execution
Download to a local folder and unzip.
From within the folder, create a pipenv virtual environment:

```
pipenv shell
```

To install the dependencies:

```
pipenv install
```

Or install dependencies including development (ruff and pytest):

```
pipenv install --dev
```

Run the program:

```
python ./src/wlsolver --help
```

And because programmers are incredibly, stubbornly arrogant to the point they refuse to add this to the pipenv documentation because 'everyone should know how to exit a shell' even though you use pipenv to create the virtual environment shell and would naturally expect to use a pipenv command to leave it, to exit the virtual environment, just type exit:

```
exit
```


## Future
- Add solving for non-square boards
- Guard print statements from non-existent keys.
- Remove brute force method (probably when implementing non-square boards)
