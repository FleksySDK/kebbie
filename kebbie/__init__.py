"""`kebbie` package, which contains the python code to evaluate the NLP
features of a mobile keyboard, as well as a command line to evaluate other
keyboards running in an emulator.
"""
from typing import Dict, List

from .correctors import Corrector
from .oracle import N_MOST_COMMON_MISTAKES, Oracle
from .utils import get_soda_dataset


SUPPORTED_LANG = ["en-US"]


class UnsupportedLanguage(Exception):
    """Custom Exception when the required language is not supported."""

    pass


def evaluate(
    corrector: Corrector,
    lang: str = "en-US",
    dataset: Dict[str, List[str]] = None,
    track_mistakes: bool = False,
    n_most_common_mistakes: int = N_MOST_COMMON_MISTAKES,
) -> Dict:
    """Main function of the `kebbie` framework, it evaluates the given
    Corrector.

    Args:
        lang (str, optional): Language to test. For now, only `en-US` is
            supported. Defaults to `en-US`.
        corrector (Corrector): The corrector to evaluate.
        dataset (Dict[str, List[str]], optional): Data to use for testing. It
            should be a dictionary where the key is the name of the domain, and
            the value is a list of sentences. If `None` is given, it will use
            the SODA dataset. Defaults to `None`.
        track_mistakes (bool, optional): If `True`, we will track the most
            common mistakes of the Corrector (these will be saved as TSV files
            in the working directory). Defaults to `False`.
        n_most_common_mistakes (int, optional): If `track_mistakes` is set to
            `True`, the top X mistakes to record. Defaults to
            N_MOST_COMMON_MISTAKES.

    Raises:
        UnsupportedLanguage: Exception raised if `lang` is set to a language
            that is not supported yet.

    Returns:
        Dict: The results, in a dictionary.
    """
    if lang not in SUPPORTED_LANG:
        raise UnsupportedLanguage(f"{lang} is not supported yet. List of supported languages : {SUPPORTED_LANG}")

    if dataset is None:
        dataset = get_soda_dataset()

    # Create the Oracle, the class used to create test cases and evaluate the scores
    oracle = Oracle(lang, dataset, track_mistakes=track_mistakes)
    n_proc = None  # Use multiprocessing by default

    # Run the tests & get the results
    results = oracle.test(corrector, n_proc=n_proc)
    return results
