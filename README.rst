========
wlsolver
========

Solve a word list game.

----

Features
________

* This program will solve a word game like squaredle.
* The playable letters need not be in a contiguous rectangle, but the row lengths must match.
* You can specify the minimum and maximum word length to search.
* It will take any word list with a single, case insensitive word per line. One is provided.
* There is an 8 way logic movement defining valid moves.

----

Solving Method
==============

* Create a dictionary of valid moves from the provided playing board.
* Prune the word list by min/max and non-playable letters. (At this stage, duplicate letters have not been removed.)
* Uses b-tree or Trie logic.

Logic Example
-------------
1. Start with the first letter of a word and build a list of possible moves until the word is valid or invalid.
2. For 'that', it starts with 't' as a key and creates a list of a list of 't' positions (e.g. spot 14).
3. Then it finds the 'h' (spot 13) and confirms it is a valid move from spot 14 creating a 'th' key with a list of [14, 13].
4. It moves to an 'a' (spot 9) which is also valid, creating a 'tha' key with [14, 13, 9].
5. Finally, it finds one 't' (spot 14), but is prevented from adding a duplicate spot (14) breaking the loop as an unplayable word.
6. Lists of lists are used  as letters may be on the board in multiple spots with multiple pathways to make a valid word.

----

Execution
=========

Download the project to a local folder, unzip, and cd to the new folder.

Non-Virtual
-----------

This requires having the dependencies (rich, typer, & their respective dependencies) installed system wide.

``python ./src/wlsolver <board>``

Virtual
-------

The easiest way is to use uv to either run the program or create the environment to run the program.

* Execute uv having it auto create a virtual environment on execution.

``uv run wlsolver <board>``

* Or, manually use uv to build the virtual environment, add the dependencies, and then execute with python.

``uv venv``

``source .venv/bin/activate``

``uv sync``

``python ./src/wlsolver <board>``

----

TODO
====
* Create pytest tests for validation.
* Refactor output code to not be disrupted by --log option.
* Refactor code to eliminate writing to global variables.
* Add verbose logging for use with small word lists to output during large iterations.
