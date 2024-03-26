"""Module defining `BasicTokenizer`, very basic tokenizer to separate a
sentence into words.
"""

import re
from typing import List


class BasicTokenizer:
    """A basic tokenizer, used for regular latin languages.
    This tokenizer simply use space as word separator. Since it is used for
    testing only, we don't need to care about punctuations, etc...
    """

    def preprocess(self, sentence: str) -> str:
        """Method for simple preprocessing.

        The goal of this function is not to provide an extensive and clean
        preprocessing. The goal is just to normalize some characters (that
        are not in our keyboard, so the user can't officially type them) into
        their normal counterpart, that are in the keyboard.

        Args:
            sentence (str): String to normalize.

        Returns:
            Normalized string.
        """
        # Replace things that are like "
        sentence = sentence.replace("“", '"').replace("”", '"').replace("„", '"')

        # Replace things that are like '
        sentence = sentence.replace("’", "'").replace("ʻ", "'").replace("‘", "'").replace("´", "'").replace("ʼ", "'")

        # Replace things that are like -
        sentence = sentence.replace("–", "-").replace("—", "-").replace("‑", "-").replace("−", "-").replace("ー", "-")

        # Replace other punctuations
        sentence = sentence.replace("…", "...").replace("‚", ",").replace("․", ".")

        # TODO: Each keyboard has its own way to deal with punctuation
        # (applying auto-correction or not, displaying next-word prediction or
        # not, etc...). So for now we just get rid of the punctuations, it's a
        # convenient shortcut and it's fair to all keyboards.
        # Eventually we should find a better way to deal with that.
        sentence = re.sub(r"\s*\.+\s*", " ", sentence)
        sentence = re.sub(r"\s*[,:;\(\)\"!?\[\]\{\}~]\s*", " ", sentence)

        return sentence

    def word_split(self, sentence: str) -> List[str]:
        """Method for splitting a sentence into a list of words.

        Args:
            sentence (str): Sentence to split.

        Returns:
            List of words from the sentence.
        """
        return sentence.strip().split()

    def update_context(self, context: str, word: str) -> str:
        """Method for updating a context, given a word that was typed.

        Args:
            context (str): Existing context.
            word (str): Word being typed.

        Returns:
            Updated context.
        """
        return context + word + " "
