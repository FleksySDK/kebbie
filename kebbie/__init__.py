"""`kebbie` package, which contains the python code to evaluate the NLP
features of a mobile keyboard, as well as a command line to evaluate other
keyboards running in an emulator.
"""

from typing import Dict, List, Optional

from .correctors import Corrector
from .oracle import Oracle
from .scorer import DEFAULT_BETA
from .utils import get_soda_dataset


SUPPORTED_LANG = ["en-US"]
N_MOST_COMMON_MISTAKES = 1000
DEFAULT_SEED = 42


class UnsupportedLanguage(Exception):
    """Custom Exception when the required language is not supported."""

    pass


def evaluate(
    corrector: Corrector,
    lang: str = "en-US",
    custom_keyboard: Dict = None,
    dataset: Dict[str, List[str]] = None,
    track_mistakes: bool = False,
    n_most_common_mistakes: int = N_MOST_COMMON_MISTAKES,
    n_proc: Optional[int] = None,
    seed: int = DEFAULT_SEED,
    beta: float = DEFAULT_BETA,
) -> Dict:
    """Main function of the `kebbie` framework, it evaluates the given
    Corrector.

    Args:
        corrector (Corrector): The corrector to evaluate.
        lang (str, optional): Language to test. For now, only `en-US` is
            supported.
        custom_keyboard (Dict, optional): If provided, instead of relying on
            the keyboard layout provided by default, uses the given keyboard
            layout.
        dataset (Dict[str, List[str]], optional): Data to use for testing. It
            should be a dictionary where the key is the name of the domain, and
            the value is a list of sentences. If `None` is given, it will use
            the SODA dataset.
        track_mistakes (bool, optional): If `True`, we will track the most
            common mistakes of the Corrector (these will be saved as TSV files
            in the working directory).
        n_most_common_mistakes (int, optional): If `track_mistakes` is set to
            `True`, the top X mistakes to record.
        n_proc (int, optional): Number of processes to use. If `None`,
            `os.cpu_count()` is used.
        seed (int): Seed to use for running the tests.
        beta (float, optional): Beta to use for computing the F-beta score.

    Raises:
        UnsupportedLanguage: Exception raised if `lang` is set to a language
            that is not supported yet.

    Returns:
        The results, in a dictionary.
    """
    if lang not in SUPPORTED_LANG and custom_keyboard is None:
        raise UnsupportedLanguage(f"{lang} is not supported yet. List of supported languages : {SUPPORTED_LANG}")

    if dataset is None:
        dataset = get_soda_dataset()

    # Create the Oracle, the class used to create test cases and evaluate the scores
    oracle = Oracle(
        lang,
        dataset,
        custom_keyboard=custom_keyboard,
        track_mistakes=track_mistakes,
        n_most_common_mistakes=n_most_common_mistakes,
        beta=beta,
    )

    # Run the tests & get the results
    results = oracle.test(corrector, n_proc=n_proc, seed=seed)
    return results
