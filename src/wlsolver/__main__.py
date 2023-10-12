#!/usr/bin/env python3
"""wlsolver: a cli tool to solve a word list puzzle.

TODO: guard all print statements from key value error if word list doesn't contain words of that length
TODO: support non-square boards
"""

__author__ = 'Brandon Wells'
__email__ = 'b.w.prog@outlook.com'
__copyright__ = '© 2023 Brandon Wells'
__license__ = 'GPL3+'
__status__ = 'Development'
__update__ = '2023.10.11'
__version__ = '0.9.0'


from collections.abc import Callable
from enum import Enum
from math import sqrt
from pathlib import Path
from time import perf_counter
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table
from rich.traceback import install

# constants for tracking program duration and directions strings
PROG_TIME_START: float = perf_counter()
DIRECTIONS: set[str] = {'ri', 'dr', 'do', 'dl', 'le', 'ul', 'up', 'ur'}
BADV: int = 9999


# rich enhancements: console output | install provides traceback | (rp) rich print replaces print()
console = Console()
install()
rp: Callable[..., None] = console.print

# globally available variables -- they may be updated within functions
ver: str = f'wlsolver [green]-[/] {__version__} [green]({__update__})[/]'
global_verb: bool = False
global_board: int = 0
global_min_wl: int = 0
global_max_wl: int = 0
global_l_word: int = 0
global_mov_solve: str = ''
global_default_path = Path('./words/wlsolver_dictionary.txt')
global_let_dict: dict[str, list[int]] = {}
global_move_dict: dict[int, list[int]] = {}


# ~~~ #     - Class for Method Option -
class MethodClass(
        str,
        Enum,
):
    """Choice used by -m/--method Option.

    Parameters
    ----------
    str : _type_
        brute force choice
    Enum : _type_
        optimize choices
    """

    b = 'b'
    o = 'o'


# ~~~ #     - typer callback function -
def callback_version(
        version: bool,
) -> None:
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
        rp(f'\n{ver}\n', highlight=False)
        raise typer.Exit


# ~~~ #     - typer callback function -
def callback_letters(
        letters: str,
) -> str:
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
        value error if letters don't form a square (e.g. 3x3=9)
    """
    # enable global board for updating
    global global_board, global_let_dict                                                                              # noqa: PLW0602

    # create raw letters string by stripping hyphens
    raw: str = ''.join(x for x in letters if x.isalpha())

    # get square root of raw board length as string so we can get specific characters
    raw_sr: str = str(object=sqrt(len(raw)))

    # update global letter dict where key = unique letter in raw with value = each position the letter is in.
    for i, letter in enumerate(iterable=raw):
        if letter in global_let_dict:
            global_let_dict[letter].append(i)
        else:
            global_let_dict[letter] = [i]

    # identify board size and return raw letters or guard against wrong input
    # ending digit should be 0 if board is square (square root)
    match raw_sr[-1]:
        case '0':
            global_board = int(raw_sr[:-2])
        case _:
            rp(Panel(
                f'Invalid letters entry: [blue]{letters}[/]\n'
                'Board must be square (e.g. 3x3=9) entered as such: [blue]xxx-xxx-xxx[/]\n'
                f'Board entered contains [blue]{len(raw)}[/] letters which does not form a square.',
                title='Error',
                title_align='left',
                border_style='red',
                highlight=False,
                ),
            )
            raise typer.Exit from ValueError

    return raw


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
    """
    # enable global longest word for updating
    global global_l_word
    # create the empty return dictionary with the only two str entries
    word_dict: dict[str | int, set[str]] = {
        'full_words': set(),
        'pruned_words': set(),
    }

    # open and read file creating set of all words
    track_full_word_start: float = perf_counter()
    with Path.open(self=words) as f:
        # ensure no new lines and all words are lowercase
        word_dict['full_words'] = {line.strip().lower() for line in f}

    track_full_word_total: float = perf_counter() - track_full_word_start

    # Add sets with word length keys to dict and populate with words
    track_word_sep_start: float = perf_counter()
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

    track_word_sep_total: float = perf_counter() - track_word_sep_start

    # update global longest word
    global_l_word = max(a for a in word_dict if isinstance(a, int)) + 1
    # generate length variables only used for printing to Words Panel
    len_fw: int = len(word_dict['full_words'])
    len_pw: int = len(word_dict['pruned_words'])
    len_min: int = len(word_dict[global_min_wl - 1])
    len_max: int = len(word_dict[global_l_word - 1])
    len_wd: int = len([b for b in word_dict if isinstance(b, int)])

    # print words and pruning to Words Panel
    if global_verb:
        rp(Panel(
            f'Total Word Set from File: [green]{len_fw:,} Words[/] ([green]{track_full_word_total:.4f}[/]s)\n'
            f'Pruned [green]{len_fw - len_pw:,}[/] words (too short/long) and separated by length ([green]'
            f'{track_word_sep_total:.4f}[/]s)\n'
            f'Pruned Word Set: [green]{len_pw:,}[/] ([green]{len_wd}[/] word lengths)\n'
            f'Total Min/Max [green]{global_min_wl}[/]/[green]{global_l_word}[/] Words: ([green]{len_min:,}[/]/[green]'
            f'{len_max:,}[/])',
            title='Words',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    return word_dict


# ~~~ #     - input word list letters function -
def display_letters(
        letters: str,
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
    wl_table = Table(title=f'Word List Table ({global_board}x{global_board})', box=box.HEAVY, show_header=False)
    for _ in range(global_board):
        wl_table.add_column(justify='center', style='green', no_wrap=True)

    for i in range(global_board):
        temp_list: list[str] = list(letters[(i * global_board):((i + 1) * global_board)])
        wl_table.add_row(*temp_list)

    rp(wl_table)

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
    j: int = global_board
    k: int = (j * j) - 1
    # match i to a direction and if valid return digit, otherwise return BADV since board is square and start
    # counting from 0, left row contains digits divisible by board square size allowing this code to work for
    # any square board size smaller than BADV, the arbitrarily chosen invalid direction value. It also guards
    # against below 0 or above max board size.
    match direction:
        case 'ri':
            return BADV if (i + 1) > k or (i + 1) % j == 0 else (i + 1)
        case 'dr':
            return BADV if (i + j + 1) > k or (i + 1) % j == 0 else (i + j + 1)
        case 'do':
            return BADV if (i + j) > k else (i + j)
        case 'dl':
            return BADV if (i + j - 1) > k or (i + j) % j == 0 else (i + j - 1)
        case 'le':
            return BADV if (i - 1) < 0 or (i + j) % j == 0 else (i - 1)
        case 'ul':
            return BADV if (i - j - 1) < 0 or (i + j) % j == 0 else (i - j - 1)
        case 'up':
            return BADV if (i - j) < 0 else (i - j)
        case 'ur':
            return BADV if (i - j + 1) < 0 or (i + 1) % j == 0 else (i - j + 1)
        case _:
            return BADV


# ~~~ #     - global move_dict builder -
def move_dict_builder() -> None:
    """Update the global_move_dict with possible moves from each position.

    The global_move_dict is used by the Optimized function to identify valid moves.
    """
    global global_move_dict
    k: int = (global_board * global_board)
    # pre-populate the dictionary with an integer key for every spot on the board
    global_move_dict = {key: [] for key in range(k)}
    # build all possible 1-step moves using the starting point as key and a list of integers as the valid move options
    # if verbose, show progress bar (doesn't take long but visually shows step)
    for dir_list in track(
        sequence=global_move_dict,
        total=len(global_move_dict),
        disable=(not global_verb),
    ):
        # iterate through the 8 way directions
        for j in DIRECTIONS:
            # get last entry in sub-list and send off with direction to get move digit
            ret_dir: int = valid_mover(i=dir_list, direction=j)
            # guard against bad move with 9999 and unique entry as spaces can only be used once
            match ret_dir != BADV and ret_dir not in global_move_dict[dir_list]:
                case True:
                    # append current top list with unpacked sub list of previous top list's sublist
                    # and add the new valid entry to the end of the sublist
                    global_move_dict[dir_list].append(ret_dir)


# ~~~ #     - brute force direction builder -
def move_builder() -> dict[int, list[list[int]]]:
    """Recursively go through all possible moves on the board building a dictionary.

    This is used by the brute_force function to generate lists of all possible moves.

    Returns
    -------
    dict[int, list[list[int]]]
        key is the length of each entry in the sub list
    """
    k: int = (global_board * global_board)

    # build all possible list in dict
    move_dict: dict[int, list[list[int]]] = {key: [] for key in range(k)}
    # build dict of all possible moves; if verbose, show progress bar
    for md_list in track(
        sequence=move_dict,
        total=len(move_dict),
        disable=(not global_verb),
    ):
        match md_list:
            # first level move, we build initial entry with one item per board tile
            case 0:
                for i in range(k):
                    move_dict[0].append([i])
            # all others from 1 to one less than max word length (count from 0) build off previous
            case v if 1 <= v < global_max_wl:
                # iterate through each sub list in previous built top list
                for ll in move_dict[md_list - 1]:
                    # iterate through the 8 way directions
                    for j in DIRECTIONS:
                        # get last entry in sub-list and send off with direction to get move digit
                        ret_dir: int = valid_mover(i=ll[-1], direction=j)
                        # guard against bad move with 9999 and unique entry as spaces can only be used once
                        match ret_dir != BADV and ret_dir not in ll:
                            case True:
                                # append current top list with unpacked sub list of previous top list's sublist
                                # and add the new valid entry to the end of the sublist
                                move_dict[md_list].append([*ll, ret_dir])

    # sum the total sub-lists of the top lists
    total_moves: int = sum(len(move_dict[i]) for i in move_dict)

    # if verbose, show the Move Panel stats
    if global_verb:
        rp(Panel(
            f'Total Moves Calculated: [green]{total_moves:,}[/]\n'
            f'Valid [green]{global_min_wl}[/] Letter Moves: [green]{len(move_dict[(global_min_wl - 1)]):,}[/]',
            title='Brute Force Move Builder',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    return move_dict


# ~~~ #     - brute force the final word list -
def brute_force(
        a_word_dict: dict[str | int, set[str]],
        letters_dict: dict[str, str],
) -> dict[int, set[str]]:
    """Brute Force method to derive all possible words.

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
    # print different progress if verbose or not
    if global_verb:
        rp('Brute Force: Calculate all possible moves')
    else:
        rp('Working...')
    # generate available moves
    bf_moves: dict[int, list[list[int]]] = move_builder()

    # generate dicts to hold the final return data and the intermediate set
    final_words: dict[int, set[str]] = {}
    int_sets: dict[int, set[str]] = {key: set() for key in range((global_min_wl - 1), global_max_wl)}

    if global_verb:
        rp('Brute Force: Transform moves into possible words')
    # convert the list of integers of possible moves into sets of letters and show progress
    for moves in track(
        sequence=bf_moves,
        total=len(bf_moves),
        disable=(not global_verb),
    ):
        match moves:
            # guard min/max word length
            case v if (global_min_wl - 1) <= v <= global_max_wl:
                # iterate through each sublist
                for ll in bf_moves[moves]:
                    # convert list of int to letters and add to set of word length use of set here eliminates
                    # multiple pathways forming the same word
                    int_sets[v].add(''.join(letters_dict['raw'][i] for i in ll))

    # sum the total possible words and display if verbose
    if global_verb:
        total_p_moves: int = sum(len(int_sets[i]) for i in int_sets)
        rp(Panel(
            f'Total Possible Words: [green]{total_p_moves:,}[/]\n'
            f'Possible [green]{global_min_wl}[/] Letter words: [green]{len(int_sets[global_min_wl - 1]):,}[/]',
            title='Possible Words',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    if global_verb:
        rp('Brute Force: Match real words to possible words')
    # merge & keep like entries in word sets, creating set only if it contains at least one word
    for i_set in track(
        sequence=int_sets,
        total=len(int_sets),
        disable=(not global_verb),
    ):
        if len(x := a_word_dict[i_set] & int_sets[i_set]) > 0:
            final_words[i_set] = x

    # sum the total real words and display if verbose
    if global_verb:
        total_words: int = sum(len(final_words[i]) for i in final_words)
        # guard against key not in dict meaning 0 words
        tmp_fw: int = len(final_words[global_min_wl - 1]) if (global_min_wl - 1) in final_words else 0
        rp(Panel(
            f'Total Real Words: [green]{total_words:,}[/]\n'
            f'Real [green]{global_min_wl}[/] Letter words: [green]{tmp_fw:,}[/]',
            title='Real Words',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    # uncomment following line to view local variables for troubleshooting
    # console.log('optimized function', log_locals=True)

    return final_words


# ~~~ #     - Optimized solver -
def optimized(                                                                          # noqa: C901 PLR0912 PLR0915
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
    # print different progress if verbose or not
    if global_verb:
        rp('Optimized: Trimming Words with invalid letters')
    else:
        rp('Working...')
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
    # iterate through all words discarding any that contain letters not on the game board
    # word_set_key and word_set_value top level in the dictionary: e.g. 3: {bike, ants}
    for w_set_k, w_set_v in track(
        sequence=b_word_dict.items(),
        total=len(b_word_dict),
        disable=(not global_verb),
    ):
        # iterated through all words in the set
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

    # sum the total possible words and display if verbose
    if global_verb:
        total_p_moves: int = sum(len(temp_words[i]) for i in temp_words)
        rp(Panel(
            f'Total Possible Words: [green]{total_p_moves:,}[/]\n'
            f'Possible [green]{global_min_wl}[/] Letter words: [green]{len(temp_words[global_min_wl - 1]):,}[/]',
            title='Possible Words',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    # print different progress if verbose
    if global_verb:
        rp('Optimized: Calculating Valid Words')
    # valid word flag used to guard against an invalid move
    invalid_move: bool = False
    # iterate through all words in the new temp_words dictionary that was pruned of invalid words
    for w_set_k, w_set_v in track(
        sequence=temp_words.items(),
        total=len(temp_words),
        disable=(not global_verb),
    ):
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
                            # break the l_num look if there are no valid moves to continue
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

    # creating set only if it contains at least one word
    for i_set in inter_words:
        if len(inter_words[i_set]) > 0:
            final_words[i_set] = inter_words[i_set]

    # sum the total real words and display if verbose
    if global_verb:
        total_words: int = sum(len(final_words[i]) for i in final_words)
        # guard against key not in dict meaning 0 words
        tmp_fw: int = len(final_words[global_min_wl - 1]) if (global_min_wl - 1) in final_words else 0
        rp(Panel(
            f'Total Real Words: [green]{total_words:,}[/]\n'
            f'Real [green]{global_min_wl}[/] Letter words: [green]{tmp_fw:,}[/]',
            title='Real Words',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    # uncomment following line to view local variables for troubleshooting
    # console.log('optimized function', log_locals=True)

    return final_words


# ~~~ #     - CLI variables are here in main for typer -
def main(                                                                                               # noqa: D103
        letters: Annotated[str, typer.Option(
            ...,
            '--letters',
            '-l',
            prompt=True,
            callback=callback_letters,
            help='Enter the game board rows of letters separated by hyphens. e.g. xxx-xxx-xxx',
        )] = '',
        minimum: Annotated[int, typer.Option(
            '--minimum',
            '-n',
            help='Shortest word length',
        )] = 4,
        maximum: Annotated[int, typer.Option(
            '--maximum',
            '-x',
            help='Longest word length',
        )] = 10,
        method: Annotated[MethodClass, typer.Option(
            '--method',
            '-m',
            case_sensitive=False,
            show_default=False,
            help='solving method: (b)rute force or (o)ptimized [default: o]',
        )] = MethodClass.o,
        words: Annotated[Path, typer.Option(
            '--words',
            '-w',
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help='Word list file to use',
        )] = global_default_path,
        verbose: Annotated[bool, typer.Option(
            '--verbose',
            '-v',
            help='Print calculation details',
        )] = False,
        version: Annotated[Optional[bool] | None, typer.Option(                                         # noqa: UP007
            '--version',
            is_eager=True,
            callback=callback_version,
            help='Print version and exit.',
        )] = None,
) -> None:

    # enable global variable updating
    global global_verb, global_min_wl, global_max_wl, global_mov_solve

    # adjust globals per CLI input
    global_verb = verbose
    # guard against word size less than 2 letters
    global_min_wl = minimum if minimum > 1 else 2
    # guard against impossible word lengths longer than the board
    global_max_wl = maximum if maximum <= (global_board * global_board) else (global_board * global_board)
    global_mov_solve = method

    # Initial output of the program name and version
    rp(f'\n{ver}\n', highlight=False)

    # create dict of valid next moves and update the global_dict_move variable
    move_dict_builder()
    # uncomment to view possible moves
    # rp(global_move_dict)

    # load the list of words
    if global_verb:
        rp(f'Attempting to load: {words}')

    word_dict: dict[str | int, set[str]] = load_words(words=words)

    # display word list letters from user
    letters_dict: dict[str, str] = display_letters(letters=letters)

    # option to pic solving method style; _ is there only for IDE error without
    match method:
        case 'b':
            wl_words: dict[int, set[str]] = brute_force(
                a_word_dict=word_dict,
                letters_dict=letters_dict,
            )
        case 'o':
            wl_words: dict[int, set[str]] = optimized(
                a_word_dict=word_dict,
                letters_dict=letters_dict,
            )
        case _:
            raise typer.Exit from ValueError

    # Generate panels for valid word lengths and print them
    rp('Word Lists')
    for i in wl_words:
        cw: list = []
        # populate colored word list with alternating words being colored blue
        for y, z in enumerate(iterable=sorted(wl_words[i])):
            cw.append(f'[blue]{z}[/]' if y % 3 == 1 else z)

        rp(Panel(
            ', '.join(cw),
            title=f'[bold white]{i + 1}[/] Letter Words: [bold white]{len(cw)}[/]',
            title_align='left',
            border_style='green',
            highlight=False,
            ),
        )

    # exit the app
    prog_time_total: float = perf_counter() - PROG_TIME_START
    rp(Panel(
        f'([green]{prog_time_total:.4f}[/]s)',
        title='[bold white]:glowing_star: Complete :glowing_star:[/]',
        title_align='left',
        border_style='green',
        highlight=False,
        ),
    )
    raise typer.Exit


# ~~~ #
if __name__ == '__main__':

    # use typer to build cli arguments off main variables
    typer.run(function=main)
