import pytest

from kebbie import Corrector
from kebbie.oracle import Oracle


@pytest.fixture
def dummy_dataset():
    return {
        "narrative": [
            "This is a long and descriptive sentence",
            "They got up and withdrew quietly into the shadows",
        ],
        "dialogue": ["Hey what is up", "Nothing and you"],
    }


class DummyCorrector(Corrector):
    """Dummy Corrector that always returns the same predictions. It also counts
    the number of time each method was called.
    """

    def __init__(self):
        self.counts = {"nwp": 0, "acp": 0, "acr": 0, "swp": 0}

    def auto_correct(self, context, keystrokes, word):
        self.counts["acr"] += 1
        return ["is", "and", "descriptive"]

    def auto_complete(self, context, keystrokes, partial_word):
        self.counts["acp"] += 1
        return ["is", "and", "descriptive"]

    def resolve_swipe(self, context, swipe_gesture):
        self.counts["swp"] += 1
        return ["is", "and", "descriptive"]

    def predict_next_word(self, context):
        self.counts["nwp"] += 1
        return ["is", "and", "descriptive"]


class MockPool:
    """A mock of multiprocessing pool, that just call the function in the
    current process.
    """

    def __init__(self, processes, initializer, initargs):
        initializer(*initargs)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def imap_unordered(self, fn, inputs, chunksize):
        for x in inputs:
            yield fn(x)


class MockQueue:
    """A mock of multiprocessing queue, which works on a single process
    (regular queue, then...)
    """

    def __init__(self):
        self.q = []

    def put(self, x):
        self.q.append(x)

    def get(self):
        return self.q.pop(0)


@pytest.fixture
def no_mp(monkeypatch):
    import multiprocessing as mp

    monkeypatch.setattr(mp, "Pool", MockPool)
    monkeypatch.setattr(mp, "Queue", MockQueue)


@pytest.mark.parametrize("use_list", [False, True])
def test_oracle_basic(no_mp, dummy_dataset, noisy, use_list):
    oracle = Oracle(
        lang="en-US",
        test_data=dummy_dataset,
        custom_keyboard=None,
        track_mistakes=False,
        n_most_common_mistakes=10,
        beta=0.9,
    )

    corrector = DummyCorrector()

    # Using a seed that will trigger a swipe gesture (since we are not running these for all the words)
    if not use_list:
        # We can either give a corrector as is...
        results = oracle.test(corrector, n_proc=1, seed=13)
    else:
        # ... Or as a list (one instance per process)
        results = oracle.test([corrector], n_proc=1, seed=13)

    assert results["next_word_prediction"]["score"]["top3_accuracy"] == round(6 / 19, 2)
    assert results["next_word_prediction"]["score"]["n"] == 19
    assert corrector.counts["nwp"] == 19
    assert results["auto_completion"]["score"]["top3_accuracy"] == round(6 / 22, 2)
    assert results["auto_completion"]["score"]["n"] == 22
    assert corrector.counts["acp"] == 22
    # Can't really check auto-correction score, since typos are introduced at random
    assert results["auto_correction"]["score"]["n"] == corrector.counts["acr"]
    # Same for swipe
    assert corrector.counts["swp"] > 0
    assert results["swipe_resolution"]["score"]["n"] == corrector.counts["swp"]

    assert results["overall_score"] > 0


def test_oracle_reproducible(no_mp, dummy_dataset, noisy):
    oracle = Oracle(
        lang="en-US",
        test_data=dummy_dataset,
        custom_keyboard=None,
        track_mistakes=False,
        n_most_common_mistakes=10,
        beta=0.9,
    )

    corrector = DummyCorrector()

    # Despite using randomized typo, the same seed should always give the same results
    results_1 = oracle.test(corrector, n_proc=1, seed=2)
    results_2 = oracle.test(corrector, n_proc=1, seed=2)

    # But we have to exclude the runtimes / memories metrics, because they may
    # vary from one run to the other
    for task in ["next_word_prediction", "auto_completion", "auto_correction", "swipe_resolution"]:
        results_1[task].pop("performances")
        results_2[task].pop("performances")

    assert results_1 == results_2


def test_oracle_track_mistakes(no_mp, dummy_dataset, noisy):
    oracle = Oracle(
        lang="en-US",
        test_data=dummy_dataset,
        custom_keyboard=None,
        track_mistakes=True,
        n_most_common_mistakes=3,
        beta=0.9,
    )

    corrector = DummyCorrector()

    results = oracle.test(corrector, n_proc=1, seed=1)

    assert "most_common_mistakes" in results
    assert "next_word_prediction" in results["most_common_mistakes"]
    assert "auto_completion" in results["most_common_mistakes"]
    assert "auto_correction" in results["most_common_mistakes"]
    # +1 because of the title (CSV style)
    assert len(results["most_common_mistakes"]["next_word_prediction"]) == 3 + 1
    assert len(results["most_common_mistakes"]["auto_completion"]) == 3 + 1
    assert len(results["most_common_mistakes"]["auto_correction"]) == 3 + 1
