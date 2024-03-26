"""Various utils function used by `kebbie`."""

import json
import math
import random
import time
import tracemalloc
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import datasets


SEC_TO_NANOSEC = 10e9


def profile_fn(fn: Callable, *args: Any, **kwargs: Any) -> Tuple[Any, int, int]:
    """Profile the runtime and memory usage of the given function.

    Note that it will only account for memory allocated by python (if you use
    a library in C/C++ that does its own allocation, it won't report it).

    Args:
        fn (Callable): Function to profile.
        *args: Positional arguments to pass to the given function.
        **kwargs: Keywords arguments to pass to the given function.

    Returns:
        The return value of the function called.
        The memory usage (in bytes).
        The runtime (in nano seconds).
    """
    tracemalloc.start()
    t0 = time.time()

    result = fn(*args, **kwargs)

    runtime = time.time() - t0
    _, memory = tracemalloc.get_traced_memory()

    return result, memory, runtime * SEC_TO_NANOSEC


def euclidian_dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Function computing the euclidian distance between 2 points.

    Args:
        p1 (Tuple[float, float]): Point 1.
        p2 (Tuple[float, float]): Point 2.

    Returns:
        Euclidian distance between the 2 given points.
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def load_keyboard(lang: str = "en-US") -> Dict:
    """Load the keyboard data for the given language.

    For now, only `en-US` is supported.

    Args:
        lang (str, optional): Language of the keyboard to load.

    Returns:
        The keyboard data.
    """
    layout_folder = Path(__file__).parent / "layouts"
    with open(layout_folder / f"{lang}.json", "r") as f:
        keyboard = json.load(f)
    return keyboard


def strip_accents(s: str) -> str:
    """Util function for removing accents from a given string.

    Args:
        s (str): Accented string.

    Returns:
        Same string, without accent.
    """
    nfkd_form = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def sample(proba: float) -> bool:
    """Simple function to sample an event with the given probability.
    For example, calling `sample(0.95)` will return `True` in 95% cases, and
    `False` in 5% cases.

    Args:
        proba (float): Probability of the event to happen. Should be between 0
            and 1 (included).

    Returns:
        `True` if the event was sampled, `False` otherwise.
    """
    assert 0 <= proba <= 1, f"`{proba}` is not a valid probability (should be between 0 and 1)"
    if proba == 0:
        return False
    elif proba == 1:
        return True
    else:
        return random.choices([True, False], weights=[proba, 1 - proba])[0]


def sample_among(probs: Dict[Any, float], with_none: bool = True) -> Any:
    """Function that sample an event among several with different
    probabilities.

    Args:
        probs (Dict[Any, float]): Dictionary representing the different events
            and their probabilities. Each probability should be above 0 and
            their sum should not exceed 1.
        with_none (bool): If set to `True`, add a `None` option (no event
            sampled).

    Returns:
        The corresponding key of the event sampled.
    """
    options = list(probs.keys())
    weights = list(probs.values())
    assert (
        all(w >= 0 for w in weights) and sum(weights) <= 1
    ), "The numbers given are not a probability (should be above 0 and their sum should not exceed 1)"

    if with_none:
        options.append(None)
        weights.append(1 - sum(weights))

    return random.choices(options, weights=weights)[0]


def sample_partial_word(
    keystrokes: List[Optional[Tuple[float, float]]], word: str, true_word: str
) -> Tuple[List[Optional[Tuple[float, float]]], str]:
    """Sample a partial word from a given word, and extract the corresponding
    keystrokes as well.

    Sampling is done with increasing weights (more chances to sample a longer
    list). For example if the list represent the keystrokes of "abcdef", the
    probabilities are as follow:
     * "a" :     1/15
     * "ab" :    2/15
     * "abc" :   3/15
     * "abcd" :  4/15
     * "abcde" : 5/15

    Args:
        keystrokes (List[Optional[Tuple[float, float]]]): Complete list of
            keystrokes, representing a full word.
        word (str): The word corresponding to the keystrokes.
        true_word (str): Actual word (without typo). Necessary to ensure the
            sampled keystrokes are partial.

    Returns:
        The partial list of keystrokes (sampled from the given word).
        The partial word (sampled from the given word).
    """
    r = range(1, min(len(true_word), len(word)))
    s = random.choices(r, weights=r)[0]
    return keystrokes[:s], word[:s]


def accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
    """Function computing the precision.

    Args:
        tp (int): Number of True Positive.
        tn (int): Number of True Negative.
        fp (int): Number of False Positive.
        fn (int): Number of False Negative.

    Returns:
        Accuracy.
    """
    try:
        return (tp + tn) / (tp + tn + fp + fn)
    except ZeroDivisionError:
        return 0


def precision(tp: int, fp: int) -> float:
    """Function computing the precision.

    Args:
        tp (int): Number of True Positive.
        fp (int): Number of False Positive.

    Returns:
        Precision.
    """
    try:
        return tp / (tp + fp)
    except ZeroDivisionError:
        return 0


def recall(tp: int, fn: int) -> float:
    """Function computing the recall.

    Args:
        tp (int): Number of True Positive.
        fn (int): Number of False Negative.

    Returns:
        Recall.
    """
    try:
        return tp / (tp + fn)
    except ZeroDivisionError:
        return 0


def fbeta(precision: float, recall: float, beta: float = 1) -> float:
    """Function computing the F-beta score (which is a generalization of the
    F1 score).

    The value of Beta changes how much we weight recall versus precision:
     * For beta=0.5, Precision is twice as important as Recall
     * For beta=2, Recall is twice as important as Precision

    Args:
        precision (float): Precision.
        recall (float): Recall.
        beta (float): Beta factor.

    Returns:
        F-beta score.
    """
    try:
        return (1 + beta**2) * precision * recall / (beta**2 * precision + recall)
    except ZeroDivisionError:
        return 0


def round_to_n(x: float, n: int = 2) -> float:
    """Util function to round a given number to n significant digits.

    Args:
        x (float): Number to round.
        n (int): Number of significant digits to use.

    Returns:
        Rounded number.
    """
    return round(x, -int(math.floor(math.log10(x))) + (n - 1)) if x != 0 else 0


def human_readable_memory(x: int) -> str:
    """Given a number in bytes, return a human-readable string of this number,
    with the right unit.

    Args:
        x (int): Number in bytes.

    Returns:
        Human-readable version of the given number, with the right unit.
    """
    x = round_to_n(x, n=3)
    for unit in ["B", "KB", "MB", "GB"]:
        if x < 1000:
            return f"{x} {unit}"

        x /= 1000
    return f"{x} TB"


def human_readable_runtime(x: int) -> str:
    """Given a number in nanoseconds, return a human-readable string of this
    number, with the right unit.

    Args:
        x (int): Number in nanoseconds.

    Returns:
        Human-readable version of the given number, with the right unit.
    """
    x = round_to_n(x, n=3)
    for unit in ["ns", "μs", "ms"]:
        if x < 1000:
            return f"{x} {unit}"

        x /= 1000
    return f"{x} s"


def get_soda_dataset(max_sentences: int = 2_000, seed: int = 31) -> Dict[str, List[str]]:
    """Load the SODA dataset.

    Args:
        max_sentences (int, optional): Maximum number of sentences in total in
            the dataset. They will be shared across domain (50% from the
            `narrative` domain, 50% from the `dialogue` domain).
        seed (int, optional): Seed to use when shuffling the dataset (since we
            don't use the whole dataset, it's better to shuffle it before
            extracting the X first sentences).

    Returns:
        The dataset, separated into two domains : narrative and dialogue.
    """
    data = {"narrative": [], "dialogue": []}
    max_domain_sentences = max_sentences // 2

    hf_dataset = datasets.load_dataset("allenai/soda", split="test")
    hf_dataset = hf_dataset.shuffle(seed=seed)

    for sample in hf_dataset:
        if len(data["narrative"]) >= max_domain_sentences and len(data["dialogue"]) >= max_domain_sentences:
            break

        if len(data["narrative"]) < max_domain_sentences:
            data["narrative"].append(sample["narrative"])

        for sen in sample["dialogue"]:
            if len(data["dialogue"]) < max_domain_sentences:
                data["dialogue"].append(sen)

    return data
