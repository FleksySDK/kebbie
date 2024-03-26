"""Module implementing `Scorer`, a class that keep track of how many errors
the model is making, and output various corresponding metrics.
"""

from __future__ import annotations

import statistics as stats
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import partial
from typing import Dict, List, Optional

from kebbie.noise_model import Typo
from kebbie.utils import accuracy, fbeta, human_readable_memory, human_readable_runtime, precision, recall, round_to_n


DEFAULT_BETA = 0.9
WITH_TYPO = "with_typo"
WITHOUT_TYPO = "without_typo"


@dataclass
class Count:
    """Structure representing the most basic counts for a task.

    It counts :
    * Number of correct predictions
    * Number of top3-correct predictions
    * Total number of predictions
    """

    correct: int = 0  # Number of times the first prediction was correct
    correct_3: int = 0  # Number of times one of the top-3 predictions was correct
    total: int = 0  # Total number of predictions

    def __add__(self, count: Count) -> Count:
        """Merge two `Count` instance by adding their counts.

        Args:
            count (Count): Count instance to add.

        Returns:
            Merged Count.
        """
        return Count(
            correct=self.correct + count.correct,
            correct_3=self.correct_3 + count.correct_3,
            total=self.total + count.total,
        )

    def __mul__(self, proportion: float) -> Count:
        """Multiply the current `Count` instance by a given proportion.

        Args:
            proportion (float): Proportion to multiply by.

        Returns:
            Count with the right proportion.
        """
        return Count(
            correct=round(self.correct * proportion),
            correct_3=round(self.correct_3 * proportion),
            total=round(self.total * proportion),
        )


@dataclass(eq=True, frozen=True)
class Mistake:
    """Structure representing a mistake (including the context of the mistake,
    the expected word and the predictions).
    """

    actual: str = field(compare=True)
    preds: List[str] = field(compare=False)
    context: str = field(compare=False)


def dd_x_layers(n_layers: int = 1) -> defaultdict:
    """Helper function for creating a nested defaultdict, with a specified
    number of nest level. The end object is a Count.

    Args:
        n_layers (int): Number of layer for the defaultdict.

    Returns:
        Created nested defaultdict.
    """
    assert n_layers > 0, f"A default dict have at least 1 layer ({n_layers} given)"
    if n_layers == 1:
        return defaultdict(Count)
    else:
        return defaultdict(partial(dd_x_layers, n_layers=n_layers - 1))


def one_score(results: Dict) -> float:
    """One Score to rule them all, One Score to find them, One Score to bring
    them all and in the darkness bind them.

    This function is here to gather the various testing metrics of a JET file
    in a single number, to easily compare models.

    We take a single metric for each task, and weight them based on the
    importance of the task (these metrics already have the same scale : between
    0 and 1).

    For NWP and ACP we take a top-3 metric, because these tasks usually involve
    a user action from a proposed list. For ACR and SWP, we take a top-1
    metric, since usually it's automatically applied without user input.

    Args:
        results (Dict): Testing results. Should be a dictionary containing all
            the metrics (used to compute the one score).

    Returns:
        One score, computed from the results given.
    """
    nwp = results["next_word_prediction"]["score"]["top3_accuracy"]
    acp = results["auto_completion"]["score"]["top3_accuracy"]
    acr = results["auto_correction"]["score"]["fscore"]
    swp = results["swipe_resolution"]["score"]["accuracy"]

    return 0.15 * nwp + 0.2 * acp + 0.4 * acr + 0.25 * swp


class Scorer:
    """Class keeping track of the predictions and how correct they are, but
    also computing the associated score for each task after the end of test.

    Args:
        domains (List[str]): The list of domains in the dataset. The Scorer
            keeps track of the score for each domain, so that we can spot
            discrepancies between domain, if any.
        human_readable (bool, optional): If set to `False`, performance metrics
            (memory, runtime) are kept in their raw, numeral form. If set to
            `True`, these are converted to a human readable string.
        track_mistakes (bool, optional): Set to `True` for tracking the most
            common mistakes.
    """

    def __init__(self, domains: List[str], human_readable: bool = True, track_mistakes: bool = False) -> None:
        self.human_readable = human_readable

        # For each task, create a dictionary of Counts
        # Each task has a different structure :

        # Next-word prediction : [domain] -> counts
        self.nwp_c = dd_x_layers(1)

        # Autocompletion : [domain] -> [typo/no_typo] -> [word_completion_rate] -> counts
        self.acp_c = dd_x_layers(3)

        # Autocorrection : [domain] -> [typo type/number of typo] -> counts
        self.acr_c = dd_x_layers(2)

        # Swipe resolution : [domain] -> counts
        self.swp_c = dd_x_layers(1)

        # Make sure we track each domain (create a 0-Count for each domain)
        for d in domains:
            _ = self.nwp_c[d], self.acp_c[d][WITH_TYPO][0], self.acr_c[d][None], self.swp_c[d]

        # Also keep track of memories & runtimes
        self.nwp_memories = []
        self.acp_memories = []
        self.acr_memories = []
        self.swp_memories = []
        self.nwp_runtimes = []
        self.acp_runtimes = []
        self.acr_runtimes = []
        self.swp_runtimes = []

        # Optionally track common mistakes
        self.track_mistakes = track_mistakes
        self.nwp_mistakes = Counter()
        self.acp_mistakes = Counter()
        self.acr_mistakes = Counter()
        self.swp_mistakes = Counter()

    def add(self, scorer) -> None:
        """Method to update the current Scorer with the counts from another
        Scorer.

        Args:
            scorer (Scorer): Scorer to add.
        """

        def update(d1, d2):
            for k in d2:
                if isinstance(d2[k], Count):
                    d1[k] += d2[k]
                else:
                    update(d1[k], d2[k])

        update(self.nwp_c, scorer.nwp_c)
        update(self.acp_c, scorer.acp_c)
        update(self.acr_c, scorer.acr_c)
        update(self.swp_c, scorer.swp_c)
        self.nwp_memories.extend(scorer.nwp_memories)
        self.acp_memories.extend(scorer.acp_memories)
        self.acr_memories.extend(scorer.acr_memories)
        self.swp_memories.extend(scorer.swp_memories)
        self.nwp_runtimes.extend(scorer.nwp_runtimes)
        self.acp_runtimes.extend(scorer.acp_runtimes)
        self.acr_runtimes.extend(scorer.acr_runtimes)
        self.swp_runtimes.extend(scorer.swp_runtimes)
        self.nwp_mistakes.update(scorer.nwp_mistakes)
        self.acp_mistakes.update(scorer.acp_mistakes)
        self.acr_mistakes.update(scorer.acr_mistakes)
        self.swp_mistakes.update(scorer.swp_mistakes)

    def nwp(
        self,
        true_word: str,
        predicted_words: List[str],
        context: str,
        memory: int,
        runtime: int,
        domain: Optional[str] = None,
    ) -> None:
        """Method used to record a prediction for the next-word prediction
        task.

        Args:
            true_word (str): The label (clean word to predict).
            predicted_words (List[str]): Predictions of the model.
            context (str): The context (previous words in the sentence).
            memory (int): Memory consumption for the call of the model.
            runtime (int): Runtime for the call of the model.
            domain (str): Domain of this prediction.
        """
        # Record memory & runtime
        if memory >= 0:
            self.nwp_memories.append(memory)
        if runtime >= 0:
            self.nwp_runtimes.append(runtime)

        # Record counts
        if len(predicted_words) > 0 and predicted_words[0] == true_word:
            self.nwp_c[domain].correct += 1
        if true_word in predicted_words[:3]:
            self.nwp_c[domain].correct_3 += 1
        else:
            # If the word is not in the top-3 predictions, this is a mistake
            if self.track_mistakes:
                self.nwp_mistakes.update([Mistake(actual=true_word, preds=predicted_words[:3], context=context)])

        self.nwp_c[domain].total += 1

    def acp(
        self,
        true_word: str,
        predicted_words: List[str],
        partial_word: str,
        context: str,
        memory: int,
        runtime: int,
        domain: Optional[str] = None,
    ) -> None:
        """Method used to record a prediction for the auto-completion task.

        Args:
            true_word (str): The label (clean word to predict).
            predicted_words (List[str]): Predictions of the model.
            partial_word (str): The input sent to the model (only part of the
                word to predict, with potential typos).
            context (str): The context (previous words in the sentence).
            memory (int): Memory consumption for the call of the model.
            runtime (int): Runtime for the call of the model.
            domain (str): Domain of this prediction.
        """
        # Record memory & runtime
        if memory >= 0:
            self.acp_memories.append(memory)
        if runtime >= 0:
            self.acp_runtimes.append(runtime)

        # Check if a typo was introduced or not
        has_typo = WITHOUT_TYPO if true_word.startswith(partial_word) else WITH_TYPO

        # Compute the completion rate
        completion_rate = round(len(partial_word) / len(true_word), 2)

        # Record counts
        if len(predicted_words) > 0 and predicted_words[0] == true_word:
            self.acp_c[domain][has_typo][completion_rate].correct += 1
        if true_word in predicted_words[:3]:
            self.acp_c[domain][has_typo][completion_rate].correct_3 += 1
        else:
            # If the word is not in the top-3 predictions, this is a mistake
            if self.track_mistakes:
                self.acp_mistakes.update(
                    [Mistake(actual=true_word, preds=predicted_words[:3], context=f"{context}{partial_word}")]
                )

        self.acp_c[domain][has_typo][completion_rate].total += 1

    def acr(
        self,
        true_word: str,
        predicted_words: List[str],
        typed_word: str,
        context: str,
        typos: List[Typo],
        memory: int,
        runtime: int,
        domain: Optional[str] = None,
    ) -> None:
        """Method used to record a prediction for the auto-correction task.

        Args:
            true_word (str): The label (clean word to predict).
            predicted_words (List[str]): Predictions of the model.
            typed_word (str): The word typed, containing potential typos.
            context (str): The context (previous words in the sentence).
            typos (List[Typo]): List of typos introduced.
            memory (int): Memory consumption for the call of the model.
            runtime (int): Runtime for the call of the model.
            domain (str): Domain of this prediction.
        """
        # Record memory & runtime
        if memory >= 0:
            self.acr_memories.append(memory)
        if runtime >= 0:
            self.acr_runtimes.append(runtime)

        # Get the type of typo
        if not typos:
            typo_type = None
        elif len(typos) == 1:
            typo_type = typos[0]
        else:
            typo_type = len(typos)

        # Record counts
        if len(predicted_words) > 0 and predicted_words[0] == true_word:
            self.acr_c[domain][typo_type].correct += 1
        if true_word in predicted_words[:3]:
            self.acr_c[domain][typo_type].correct_3 += 1
        else:
            # If the word is not in the top-3 predictions, this is a mistake
            if self.track_mistakes:
                self.acr_mistakes.update(
                    [Mistake(actual=true_word, preds=predicted_words[:3], context=f"{context}{typed_word}")]
                )

        self.acr_c[domain][typo_type].total += 1

    def swp(
        self,
        true_word: str,
        predicted_words: List[str],
        context: str,
        memory: int,
        runtime: int,
        domain: Optional[str] = None,
    ) -> None:
        """Method used to record a prediction for the swipe resolution task.

        Args:
            true_word (str): The label (clean word to predict).
            predicted_words (List[str]): Predictions of the model.
            context (str): The context (previous words in the sentence).
            memory (int): Memory consumption for the call of the model.
            runtime (int): Runtime for the call of the model.
            domain (str): Domain of this prediction.
        """
        # Record memory & runtime
        if memory >= 0:
            self.swp_memories.append(memory)
        if runtime >= 0:
            self.swp_runtimes.append(runtime)

        # Record counts
        if len(predicted_words) > 0 and predicted_words[0] == true_word:
            self.swp_c[domain].correct += 1
        if true_word in predicted_words[:3]:
            self.swp_c[domain].correct_3 += 1
        else:
            # If the word is not in the top-3 predictions, this is a mistake
            if self.track_mistakes:
                self.swp_mistakes.update([Mistake(actual=true_word, preds=predicted_words[:3], context=context)])

        self.swp_c[domain].total += 1

    def set_domain(self, domain: str) -> None:
        """Method setting the domain for the scores associated with no domain.

        To make it easier to score a single sentence, it's possible to call the
        scorer without a domain (see signature of `nwp()`, `acp()`, `acr()`).
        In this case the scores are associated to no domain (`None` key).
        This method allows the user to set the domain name for these scores
        with no domain (effectively moving the `None` domain scores to the
        given domain name).

        Note:
            If some scores were already linked to the given domain, these
            scores will be erased (replaced by the scores of the `None`
            domain).

        Args:
            domain (str): Domain name to associate the scores to.
        """
        if None in self.nwp_c:
            self.nwp_c[domain] = self.nwp_c.pop(None)
        if None in self.acp_c:
            self.acp_c[domain] = self.acp_c.pop(None)
        if None in self.acr_c:
            self.acr_c[domain] = self.acr_c.pop(None)
        if None in self.swp_c:
            self.swp_c[domain] = self.swp_c.pop(None)

    def _score_accuracy(self, c: Count) -> Dict:
        """Helper method to compute the accuracy given a prediction count.

        This method return a dictionary with 3 metrics :
         * Accuracy
         * Top3 accuracy
         * Total number of predictions

        Args:
            c (Count): Count object to use to compute the accuracy.

        Returns:
            Dictionary with the computed metrics.
        """
        return {
            "accuracy": round_to_n(c.correct / c.total) if c.total != 0 else 0,
            "top3_accuracy": round_to_n(c.correct_3 / c.total) if c.total != 0 else 0,
            "n": c.total,
        }

    def _score_precision_recall(self, no_typo_c: Count, typo_c: Count, beta: float) -> Dict:
        """Helper method to compute the precision and recall for
        auto-correction.

        This method return a dictionary with several metrics :
         * Accuracy
         * Precision
         * Recall
         * F-score
         * Top3 accuracy
         * Top3 precision
         * Top3 recall
         * Top3 F-score
         * Number of predictions with a typo
         * Total number of predictions

        For auto-correction, we need 2 Count objects : the counts of typos, and
        the counts of non-typo (to compute the True Negative and False Positive
        metrics).

        Args:
            no_typo_c (Count): Count object for the predictions where no typo
                were added.
            typo_c (Count): Count object for the predictions where typos were
                added.
            beta (float): Beta to use for computing the F-beta score.

        Returns:
            Dictionary with the computed metrics.
        """
        # The first step is to divide the counts into TN, FP, TP, FN
        tn = no_typo_c.correct
        fp = no_typo_c.total - no_typo_c.correct
        tp = typo_c.correct
        fn = typo_c.total - typo_c.correct

        tn_3 = no_typo_c.correct_3
        fp_3 = no_typo_c.total - no_typo_c.correct_3
        tp_3 = typo_c.correct_3
        fn_3 = typo_c.total - typo_c.correct_3

        # Then we compute the metrics
        p = precision(tp=tp, fp=fp)
        r = recall(tp=tp, fn=fn)

        p_3 = precision(tp=tp_3, fp=fp_3)
        r_3 = recall(tp=tp_3, fn=fn_3)

        return {
            "accuracy": round_to_n(accuracy(tp=tp, tn=tn, fp=fp, fn=fn)),
            "precision": round_to_n(p),
            "recall": round_to_n(r),
            "fscore": round_to_n(fbeta(precision=p, recall=r, beta=beta)),
            "top3_accuracy": round_to_n(accuracy(tp=tp_3, tn=tn_3, fp=fp_3, fn=fn_3)),
            "top3_precision": round_to_n(p_3),
            "top3_recall": round_to_n(r_3),
            "top3_fscore": round_to_n(fbeta(precision=p_3, recall=r_3, beta=beta)),
            "n_typo": typo_c.total,
            "n": no_typo_c.total + typo_c.total,
        }

    def _score_performances(self, memories: List[int], runtimes: List[int]) -> Dict:
        """Helper method to compute metrics related to the memory & runtime.

        This method returns a dictionary with several metrics :
         * The mean memory consumption
         * The min memory consumption
         * The max memory consumption
         * The mean running time
         * The fastest running time
         * The slowest running time

        Args:
            memories (List[int]): List of memories consumptions for a
                specific operation.
            runtimes (List[int]): List of runtimes for a specific operation.

        Returns:
            Dictionary with the computed metrics.
        """
        perf = {
            "mean_memory": stats.mean(memories) if memories else 0,
            "min_memory": min(memories) if memories else 0,
            "max_memory": max(memories) if memories else 0,
            "mean_runtime": stats.mean(runtimes) if runtimes else 0,
            "fastest_runtime": min(runtimes) if runtimes else 0,
            "slowest_runtime": max(runtimes) if runtimes else 0,
        }

        return {
            name: human_readable_memory(x) if name.endswith("memory") else human_readable_runtime(x)
            for name, x in perf.items()
        }

    def score(self, beta: float = DEFAULT_BETA) -> Dict:  # noqa: C901
        """Method that computes the final scores (as well as some alternative
        metrics that can bring insight in the capabilities of the model), and
        output these in an organized dictionary.

        Args:
            beta (float, optional): Beta to use for computing the F-beta score.

        Returns:
            Dictionary containing the computed scores and metrics for the
            model tested.
        """
        # --- Next-word prediction ---
        # Group scores by domain
        per = defaultdict(Count)
        for domain, c in self.nwp_c.items():
            per[domain] += c
        total_c = sum(per.values(), Count())
        per_domain = {k: self._score_accuracy(c) for k, c in per.items()}

        # Task results
        nwp = {
            "score": self._score_accuracy(total_c),
            "per_domain": per_domain,
            "performances": self._score_performances(self.nwp_memories, self.nwp_runtimes),
        }

        # --- Auto-completion ---
        # Group scores by domain
        per = defaultdict(Count)
        for domain, d1 in self.acp_c.items():
            for has_typo, d2 in d1.items():
                for compl_rate, c in d2.items():
                    per[domain] += c
        total_c = sum(per.values(), Count())
        per_domain = {k: self._score_accuracy(c) for k, c in per.items()}

        # Group scores by completion rate
        per = defaultdict(Count)
        for domain, d1 in self.acp_c.items():
            for has_typo, d2 in d1.items():
                for compl_rate, c in d2.items():
                    per[compl_rate] += c
        per_compl_rate = {
            "<25%": self._score_accuracy(sum((c for k, c in per.items() if k < 0.25), Count())),
            "25%~50%": self._score_accuracy(sum((c for k, c in per.items() if 0.25 <= k < 0.5), Count())),
            "50%~75%": self._score_accuracy(sum((c for k, c in per.items() if 0.5 <= k < 0.75), Count())),
            ">75%": self._score_accuracy(sum((c for k, c in per.items() if 0.75 <= k), Count())),
        }

        # Group scores by with_typo / without_typo
        per = defaultdict(Count)
        for domain, d1 in self.acp_c.items():
            for has_typo, d2 in d1.items():
                for compl_rate, c in d2.items():
                    per[has_typo] += c
        per_other = {k: self._score_accuracy(per[k]) for k in [WITHOUT_TYPO, WITH_TYPO]}

        # Task results
        acp = {
            "score": self._score_accuracy(total_c),
            "per_domain": per_domain,
            "per_completion_rate": per_compl_rate,
            "per_other": per_other,
            "performances": self._score_performances(self.acp_memories, self.acp_runtimes),
        }

        # --- Auto-correction ---
        # Group scores by domain
        no_typo_per, typo_per = defaultdict(Count), defaultdict(Count)
        for domain, d1 in self.acr_c.items():
            for typo, c in d1.items():
                if typo is None:
                    no_typo_per[domain] += c
                else:
                    typo_per[domain] += c
        no_typo_total_c = sum(no_typo_per.values(), Count())
        typo_total_c = sum(typo_per.values(), Count())
        per_domain = {k: self._score_precision_recall(no_typo_per[k], typo_per[k], beta=beta) for k in no_typo_per}

        # Group scores by typo type
        no_typo_c, typo_per = Count(), defaultdict(Count)
        for domain, d1 in self.acr_c.items():
            for typo, c in d1.items():
                if typo is None:
                    no_typo_c += c
                else:
                    typo_per[typo] += c
        # Divide the total count of no-typo into each type of typos with the right proportions
        no_typo_per = defaultdict(Count, {k: no_typo_c * (c.total / typo_total_c.total) for k, c in typo_per.items()})
        per_typo_type = {t.name: self._score_precision_recall(no_typo_per[t], typo_per[t], beta=beta) for t in Typo}
        per_n_typo = {
            "1": self._score_precision_recall(
                sum((c for k, c in no_typo_per.items() if isinstance(k, Typo)), Count()),
                sum((c for k, c in typo_per.items() if isinstance(k, Typo)), Count()),
                beta=beta,
            ),
            "2": self._score_precision_recall(no_typo_per[2], typo_per[2], beta=beta),
            "3+": self._score_precision_recall(
                sum((c for k, c in no_typo_per.items() if isinstance(k, int) and k > 2), Count()),
                sum((c for k, c in typo_per.items() if isinstance(k, int) and k > 2), Count()),
                beta=beta,
            ),
        }

        # Task results
        acr = {
            "score": self._score_precision_recall(no_typo_total_c, typo_total_c, beta=beta),
            "per_domain": per_domain,
            "per_typo_type": per_typo_type,
            "per_number_of_typos": per_n_typo,
            "performances": self._score_performances(self.acr_memories, self.acr_runtimes),
        }

        # --- Swipe resolution ---
        # Group scores by domain
        per = defaultdict(Count)
        for domain, c in self.swp_c.items():
            per[domain] += c
        total_c = sum(per.values(), Count())
        per_domain = {k: self._score_accuracy(c) for k, c in per.items()}

        # Task results
        swp = {
            "score": self._score_accuracy(total_c),
            "per_domain": per_domain,
            "performances": self._score_performances(self.swp_memories, self.swp_runtimes),
        }

        # Final results
        results = {
            "next_word_prediction": nwp,
            "auto_completion": acp,
            "auto_correction": acr,
            "swipe_resolution": swp,
        }

        # Add the overall score
        results["overall_score"] = one_score(results)

        return results
