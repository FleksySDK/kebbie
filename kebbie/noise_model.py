"""Module defining the `NoiseModel` class, which takes care of introducing
typos in a clean text (and later see if the model can properly correct these
typos).
"""

import json
import os
import random
import string
from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, Tuple

import regex as re
import requests

from kebbie.gesture import make_swipe_gesture
from kebbie.layout import LayoutHelper
from kebbie.utils import sample, sample_among, strip_accents


class Typo(Enum):
    """Enum listing all possible typos that can be introduced."""

    # Deletions
    DELETE_SPELLING_SYMBOL = "DELETE_SPELLING_SYMBOL"
    DELETE_SPACE = "DELETE_SPACE"
    DELETE_PUNCTUATION = "DELETE_PUNCTUATION"
    DELETE_CHAR = "DELETE_CHAR"

    # Additions
    ADD_SPELLING_SYMBOL = "ADD_SPELLING_SYMBOL"
    ADD_SPACE = "ADD_SPACE"
    ADD_PUNCTUATION = "ADD_PUNCTUATION"
    ADD_CHAR = "ADD_CHAR"

    # Substitutions
    SUBSTITUTE_CHAR = "SUBSTITUTE_CHAR"

    # Simplifications
    SIMPLIFY_ACCENT = "SIMPLIFY_ACCENT"
    SIMPLIFY_CASE = "SIMPLIFY_CASE"

    # Transposition
    TRANSPOSE_CHAR = "TRANSPOSE_CHAR"

    # Common typos
    COMMON_TYPO = "COMMON_TYPO"


DEFAULT_TYPO_PROBS = {
    # Sampled on every characters (except the last one)
    Typo.TRANSPOSE_CHAR: 0.01,
    # Sampled on spelling symbols
    Typo.DELETE_SPELLING_SYMBOL: 0.1,
    Typo.ADD_SPELLING_SYMBOL: 0,
    # Sampled on spaces
    Typo.DELETE_SPACE: 0.01,
    Typo.ADD_SPACE: 0,
    # Sampled on punctuations
    Typo.DELETE_PUNCTUATION: 0,
    Typo.ADD_PUNCTUATION: 0,
    # Sampled on regular characters
    Typo.DELETE_CHAR: 0.005,
    Typo.ADD_CHAR: 0.005,
    # Sampled on accented letters
    Typo.SIMPLIFY_ACCENT: 0.08,
    # Sampled on uppercase letters
    Typo.SIMPLIFY_CASE: 0.08,
    # Sampled once per word
    Typo.COMMON_TYPO: 0.05,
}
SPACE = " "
DELETIONS = [Typo.DELETE_SPELLING_SYMBOL, Typo.DELETE_SPACE, Typo.DELETE_PUNCTUATION, Typo.DELETE_CHAR]
FRONT_DELETION_MULTIPLIER = 0.36  # Reduce probability of a front deletion
DEFAULT_SIGMA_RATIO = 3  # Equivalent of 99% typing the right letter (1% chance of a typo)
CACHE_DIR = os.path.expanduser("~/.cache/common_typos/")
TWEET_TYPO_CORPUS_URL = "https://luululu.com/tweet/typo-corpus-r1.txt"


class NoiseModel:
    """Class responsible for introducing typo in a clean text.

    Most of typos are introduced on text directly. Then fuzzy typing is
    applied, using two Gaussian distributions (for x-axis and y-axis),
    mimicking a user typing on a soft keyboard.

    The ratio arguments are here to choose how wide the Gaussian distribution
    is. A wider distribution will be less precise, a narrower distribution will
    be more precise. To test how wide a ratio is, run the following code :
    ```
    from scipy.stats import norm

    def compute(x):
        cdf = norm.cdf(x)
        return cdf - (1 - cdf)

    print(compute(2.32))    # >>> 0.9796591226625606
    ```
    So in this case, a ratio of `2.32` gives a precision of ~98% (a typo will
    be introduced in 2% of the cases).

    Args:
        lang (str): Language used.
        custom_keyboard (Dict, optional): If provided, instead of relying on
            the keyboard layout provided by default, uses the given keyboard
            layout.
        common_typos (Optional[Dict[str, List[str]]], optional): Dictionary of
            common typos. If `None`, common typos are not used.
        typo_probs (Optional[Dict[str, float]], optional): Probabilities for
            each type of typos. If `None` is given, `DEFAULT_TYPO_PROBS` is
            used.
        x_offset (float, optional): Parameter for the Gaussian distribution for
            the fuzzy typing. Base position offset on the x-axis.
        y_offset (float, optional): Parameter for the Gaussian distribution for
            the fuzzy typing. Base position offset on the y-axis.
        x_ratio (float, optional): Parameter for the Gaussian distribution for
            the fuzzy typing. It controls how wide the distribution is on the
            x-axis, which is the precision of the typing.
        y_ratio (float, optional): Parameter for the Gaussian distribution for
            the fuzzy typing. It controls how wide the distribution is on the
            y-axis, which is the precision of the typing.
    """

    def __init__(
        self,
        lang: str,
        custom_keyboard: Dict = None,
        common_typos: Optional[Dict[str, List[str]]] = None,
        typo_probs: Optional[Dict[str, float]] = None,
        x_offset: float = 0,
        y_offset: float = 0,
        x_ratio: float = DEFAULT_SIGMA_RATIO,
        y_ratio: float = DEFAULT_SIGMA_RATIO,
    ):
        self.lang = lang
        self.x_offset, self.y_offset = x_offset, y_offset
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.klayout = LayoutHelper(self.lang, custom_keyboard=custom_keyboard, ignore_layers_after=3)
        self.probs = typo_probs if typo_probs is not None else DEFAULT_TYPO_PROBS
        self.common_typos = common_typos if common_typos is not None else self._get_common_typos()

    def type_till_space(
        self,
        words: List[str],
    ) -> Tuple[
        List[Optional[Tuple[float, float]]],
        str,
        int,
        List[Typo],
    ]:
        """Method introducing typos word by word.

        This method receives a list of words, and type these words while
        introducing typos.
        So most of the time, only one word will be typed and the method will
        return. In some cases, the space is mistyped or deleted, so two words
        are typed.

        Args:
            words (List[str]): List of words to type.

        Returns:
            List of keystrokes (may contains some None).
            The typed characters as string.
            The number of words typed.
            The list of typos introduced in the string typed.
        """
        all_keystrokes = []
        all_typed_char = ""
        all_typos = []

        for i, word in enumerate(words):
            # Some words can't be corrected (numbers, symbols, etc...) -> Don't introduce typos
            error_free = False if self._is_correctable(word) else True

            # Add typos in the word
            noisy_word, typos = self._introduce_typos(word, error_free=error_free)
            all_typos += typos

            # Type the word (fuzzy)
            keystrokes, typed_char, typos = self._fuzzy_type(noisy_word, error_free=error_free)
            all_keystrokes += keystrokes
            all_typed_char += typed_char
            all_typos += typos

            # Then, we try to type a space (separator between words)
            # TODO : Modify this part for languages without space
            noisy_space, sp_typo_1 = self._introduce_typos(SPACE)
            keystrokes, typed_char, sp_typo_2 = self._fuzzy_type(noisy_space)

            # If the space is correctly typed, return now, otherwise type the next word
            if not sp_typo_1 and not sp_typo_2:
                break
            else:
                all_keystrokes += keystrokes
                all_typed_char += typed_char
                all_typos += sp_typo_1 + sp_typo_2

        return all_keystrokes, all_typed_char, i + 1, all_typos

    def swipe(self, word: str) -> Optional[List[Tuple[float, float]]]:
        """Method for creating an artificial swipe gesture given a word.

        Args:
            word (str): Word to type with a swipe gesture.

        Returns:
            Positions (x, y) of the generated swipe gesture, or None if the
                swipe gesture couldn't be created.
        """
        # Some words can't be corrected (numbers, symbols, etc...) -> Don't introduce typos
        error_free = False if self._is_correctable(word) else True

        # Get the core keystrokes (fuzzy)
        keystrokes, *_ = self._fuzzy_type(word, error_free=error_free)

        # If we can swipe that word, create the corresponding artificial gesture
        if all(keystrokes) and len(keystrokes) > 1:
            return make_swipe_gesture(keystrokes)
        else:
            return None

    def _introduce_typos(self, word: str, error_free: bool = False) -> Tuple[str, List[Typo]]:  # noqa: C901
        """Method to introduce typos in a given string.

        Either the word is changed into an existing common typo, or the word is
        processed as a stream of characters, each character having a chance of
        being mistyped.
        This method only add regular typos (deletions, additions, etc...), and
        is not introducing fuzzy typing.

        Args:
            word (str): Clean string where to add typos.
            error_free (bool): If set to True, don't introduce typo. Defaults
                to False.

        Returns:
            The noisy string.
            The list of typos introduced.
        """
        if error_free:
            return word, []

        # First of all, we either consider the word as a unit and introduce a
        # language-specific common typo (if available), or treat the word as a
        # sequence of character, where each character can have a typo
        if word in self.common_typos and sample(self.probs[Typo.COMMON_TYPO]):
            # Introduce a common typo
            return random.choice(self.common_typos[word]), [Typo.COMMON_TYPO]

        # From here, treat the word as a stream of characters, and potentially
        # add typos for each character
        noisy_word = ""
        typos = []
        word_chars = list(word)
        for i, char in enumerate(word_chars):
            # First, potentially apply simplifications (removing accent, or
            # lowercasing an uppercase character)
            # Note that if the full word is uppercase, we don't apply lowercase
            # simplification (doesn't feel like a natural typo a user would do)
            if char in self.klayout.letter_accents and sample(self.probs[Typo.SIMPLIFY_ACCENT]):
                char = strip_accents(char)
                typos.append(Typo.SIMPLIFY_ACCENT)
            if char.isupper() and len(word) > 1 and not word.isupper() and sample(self.probs[Typo.SIMPLIFY_CASE]):
                char = char.lower()
                typos.append(Typo.SIMPLIFY_CASE)

            # Check if this character exists on our keyboard
            try:
                *_, klayer_id = self.klayout.get_key_info(char)
                char_is_on_kb = True
                char_is_on_default_kb = klayer_id == 0
            except KeyError:
                char_is_on_kb = char_is_on_default_kb = False

            # Then, add the possible typo depending on the character type
            events = []
            is_first_char = bool(i == 0)
            is_last_char = bool(i >= (len(word_chars) - 1))
            if char.isnumeric() or not char_is_on_kb:
                # Don't introduce typos for numbers or symbols that are not on keyboard
                pass
            else:
                if not is_last_char:
                    # Only transpose char if they are on the same keyboard layer
                    try:
                        *_, next_char_klayer_id = self.klayout.get_key_info(word[i + 1])
                    except KeyError:
                        next_char_klayer_id = None

                    if klayer_id == next_char_klayer_id:
                        events.append(Typo.TRANSPOSE_CHAR)
                if char in self.klayout.spelling_symbols:
                    events.append(Typo.DELETE_SPELLING_SYMBOL)
                    events.append(Typo.ADD_SPELLING_SYMBOL)
                elif char.isspace():
                    events.append(Typo.DELETE_SPACE)
                    events.append(Typo.ADD_SPACE)
                elif char in string.punctuation:
                    events.append(Typo.DELETE_PUNCTUATION)
                    events.append(Typo.ADD_PUNCTUATION)
                elif char_is_on_default_kb:
                    events.append(Typo.DELETE_CHAR)
                    events.append(Typo.ADD_CHAR)

            # If it's the last character (and we are not typing a space),
            # don't add deletions typos, because it's an auto-completion case,
            # not auto-correction
            if is_last_char and word != SPACE:
                events = [e for e in events if e not in DELETIONS]

            # Get the probabilities for these possible events
            typo_probs = {e: self.probs[e] for e in events}
            if is_first_char:
                # Deleting the first character of the word is not so common, update the probabilities accordingly
                typo_probs = {e: p * FRONT_DELETION_MULTIPLIER if e in DELETIONS else p for e, p in typo_probs.items()}

            # And sample one of them
            typo = sample_among(typo_probs)

            # Process the typo
            if typo is Typo.TRANSPOSE_CHAR:
                noisy_char = word_chars[i + 1]
                word_chars[i + 1] = char
            elif typo in [Typo.DELETE_SPELLING_SYMBOL, Typo.DELETE_SPACE, Typo.DELETE_PUNCTUATION, Typo.DELETE_CHAR]:
                noisy_char = ""
            elif typo in [Typo.ADD_SPELLING_SYMBOL, Typo.ADD_SPACE, Typo.ADD_PUNCTUATION, Typo.ADD_CHAR]:
                noisy_char = f"{char}{char}"
            else:  # No typo
                noisy_char = char

            noisy_word += noisy_char
            if typo is not None:
                typos.append(typo)

        return noisy_word, typos

    def _fuzzy_type(
        self, word: str, error_free: bool = False
    ) -> Tuple[List[Optional[Tuple[float, float]]], str, List[Typo]]:
        """Method adding fuzzy typing.

        This method takes a string (potentially already noisy from other type
        of typos), and fuzzy-type it : simulate a user on a soft-keyboard.
        This "fat-finger syndrom" is simulated using two Gaussian
        distributions, one for each axis (x, y).
        This method also returns the generated keystrokes (positions on the
        keyboard), but only for the default keyboard (ID = 0). Keystrokes from
        other keyboard are set to None.

        Args:
            word (str): String to fuzzy-type.
            error_free (bool): If set to True, don't introduce typo. Defaults
                to False.

        Returns:
            List of keystrokes.
            Fuzzy string (corresponding to the keystrokes).
            List of typos introduced.
        """
        fuzzy_word = ""
        keystrokes = []
        typos = []

        # Type word character by character
        for char in word:
            try:
                width, height, x_center, y_center, klayer_id = self.klayout.get_key_info(char)
            except KeyError:
                # This character doesn't exist on the current keyboard
                # Just type it without introducing typo, like if the user copy-pasted it
                keystrokes.append(None)
                fuzzy_word += char
                continue

            # Sample a keystroke for this character
            # Note that we don't generate typos for characters outside of the default keyboard
            if error_free or klayer_id != 0:
                keystroke = (x_center, y_center)
            else:
                # Compute mu and sigma for the Normal distribution
                x_mu = x_center + self.x_offset
                y_mu = y_center + self.y_offset
                x_sigma = (width / 2) / self.x_ratio
                y_sigma = (height / 2) / self.y_ratio

                # Sample a position (x and y)
                keystroke = (random.gauss(x_mu, x_sigma), random.gauss(y_mu, y_sigma))

            # Convert it back to a character, to see where we tapped
            fuzzy_char = self.klayout.get_key(keystroke, klayer_id)

            # Save it (save the keystroke only if part of the default keyboard)
            keystrokes.append(keystroke if klayer_id == 0 else None)
            fuzzy_word += fuzzy_char
            if fuzzy_char != char:
                typos.append(Typo.SUBSTITUTE_CHAR)

        return keystrokes, fuzzy_word, typos

    def _is_correctable(self, word: str) -> bool:
        """Method returning True if we expect the given word to be corrected
        upon typo introduction, False otherwise.

        This is necessary to ensure we don't introduce typos in words that
        can't be corrected, because if we do, it will be counted as error.

        For now, are considered non-correctable :
         * Words that don't contains any letter (from Unicode standard)

        Args:
            word (str): Word to classify as correctable or not.

        Returns:
            True if the word is correctable (and therefore we can introduce
            typo), False otherwise.
        """
        # Use the Unicode category `L` (see https://en.wikipedia.org/wiki/Unicode_character_property#General_Category)
        return not bool(re.match(r"^[^\pL]+$", word))

    def _get_common_typos(self) -> Dict[str, List[str]]:
        """Retrieve the list (if it exists) of plausible common typos to use
        when introducing typos.

        Returns:
            Dictionary where the keys are the correct words and the values are
                the associated possible typos for this word.
        """
        plang = self.lang.split("-")[0]
        common_typos_cache_file = os.path.join(CACHE_DIR, f"{plang}.json")

        # Try to access the cached common typos, and if it fails, it means we
        # don't have it locally
        try:
            with open(common_typos_cache_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            pass

        # File is not cached, download & process the common typos from online
        os.makedirs(os.path.dirname(common_typos_cache_file), exist_ok=True)
        typos = defaultdict(list)
        if plang == "en":
            response = requests.get(TWEET_TYPO_CORPUS_URL)
            for line in response.text.strip().split("\n"):
                typoed_word, correct_word, *_ = line.split("\t")
                typos[correct_word].append(typoed_word)
        else:
            return {}

        # Save the retrieved typos in cache
        with open(common_typos_cache_file, "w") as f:
            json.dump(typos, f, indent=4)

        return typos
