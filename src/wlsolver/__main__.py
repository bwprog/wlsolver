#!/usr/bin/env python3
"""wlsolver: a cli tool to solve a word list puzzle."""

from collections.abc import Callable
from os import R_OK, access
from pathlib import Path
from time import perf_counter
from typing import Annotated

import typer
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install

from wlsolver import __about__

# constants for tracking program duration, cardinal directions, and a bad value (value doesn't matter as long as
# it is an unmatchable integer).
PROG_TIME_START: float = perf_counter()
DIRECTIONS: set[str] = {'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'}
BADV: int = 9999

# rich traceback, console output, log output, and typer app initialization
install()
con = Console()
log = Console(quiet=True)
app: Callable[..., None] = typer.Typer(
    rich_markup_mode='rich',
    add_completion=False,
)
# help examples shown at the bottom of the --help output
board_epilog: str = (
    'Examples:\n\n'
    'wlsolver [violet]tguy-idcq-mngb-pore[/]               -> A standard 4x4 grid: top row "tguy", sec row "idcq", '
    'etc.\n\n'
    'wlsolver [violet]2yo-ovin-mmew-aosd-2or[/]            -> A board with unplayable blanks: top row "__yo", sec row '
    '"ovin", etc.'
)
# globally available variables -- they may be updated within functions
ver: str = f'wlsolver [green]-[/] {__about__.__version__} [green]({__about__.__update__})[/]'
# the playable game board
global_board: dict[str, int] = {'rows': 0, 'columns': 0}
# minimum word length
global_min_wl: int = 0
# maximum word length
global_max_wl: int = 0
# longest possible word
global_l_word: int = 0
# default word list path
global_words_path = Path('./words/wlsolver_dictionary.txt')
# dictionary of unique letters on the playable board
global_let_dict: dict[str, list[int]] = {}
# dictionary of all valid moves from each board position
global_move_dict: dict[int, list[int]] = {}


# ~~~ #     - typer callback function -
def callback_version(version: bool) -> None:
    """Print version and exit.

    Parameters
    ----------
    version : bool
        CLI option -v/--version to print program version

    Raises
    ------
    typer.Exit
        normal cleanup and exit after completing request
    """
    if version:
        con.print(f'\n{ver}\n', highlight=False)
        raise typer.Exit


# ~~~ #     - typer callback function -
def validate_letters(letters: str) -> tuple[str, list[list[str]]]:
    """Validate input letters and strip out the hyphens.

    Parameters
    ----------
    letters : str
        CLI option -l/--letters of all letters on the board

    Returns
    -------
    str
        letters stripped of hyphens

    Raises
    ------
    typer.Exit
        value error if letters don't form a rectangle (e.g. 3x3=9, 4x3=12)
    """
    # enable global board and letter dictionaries for updating
    global global_board, global_let_dict  # noqa: PLW0602
    log.print(f'Enter: [blue]validate_letters[/] - Imported:\n[purple]{global_board = }[/]'
              f'\n[purple]{global_let_dict =}[/]')

    # create raw letters string by stripping hyphens
    rows_raw: list[str] = letters.split(sep='-')
    log.print(f'Init: [purple]{rows_raw = }[/]')
    rows_full: list[list[str]] = []
    log.print(f'Init: [purple]{rows_full = }[/]')
    raw: str = ''
    for i, row in enumerate(iterable=rows_raw):
        rows_full.append([])
        for x in row:
            log.print(f'Iteration: [purple]{x = }[/] | [purple]{row = }[/]')
            if x.isalpha():
                raw = f'{raw}{x}'
                rows_full[i].append(x)
            if x.isnumeric():
                raw = f'{raw}{" " * int(x)}'
                rows_full[i].extend(list(' ' * int(x)))
    log.print(f'Complete: [purple]{rows_full = }[/]')

    # validate rows of equal lengths
    first_row_len: int = len(rows_full[0])
    log.print(f'Init: [purple]{first_row_len = }[/]')
    for row in rows_full:
        log.print(f'Iteration: [purple]{row = } | [blue]{len(row) = }[/] | [blue]{first_row_len = }[/]')
        if len(row) != first_row_len:
            con.print(Panel(
                f'Invalid letters entry: [blue]{letters}[/]\n'
                'Board must be rectangular (e.g. 3x3=9, 4x3=12) entered as such: [blue]xxx-xxx-xxx[/]\n'
                f'Board entered contains [blue]{len(raw)}[/] letters which does not form a square.',
                title='Error',
                title_align='left',
                border_style='red',
                highlight=False,
                ),
            )
            raise typer.Exit from ValueError

    # update global letter dict where key = unique letter in raw with value = each position the letter is in.
    for i, letter in enumerate(iterable=raw):
        if letter in global_let_dict:
            global_let_dict[letter].append(i)
            log.print(f'Iteration: [blue]{i =}[/] | [purple]{letter = }[/] - [red]In Dict[/]: [green]Appended[/]')
        else:
            global_let_dict[letter] = [i]
            log.print(f'Iteration: [blue]{i =}[/] | [purple]{letter = }[/] - [red]Not In Dict[/]: [green]Added[/]')

    # Update the global_board with valid rows and columns
    global_board['rows'] = len(rows_full)
    global_board['columns'] = first_row_len
    log.print(f'Modified: [purple]{global_board = }[/]')

    log.print(f'Exit: [blue]validate_letters[/] | return\n[purple]{raw =}[/]\n[purple]{rows_full =}[/]')
    return raw, rows_full


# ~~~ #     - loading words from file function -
def load_words(
        words: Path,
) -> dict[str | int, set[str]]:
    """Load words from the file, print details, and return words dict.

    Parameters
    ----------
    words : Path
        location of the file containing the list of words

    Returns
    -------
    dict[str | int, set[str]]
        strs are full_words and pruned_words; ints are word lengths

    Raises
    ------
    typer.Exit
        value error if words file does not exist or is unreadable
    """
    global global_l_word
    log.print(f'Enter: [blue]load_words[/] - Imported:\n[purple]{global_l_word = }[/]')

    word_dict: dict[str | int, set[str]] = {
        'full_words': set(),
        'pruned_words': set(),
    }
    log.print(f'Init: [purple]{word_dict = }[/]')
    if words.is_file() and access(words, R_OK):
        log.print(f'Validation: {words =} is valid and readable')
        with Path.open(self=words) as f:
            # ensure no new lines and all words are lowercase
            word_dict['full_words'] = {line.strip().lower() for line in f}
            log.print(f'[purple]{words = }[/] loaded | [purple]{len(word_dict['full_words']) = }[/]')
    else:
        reason: str = 'is unreadable' if words.is_file() else 'does not exist'
        con.print(Panel(
            f'Word List Location: [blue]{words}[/]\nFile {reason}',
            title='Error',
            title_align='left',
            border_style='red',
            highlight=False,
            ),
        )
        raise typer.Exit from ValueError

    # ~~ Build valid word lists ~~
    log.print('Creating word lists by length.')
    for word in word_dict['full_words']:
        # using the standard count from 0 so subtracting 1 from word length to keep standard
        wl: int = len(word) - 1
        # to be added to pruned and word length sets, word must be within min/max values
        match wl in word_dict and global_min_wl <= (wl + 1) <= global_max_wl:
            case True:
                word_dict[wl].add(word)
                word_dict['pruned_words'].add(word)
            case _:
                # must again match min/max word length as previous match was false
                match global_min_wl <= (wl + 1) <= global_max_wl:
                    case True:
                        word_dict[wl] = {word}
                        word_dict['pruned_words'].add(word)
    log.print('Word List Keys and Value Lengths')
    if not log.quiet:
        for k, v in word_dict.items():
            log.print(f'Iteration: [purple]{k = }[/]: [blue]{len(v) = }[/]')

    # ~~ update global longest word ~~
    global_l_word = max(a for a in word_dict if isinstance(a, int)) + 1
    log.print(f'Exit: [blue]load_words[/] | Longest word: {global_l_word = } | Return word_dict')

    return word_dict


# ~~~ #     - input word list letters function -
def display_letters(
        letters: str,
        rows_full: list[list[str]],
) -> dict[str, str]:
    """Display a Word List Table and return a dict of the letters.

    Parameters
    ----------
    letters : str
        The raw letters as provided via -l/--letters CLI

    Returns
    -------
    dict[str, str]
        raw = letters; raw_len = total number of letters; unique = unique letters
    """
    # Display word list block as table
    wl_table = Table(box=box.ROUNDED, show_header=False, show_lines=True)
    for _ in range(global_board['columns']):
        wl_table.add_column(justify='center', style='green', no_wrap=True)

    for row in rows_full:
        wl_table.add_row(*row)

    con.print(wl_table)

    # build and return dict of raw letters and length
    return {
        'raw': letters,
        'raw_len': str(object=len(letters)),
        'unique': str(object=len(set(letters))),
    }


# ~~~ #     - valid movement function -
def valid_mover(
        i: int,
        direction: str,
) -> int:
    """Establish if a move is Valid.

    Submit a starting digit and direction. This returns  9999 if the move is invalid, otherwise it returns the valid
    digit of the move.

    Parameters
    ----------
    i : int
        the starting point digit on the board (e.g. 0-2,3-5,6-8 on 3x3=9 board)
    direction : str
        8 way direction code

    Returns
    -------
    int
        9999 if bad move, otherwise the valid digit the move landed on
    """
    # create j (board square size), and k (full board size -1 due to start from 0 counting)
    j: int = global_board['columns']
    k: int = (j * j) - 1
    # match i to a direction and if valid return digit, otherwise return BADV since board is rectangular and start
    # counting from 0, left row contains digits divisible by board size allowing this code to work for
    # any rectangular board size smaller than BADV (9999), the arbitrarily chosen invalid direction value. It also
    # guards against below 0 or above max board size.
    match direction:
        case 'e':
            return BADV if (i + 1) > k or (i + 1) % j == 0 else (i + 1)
        case 'se':
            return BADV if (i + j + 1) > k or (i + 1) % j == 0 else (i + j + 1)
        case 's':
            return BADV if (i + j) > k else (i + j)
        case 'sw':
            return BADV if (i + j - 1) > k or (i + j) % j == 0 else (i + j - 1)
        case 'w':
            return BADV if (i - 1) < 0 or (i + j) % j == 0 else (i - 1)
        case 'nw':
            return BADV if (i - j - 1) < 0 or (i + j) % j == 0 else (i - j - 1)
        case 'n':
            return BADV if (i - j) < 0 else (i - j)
        case 'ne':
            return BADV if (i - j + 1) < 0 or (i + 1) % j == 0 else (i - j + 1)
        case _:
            return BADV


# ~~~ #     - global move_dict builder -
def move_dict_builder() -> None:
    """Update the global_move_dict with possible moves from each position.

    The global_move_dict uses the valid_mover function and is used by the optimized function to identify valid moves.
    """
    global global_move_dict
    log.print('Enter: [blue]move_dict_builder][/] - Imported global_move_dict')

    k: int = (global_board['columns'] * global_board['rows'])
    # pre-populate the dictionary with an integer key for every spot on the board
    global_move_dict = {key: [] for key in range(k)}
    # build all possible 1-step moves using the starting point as key and a list of integers as the valid move options
    for dir_list in global_move_dict:
        # iterate through the 8 way cardinal directions
        for j in DIRECTIONS:
            # get last entry in sub-list and send off with direction to get move digit
            ret_dir: int = valid_mover(i=dir_list, direction=j)
            # guard against bad move with 9999 and unique entry as spaces can only be used once
            match ret_dir != BADV and ret_dir not in global_move_dict[dir_list]:
                case True:
                    # append current top list with unpacked sub list of previous top list's sublist
                    # and add the new valid entry to the end of the sublist
                    global_move_dict[dir_list].append(ret_dir)
    log.print(f'Exit: [blue]move_dict_builder[/] - {len(global_move_dict) = }')


# ~~~ #     - Optimized solver -
def optimized(
        a_word_dict: dict[str | int, set[str]],
        letters_dict: dict[str, str],
) -> dict[int, set[str]]:
    """Calculate valid words by pruning and then following letters down valid paths.

    Parameters
    ----------
    a_word_dict : dict[str  |  int, set[str]]
        contains all real words
    letters_dict : dict[str, str]
        contains the letters on the board

    Returns
    -------
    dict[int, set[str]]
        contains all playable words using word length as key
    """
    log.print('Enter: [blue]optimized[/]')
    raw: str = letters_dict['raw']

    # generate dicts to hold the final and intermediate return data, pre-building intermediate with all possible keys
    final_words: dict[int, set[str]] = {}
    inter_words: dict[int, set[str]] = {key: set() for key in range((global_min_wl - 1), global_max_wl)}

    # get a dict of all words using word length in int as keys
    b_word_dict: dict = {k: v for k, v in a_word_dict.items() if isinstance(k, int)}
    # flag used to mark words for exclusion
    invalid_word: bool = False
    # intermediate dict that only contains possible words
    temp_words: dict[int, list[str]] = {}

    # ~~ Prune words with letters not in play on board ~~
    # iterate through all words discarding any that contain letters not on the game board
    # w_set_k and w_set_v top level in the dictionary: e.g. 3: {bike, ants}
    log.print('Iterate through initial pruned words (length) pruning words that have letters not on the board.')
    for w_set_k, w_set_v in b_word_dict.items():
        # iterate through all words in the set
        for word in w_set_v:
            # iterate through each letter of the word
            for w_let in word:
                # as soon as a letter is not in the board (raw), set the invalid_word flag and break the lowest loop
                if w_let not in raw:
                    invalid_word = True
                    break
            # guard for the key existing in the dictionary and ensure the word is valid
            if w_set_k in temp_words and not invalid_word:
                temp_words[w_set_k].append(word)
            # here we create the initial key (an int of the word length) if the word is valid
            elif not invalid_word:
                temp_words[w_set_k] = [word]
            # reset the invalid word flag for use on next word
            invalid_word = False
    if not log.quiet:
        for k, v in temp_words.items():
            log.print(f'Iteration: [purple]{k = }[/]: [blue]{len(v) = }[/]')

    # ~~ Build final dict of valid words ~~
    # valid word flag used to guard against an invalid move
    invalid_move: bool = False
    log.print('Iterate through final pruned words dict building the final word list.')
    # iterate through all words in the new temp_words dictionary that was pruned of invalid words
    for w_set_k, w_set_v in temp_words.items():
        # word level loop
        for word in w_set_v:
            # intermediate dict builds up the word with list of lists of valid moves: word: hat; board has 2 h, 2 a, 1 t
            # loops build up keys like this: key h: [[0], [13]], key ha: [[0, 4], [13, 12]], key hat: [[0, 4, 5]]
            int_words: dict[str, list[list[int]]] = {}
            # w = letter position, w_let = letter; this loops through all letters in the word
            for w, w_let in enumerate(iterable=word):
                # no guard as temp_Words must contain valid letters, can just copy global letter position list
                if w == 0:
                    int_words[w_let] = [[x] for x in global_let_dict[w_let]]
                # guard against key not being created due to invalid letter
                elif not invalid_move:
                    # loop through the previously created lower-level list to check all possible paths to a valid word
                    # if w = 2 and w_let = t and word hat, next lowest would be ha so loop through ha key
                    for i_lst in int_words[word[:w]]:
                        # loop through all possible positions for the current letter (e.g. t if building hat)
                        for l_num in global_let_dict[word[w]]:
                            # create the new list unpacking previous to be added if checks prove valid (e.g. *[0, 4], 5)
                            b: list[int] = [*i_lst, l_num]
                            # guard valid move, key exists, and letter position not already used
                            # (e.g. don't use same t twice in that)
                            if (l_num in global_move_dict[i_lst[-1]]
                                and word[:w + 1] in int_words
                                and l_num not in i_lst
                            ):
                                int_words[word[:w + 1]].append(b)
                            # guard valid move, and letter position not already used -- create key
                            elif (l_num in global_move_dict[i_lst[-1]]
                                and l_num not in i_lst
                            ):
                                int_words[word[:w + 1]] = [b]
                            # allow loop to continue if not all positions of current letter have been tried
                            elif l_num != global_let_dict[word[w]][-1]:
                                continue
                            # break the l_num loop if there are no valid moves to continue
                            else:
                                break
                        # guard if last entry in previous list was tried and if the new letter was not added
                        # (no valid moves), set the invalid flag value and break the loop
                        if i_lst == int_words[word[:w]][-1] and word[:w + 1] not in int_words:
                            invalid_move = True
                            break
                # only run when invalid_move triggers, reset invalid_move and break the current word loop
                else:
                    invalid_move = False
                    break
            # guard against invalid_move if previous loop had exhausted on last letter preventing else from running
            invalid_move = False

            # before moving to next word, add the word to the intermediate dict set if it was fully built with at least
            # one valid move from start to end
            if word in int_words:
                inter_words[w_set_k].add(word)

    # adding set to output dict only if it contains at least one word
    final_words.update({k: v for k, v in inter_words.items() if len(v) > 0})

    if not log.quiet:
        for k, v in final_words.items():
            log.print(f'Iteration: [blue]{k =}[/]: [blue]{len(v) =}[/]')
    log.print(f'Exit: [blue]optimized[/] - return final_words - {len(final_words) = }')
    return final_words


# ~~~ #     - CLI variables are here in board for typer -
@app.command(epilog=board_epilog)
def board(
        letters: Annotated[str, typer.Argument(
            rich_help_panel='[red]letters',
            help=('Enter rows of [violet]LETTERS[/] separated by hyphens; use a whole number to indicate the number '
                'of blank, unplayable spaces before the next letter.'),
        )],
        flag_log: Annotated[bool, typer.Option(
            '--log',
            help='Print a [blue]LOG[/] of steps taken; only useful for troubleshooting or learning.',
        )] = False,
        flag_minimum: Annotated[int, typer.Option(
            '--minimum',
            '-n',
            help='[orange1]MINIMUM[/] word length',
        )] = 4,
        flag_maximum: Annotated[int, typer.Option(
            '--maximum',
            '-x',
            help='[orange1]MAXIMUM[/] word length',
        )] = 16,
        flag_words: Annotated[Path, typer.Option(
            '--words',
            '-w',
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help='Word list [yellow]FILE[/] to use',
        )] = global_words_path,
        flag_version: Annotated[bool | None, typer.Option(
            default='--version',
            is_eager=True,
            callback=callback_version,
            help='Print version and exit',
        )] = None,
) -> None:
    """Entry point for wlsolver."""
    # ~~ enable logging if requested; import global variables for updating ~~
    log.quiet = not flag_log
    global global_min_wl, global_max_wl

    log.print(f'Initialize log.\nEnter: [blue]board[/] - Imported:\n[purple]{global_min_wl = }[/]'
              f'\n[purple]{global_max_wl =}[/]')

    # ~~ letter validation and processing ~~
    raw_letters: str = ''
    rows_full: list[list[str]] = []
    raw_letters, rows_full = validate_letters(letters=letters)
    # guard against word size less than 2 letters
    global_min_wl = flag_minimum if flag_minimum > 1 else 2
    # guard against impossible word lengths longer than the board
    global_max_wl = (
        min(flag_maximum, global_board['columns'] * global_board['rows'])
    )

    # ~~ initial output of the program name and version ~~
    con.print(f'\n{ver}\n', highlight=False)

    # ~~ calculate valid moves and update the global_move_dict ~~
    move_dict_builder()

    word_dict: dict[str | int, set[str]] = load_words(words=flag_words)

    # display word list letters from user
    letters_dict: dict[str, str] = display_letters(letters=raw_letters, rows_full=rows_full)

    # option to pic solving method style; _ is there only for IDE error without
    wl_words: dict[int, set[str]] = optimized(
        a_word_dict=word_dict,
        letters_dict=letters_dict,
    )

    # ~~ Generate panels for valid word lengths and print them ~~
    word_panels: list[Panel] = []
    con.print('Word Lists')
    total_words: int = 0
    for key, value in wl_words.items():
        cw: list = []
        # populate colored word list with alternating words being colored blue
        for y, z in enumerate(iterable=sorted(value)):
            cw.append(f'[blue]{z}[/]' if y % 3 == 1 else z)

        len_cw: int = len(cw)
        total_words += len_cw
        word_panels.append(Panel(
            renderable=', '.join(cw),
            title=f'[blue]{key + 1}[/] [default]Letter Words:[/] [orange1]{len_cw}[/]',
            title_align='left',
            border_style='green',
            highlight=False,
            expand=False,
            ),
        )
    columns: Columns = Columns(renderables=word_panels, padding=(1, 1), width=40)
    con.print(columns)

    prog_time_total: float = perf_counter() - PROG_TIME_START
    duration_output: str = (f'[blue]{prog_time_total:,.2f}[/] s' if prog_time_total >= 1 else
                            f'[blue]{(prog_time_total * 1000):,.2f}[/] ms')
    con.print(Panel(
        f'{duration_output}',
        title=f'[default]Found[/] [orange1]{total_words}[/] [default]words in[/]',
        title_align='left',
        border_style='blue',
        highlight=False,
        expand=False,
        ),
    )


# ~~~ #
if __name__ == '__main__':

    app()
