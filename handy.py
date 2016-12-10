"""
Password creation based on a template specification.

The concept of the hand of a character or word is based on how it is typed. If
a word is typed only with the left hand it is left handed, and words typed 
only with the right hand are right handed. Words typed by alternating hands
each character (right-left-right-left-...) are called even handed. All other
words are called mixed handed. Characters are right or left handed based on
which hand types them. Note that even handed words are easier to type and tend
to result in less errors.

The mappings that are provided here map from letters to numbers or symbols.
They can be used to convert words to numbers and/or symbols, to make the 
passwords using those words to be more secure.

Password specifications use the following character encodings:

    W/w: Word letter
    N/n: Word letter as number
    S/s: Word letter as symbol
    A/a: Upper/lower non-word letter
    L: Random case non-word letter
    #: Number
    $: Symbol
    =: Switch to even handed
    <: Switch to left handed
    >: Switch to right handed
    @: Switch to any handed
    ;: No character (stop a word)
    .: Any character. 

The word letter characters come in upper and lower case. The number of upper
case letters indicates the minimum word length, and the number of upper and 
lower case letters indicates the maximum word length. So 'WWWWWwww' indicates
a word with five to eight letters.

Constants:
CHARS: Individual characters classified by hand/type. (dict of str: str)
PHONE: Mapping based on telephone keys. (dict of str: str)
MOD10: Mapping based on modulus base 10. (dict of str: str)
VERTICAL: Mapping based on QWERTY keyboard. (dict of str: str)

Functions:
check_hand: Check the hand settings during processing. (bool, str, str)
force_char: Force one or more characters to be a specific type. (str)
get_pass: Generate a random password from a specification. (str)
get_word: Choose a random word based on current word specification. (str)
handed: Determines handedness of a word when touch typed. (str)
load_words: Loads and classifies the words from a file. (dict of str: list)
next_char: Determine the next character in the password. (str)
"""

import random

# Individual characters classified by hand/type.
CHARS = {}
# left handed characters (qwerty)
CHARS['left-lower'] = 'qwertasdfgzxcvb'
CHARS['left-upper'] = CHARS['left-lower'].upper()
CHARS['left-letter'] = CHARS['left-lower'] + CHARS['left-upper']
CHARS['left-number'] = '12345'
CHARS['left-symbol'] = '!@#$%'
CHARS['left-all'] = CHARS['left-letter'] + CHARS['left-number'] + CHARS['left-symbol']
# right handed characters (qwerty)
CHARS['right-lower'] = 'yuiophjklnm'
CHARS['right-upper'] = CHARS['right-lower'].upper()
CHARS['right-letter'] = CHARS['right-lower'] + CHARS['right-upper']
CHARS['right-number'] = '67890'
CHARS['right-symbol'] = '^&*()'
CHARS['right-all'] = CHARS['right-letter'] + CHARS['right-number'] + CHARS['right-symbol']
# any handed characters
for partial_key in ('lower', 'upper', 'letter', 'number', 'symbol', 'all'):
    CHARS['any-' + partial_key] = CHARS['left-' + partial_key] + CHARS['right-' + partial_key]
# mappings
NUM_SYM = dict(zip('1234567890', '!@#$%^&*()'))
# Mapping based on modulus base 10.
MOD10 = {'to-number': {}, 'to-symbol': {}}
for char_index, char in enumerate("abcdefghijklmnopqrstuvwxyz"):
    char_index += 1
    MOD10['to-number'] = str(char_index % 10)
    MOD10['to-symbol'] = NUM_SYM[str(char_index % 10)]
# Mapping based on telephone keys.
PHONE = {'to-number': dict(zip("abcdefghijklmnopqrstuvwxyz", '22233344455566677778889999'))}
PHONE['to-symbol'] = dict(zip("abcdefghijklmnopqrstuvwxyz", '@@@###$$$%%%^^^&&&&***(((('))
# Mapping based on QWERTY keyboard.
VERT_BASE = {'zaq': '1', 'xsw': '2', 'cde': '3', 'vfr': '4', 'bgt': '5', 'nhy': '6', 'mju': '7',
    'ki': '8', 'lo': '9', 'p': '0'}
VERTICAL = {'to-number': {}, 'to-symbol': {}}
for key in VERT_BASE:
    for char in key:
        VERTICAL['to-number'][char] = VERT_BASE[key]
        VERTICAL['to-symbol'][char] = NUM_SYM[VERT_BASE[key]]
# clean up
del NUM_SYM
del VERT_BASE

def check_hand(spec, even, hand, next_hand):
    """
    Check for changes to the hand settings during processing. (bool, str, str)
    
    Parameters:
    spec: The current character for the password specification. (str)
    even: A flag for even handed processing. (bool)
    hand: The current hand setting. (str)
    next_hand: The next hand setting for even handed processing. (str)
    """
    # check for specification based changes
    if spec == '=':
        even = True
        hand = 'left'
        next_hand = 'right'
        if random.random() < 0.5:
            hand, next_hand = next_hand, hand
    elif spec == '<':
        hand = 'left'
        even = False
    elif spec == '>':
        hand = 'right'
        even = False
    elif spec == '@':
        even = False
        hand = 'any'
    # if even handed, swap hands each character
    if even:
        hand, next_hand = next_hand, hand
    # return updated settings
    return even, hand, next_hand

def force_char(password, indexes, mapping, any_char):
    """
    Force one or more characters to be a specific type. (str)

    Users are warned of the original password before changes are made, in case
    the original password contained dictionary words to aid memorization.

    Parameters:
    password: The password to force characters in. (str)
    indexes: The indexes of the characters to force. (list of int)
    mapping: The characters to change letters into. (dict of str: str)
    any_char: The list of charactors to change to. (str)
    """
    # warn user of original password 
    if indexes:
        print('Password before forcing characters:', password)
    # force characters one at a time
    for index in indexes:
        # don't force past the end of the password
        if index >= len(password):
            continue
        if password[index] in mapping:
            # change by mapping if possible
            char = mapping[password[index]]
        else:
            # otherwise use random character
            char = random.choice(any_char)
        # update password
        password = password[:index] + char + password[index + 1:]
    return password
    
def get_pass(spec, words, chars = CHARS, mapping = MOD10, to_number = [], to_symbol = [], trunc = 0):
    """
    Generate a random password from a specification. (str)

    See the module level documentation for details on the password 
    specification.

    Parameters:
    spec: The password specification. (str)
    words: The categorized available words. (dict of str: list)
    chars: The categorized available characters. (dict of str: str)
    mapping: A mapping of letters to numbers/symbols. (dict of str: str)
    to_number: A list of indexes that must be numbers. (list of int)
    to_symbol: A list of indexes that must be symbols. (list of int)
    trunc: The maximum characters to randomly remove from the end. (int)
    """
    # make sure terminal words get added
    if spec[-1] in 'WwNnSs':
        spec += ';'
    # set up the loop
    local_number, local_symbol = [], []
    hand, next_hand = 'any', ''
    even = False
    word_min, word_max = 0, 0
    password = ''
    # loop through the specification
    for char in spec:
        # update word length
        if char in 'WNS':
            word_min += 1
            word_max += 1
        elif char in 'wns':
            word_max += 1
        else:
            # get new word at end of word specification
            if word_min:
                password += get_word(words, word_min, word_max, even, hand)
                # reset tracking variables
                word_min, word_max = 0, 0
                if even and password[-1] in chars[hand + '-all']:
                    hand, next_hand = next_hand, hand
                # remove excess indexes
                local_number = [index for index in local_number if index < len(password)]
                local_symbol = [index for index in local_symbol if index < len(password)]
            # add the next character
            password += next_char(char, chars, hand)
            # update hand side tracking
            even, hand, next_hand = check_hand(char, even, hand, next_hand)
        # update forced character tracking
        password_length = len(password) + word_max
        if char in 'Nn':
            local_number.append(password_length - 1)
        elif char in 'Ss':
            local_symbol.append(password_length - 1)
    # force characters
    local_number.extend(to_number)
    password = force_char(password, local_number, mapping['to-number'], chars['any-number'])
    local_symbol.extend(to_symbol)
    password = force_char(password, local_symbol, mapping['to-symbol'], chars['any-symbol'])
    # truncate password if requested
    if trunc:
        trunc = random.randrange(trunc + 1)
        if trunc:
            password = password[:-trunc]
    return password

def get_word(words, word_min, word_max, even, hand):
    """
    Choose a random word based on current word specification. (str)
    
    The randomness is in the choice of word, not in the choice of word length.
    That means that the distribution of word lengths will be weighted by the
    length of available words.
    
    Words are returned in title case.
    
    Parameters:
    words: The available words in categories. (dict of str: list of str)
    word_min: The shortest allowed word length. (int)
    word_max: The longest allowed word length. (int)
    even: Flag for even handed processing. (bool)
    hand: The current hand to used characters for. (str)
    """
    # check for even handed words.
    if even:
        word_key = 'even'
    else:
        word_key = hand
    # get the valid words
    valid_words = [word for word in words[word_key] 
        if word_min <= len(word) <= word_max]
    # return one at random.
    return random.choice(valid_words).title()

def handed(word):
    """
    Determines handedness of a word when touch typed. (str)
    
    Returns 'left' or 'right' for words typed all with one hand, 'even' for words
    typed with alternating hands for each letter, and 'mixed' for all other 
    words. Determines hand based on the contents of the global variable
    CHARS['right-all'].
    
    Parameters:
    word: A string with the word to be checked. (str)
    """
    # get handedness of each character
    coded = [char in CHARS['right-all'] for char in word]
    # no rights is a left
    if sum(coded) == 0:
        return 'left'
    # all rights is a right
    elif sum(coded) == len(coded):
        return 'right'
    else:
        # all even pairs is an even
        pairs = [coded[ndx - 1] != coded[ndx] for ndx in range(1, len(coded))]
        if sum(pairs) == len(pairs):
            return 'even'
        else:
            # otherwise it's mixed
            return 'mixed'

def load_words(word_file):
    """
    Loads and classifies the words from a file. (dcit of str: list of str)
    
    The file is assumed to have one word per line. The output dictionary has 
    the following keys: left, right, even, mixed, and any. All of the words are
    put in 'any', and in one of the other four based on the hands used to type
    the word.
    
    Parameters:
    word_file: the file, or path to the file, with the words. (file or str)
    """
    # convert strings to files
    if isinstance(word_file, str):
        word_file = open(word_file)
    # set up output dictionary
    words = {'left': [], 'right': [], 'even': [], 'mixed': [], 'any': []}
    # load and categorize the words
    for word in word_file:
        word = word.strip()
        words[handed(word)].append(word)
        words['any'].append(word)
    return words

def next_char(spec, chars, hand):
    """
    Determine the next character in the password. (str)
    
    Parameters:
    spec: The character from the password specification. (str)
    chars: The characters available to use. (dict of str: str)
    hand: The hand to use characters for. (str)
    """
    if spec == '#':
        char = random.choice(chars[hand + '-number'])
    elif spec == '$':
        char = random.choice(chars[hand + '-symbol'])
    elif spec == 'A':
        char = random.choice(chars[hand + '-upper'])
    elif spec == 'a':
        char = random.choice(chars[hand + '-lower'])
    elif spec == 'L':
        char = random.choice(chars[hand + '-letter'])
    elif spec == '.':
        char = random.choice(chars[hand + '-all'])
    else:
        char = ''
    return char
    
if __name__ == '__main__':
    word_path = '/home/craig/Documents/Passwords/2of12.txt'
    words = load_words(word_path)
    specs = ['WWWWWwww$##', '=WWWWWwww$##', '<WWWWWwww$##', '>WWWWWwww$##', 'NNNN', '.' * 8, 'AaLAaL']
    specs += ['<WWWWWwww>$##', '.' * 30, 'WWWW;SNNN;WWWW', 'L#.....L', '>LLLLL<LLLLL=LLLLL@LLLLLLL']
    specs += ['WWWWnnnnn$$$', 'WWWWsssss###']
    for spec in specs:
        print(spec, get_pass(spec, words))
    print('Gibber 12-30', get_pass('.' * 30, words, trunc = 18))
    print('Pre-force 4th & 5th', get_pass('L' * 8, words, to_number = [3], to_symbol = [4]))
    print('Pre-force after word', get_pass('WWWwwwwwwAAAAAAA', words, to_number = [8]))
