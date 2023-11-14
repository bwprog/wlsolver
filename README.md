# wlsolver
Solve world lists games

- This program will solve a word game like squaredle. The board does not need to be square, but the row lengths must match.
- You can specify the min and max word length.
- There is a log option to view more details on each step.
- It will take any word list file as long as there is a single word on each line and ignores case. The unix words list is provided as are several Moby II project files. The default combines Moby II crossword and crossword delta along with a few inclusions as they are found missing.
- There is an 8 way logic movement function defining valid moves. It populates a dictionary of the board size that contains valid moves.
- This requires python 3.11, and 3rd party modules typer, and rich (and their dependency 3rd party modules).
- Development uses ruff (with almost everything enabled) and pytest though tests have not yet been implemented.
- This should be fully type annotated. It's incredibly helpful with keeping track of what is what.

## Solving Methods

- This creates a dictionary of valid moves from an existing board placement.
- This takes all words that were available (already pruned via min/max length) and further removes any words containing non-playable letters. Letter counts are not factored so the word 'that', with two 't's, would still be in the list even if the board only has one 't'.
- This starts with the first letter of the word and builds lists of possible moves and keeps adding to those moves with each additional letter in the word until the whole word has been proven valid or breaks out of the loop. For 'that', it starts with 't' as a key and creates a list of a list of 't' positions (say spot 14). Then if finds 'h' spot (13) and confirms it is a valid move from 14 so creates a 'th' key with a list of [[14, 13]]. It moves on to 'a' spot (9) which is also valid so creates a 'tha' key containing [[14, 13, 9]]. Finally it finds 't' at 14, but is prevented from adding it since 14 is already in the list so it breaks the loop with the word being unplayable. Lists of lists are used since letters may be on the board in multiple spots so there could be multiple pathways to attempt to make the word.
- This may inadvertently be a form of b-tree or Trie logic. The intent was to follow human thought of building the word from start to finish via available paths.

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

And because programmers are incredibly, stubbornly arrogant to the point they refuse to add this to the pipenv documentation because 'everyone should know how to exit a shell'--even though you use pipenv to create the virtual environment shell and would naturally expect to use a pipenv command to leave it--to exit the virtual environment, just type exit:

```
exit
```


## Future
- Guard print statements from non-existent keys.
- Add word lookup with missing letters
