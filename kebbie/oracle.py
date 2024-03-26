"""Module defining the `Oracle` class, which is the class taking care of
iterating the dataset, introducing typos using the noise model, and querying
the Corrector to correct these typos. Then the scorer is used to compute
metrics about the performances, and the results are returned.
"""

import hashlib
import multiprocessing as mp
import os
import random
from typing import Callable, Dict, List, Optional, Union

from tqdm import tqdm

from kebbie import Corrector
from kebbie.noise_model import NoiseModel
from kebbie.scorer import Scorer
from kebbie.tokenizer import BasicTokenizer
from kebbie.utils import sample, sample_partial_word


CHUNK_SIZE = 10
MAX_CHAR_PER_SENTENCE = 256
SWIPE_PROB = 0.01  # 1 / 100 is tested with swiping


def init_tester(
    fn: Callable, lang: str, custom_keyboard: Dict, correctors: mp.Queue, seed: int, track_mistakes: bool
) -> None:
    """Function run at process initialization for Tester workers.

    Each worker in a Pool will run this function when created. It will
    instanciate several things needed for testing the given corrector :
     * A Tokenizer to split sentences into words
     * A NoiseModel to introduce typos
     * A Corrector instance, which is the model we want to test

    Args:
        fn (Callable): Main tester function (instanciated objects will be
            attached to this function).
        lang (str): Language used.
        custom_keyboard (Dict, optional): If provided, instead of relying on
            the keyboard layout provided by default, uses the given keyboard
            layout.
        correctors (mp.Queue): Queue containing list of correctors to test.
            Each process will get the next corrector available in queue.
        seed (int): Base seed to use.
        track_mistakes (bool): Set to `True` for tracking the most common
            mistakes.
    """
    fn.tokenizer = BasicTokenizer()
    fn.noisy = NoiseModel(lang, custom_keyboard=custom_keyboard)
    fn.corrector = correctors.get()
    fn.base_seed = seed
    fn.track_mistakes = track_mistakes


def tester(sentence: str) -> Scorer:
    """Function to test a given sentence.

    It uses the noise model to introduce typos word by word, run the
    Corrector on various tasks (auto-completion, auto-correction, next-word
    prediction), and score the results.

    Args:
        sentence (str): Sentence to use as data for the test.

    Returns:
        Scorer class with the prediction counts for this sentence.
    """
    # Set the seed for reproducibility, using the hash of the sentence
    hsh = int(hashlib.sha256(sentence.encode("utf-8")).hexdigest(), 16)
    random.seed(tester.base_seed + hsh)
    rnd_state = random.getstate()

    # Tokenize the sentence into words
    sentence = tester.tokenizer.preprocess(sentence)
    words = tester.tokenizer.word_split(sentence)

    context = ""
    # Keep track for predictions counts with a local scorer, for this sentence
    scorer = Scorer(domains=[None], track_mistakes=tester.track_mistakes)
    while words and len(context) < MAX_CHAR_PER_SENTENCE:
        # Before randomly generating typo, set the random state for determinism
        random.setstate(rnd_state)

        # It's slow to generate swipe gesture every sentence, so run it just sometimes
        word_to_swipe = words[0]
        swipe_gesture = tester.noisy.swipe(word_to_swipe) if sample(SWIPE_PROB) else None

        # Generate noisy keystrokes for the next word(s)
        keystrokes, typed_word, n_word_typed, typos = tester.noisy.type_till_space(words)

        # Get the clean word(s), update the remaining words to type and get the next word
        actual_word = " ".join(words[:n_word_typed])
        words = words[n_word_typed:]
        next_word = words[0] if len(words) > 0 else None

        # We are done with generating typo, save the random state for the next iteration
        rnd_state = random.getstate()

        if swipe_gesture:
            # Call the swipe model
            preds, memory, runtime = tester.corrector.profiled_resolve_swipe(context, swipe_gesture)
            scorer.swp(word_to_swipe, preds, context=context, memory=memory, runtime=runtime)

        # Call the model for auto-completion (for long enough words)
        if len(typed_word) > 1 and len(actual_word) > 1:
            partial_keystrokes, partial_word = sample_partial_word(keystrokes, typed_word, actual_word)
            preds, memory, runtime = tester.corrector.profiled_auto_complete(context, partial_keystrokes, partial_word)
            scorer.acp(actual_word, preds, partial_word=partial_word, context=context, memory=memory, runtime=runtime)

        # Call the model for auto-correction
        preds, memory, runtime = tester.corrector.profiled_auto_correct(context, keystrokes, typed_word)
        scorer.acr(
            actual_word, preds, typed_word=typed_word, context=context, typos=typos, memory=memory, runtime=runtime
        )

        # Update the context for the next iteration (input forcing)
        context = tester.tokenizer.update_context(context, actual_word)

        # Call the model for next-word prediction
        if next_word:
            preds, memory, runtime = tester.corrector.profiled_predict_next_word(context)
            scorer.nwp(next_word, preds, context=context, memory=memory, runtime=runtime)

    return scorer


class Oracle:
    """Class that takes care of testing a Corrector. It basically gets clean
    text data, adds noise to it, send the noisy data to the Corrector, and
    scores its output.

    This class spawn multiple processes to decrease runtime.

    Args:
        lang (str): Language used.
        test_data (Dict[str, List[str]]): List of clean sentences for each
            domain.
        custom_keyboard (Dict): If provided, instead of relying on
            the keyboard layout provided by default, uses the given keyboard
            layout.
        track_mistakes (bool): Set to `True` for tracking the most
            common mistakes. Most common mistakes are added to the results
            dictionary.
        n_most_common_mistakes (int): If `track_mistakes` is set to
            `True`, the top X mistakes to record.
        beta (float): Beta to use for computing the F-beta score.
    """

    def __init__(
        self,
        lang: str,
        test_data: Dict[str, List[str]],
        custom_keyboard: Dict,
        track_mistakes: bool,
        n_most_common_mistakes: int,
        beta: float,
    ) -> None:
        super().__init__()

        self.lang = lang
        self.data = test_data
        self.custom_keyboard = custom_keyboard
        self.track_mistakes = track_mistakes
        self.n_most_common_mistakes = n_most_common_mistakes
        self.beta = beta

    def test(self, corrector: Union[Corrector, List[Corrector]], n_proc: Optional[int], seed: int) -> Dict:
        """Main method, it tests the given Corrector, and returns results as a
        dictionary.

        This method spawn multiple processes to decrease runtime.

        Args:
            corrector (Union[Corrector, List[Corrector]]): Corrector to test.
                If a list of Corrector is given, the argument `n_proc` is
                ignored, and one corrector is assigned for each process.
            n_proc (Optional[int]): Number of processes to use. If `None`,
                `os.cpu_count()` is used.
            seed (int): Seed to use for running the tests.

        Returns:
            Results formatted in a dictionary.
        """
        # Initialize a global Scorer here, that will gather counts across processes
        scorer = Scorer(domains=self.data.keys(), track_mistakes=self.track_mistakes)

        # For multiprocessing
        n_proc = n_proc if n_proc is not None else os.cpu_count()
        d_size = sum(len(d) for d in self.data.values())

        # Create the corrector for each process
        proc_correctors = mp.Queue()
        if isinstance(corrector, Corrector):
            for _ in range(n_proc):
                proc_correctors.put(corrector)
        else:
            # If we already have a list of correctors, assign one for each process
            n_proc = len(corrector)
            for c in corrector:
                proc_correctors.put(c)

        with mp.Pool(
            processes=n_proc,
            initializer=init_tester,
            initargs=(tester, self.lang, self.custom_keyboard, proc_correctors, seed, self.track_mistakes),
        ) as pool, tqdm(total=d_size) as pbar:
            # Test data is made of several domain, where each domain contains a list of sentences
            for domain, sentence_list in self.data.items():
                chunk_size = max(min(CHUNK_SIZE, len(sentence_list) // n_proc), 1)
                for scr in pool.imap_unordered(tester, sentence_list, chunksize=chunk_size):
                    scr.set_domain(domain)
                    scorer.add(scr)
                    pbar.update(1)

        # Retrieve the results
        results = scorer.score(beta=self.beta)

        # Then potentially add the most common mistakes
        if self.track_mistakes:
            mistakes = {}
            for task in ["nwp", "acp", "acr"]:
                task_name = {"nwp": "next_word_prediction", "acp": "auto_completion", "acr": "auto_correction"}[task]

                m_count = getattr(scorer, f"{task}_mistakes")

                mistakes[task_name] = [("Count", "Expected", "Predictions", "Context")]
                for m, c in m_count.most_common(self.n_most_common_mistakes):
                    mistakes[task_name].append((c, m.actual, f"[{', '.join(m.preds)}]", m.context))

            results["most_common_mistakes"] = mistakes

        return results
