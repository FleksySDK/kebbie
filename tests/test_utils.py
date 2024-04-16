import math
import random
from collections import Counter

import pytest

from kebbie.utils import (
    accuracy,
    euclidian_dist,
    fbeta,
    load_keyboard,
    precision,
    recall,
    round_to_n,
    sample,
    sample_among,
    sample_partial_word,
    strip_accents,
)


SQRT_29 = math.sqrt(29)


@pytest.mark.parametrize(
    "p1, p2, d",
    [
        ((0, 0), (1, 0), 1),
        ((0, 0), (0, 1), 1),
        ((0, 0), (5, 2), SQRT_29),
        ((5, 2), (0, 0), SQRT_29),
        ((2, 5), (0, 0), SQRT_29),
        ((-2, 5), (0, 0), SQRT_29),
        ((-2, -5), (0, 0), SQRT_29),
    ],
)
def test_euclidian_dist(p1, p2, d):
    assert euclidian_dist(p1, p2) == d


@pytest.mark.parametrize("kwargs", [{}, {"lang": "en-US"}])
def test_load_keyboard_valid_language(kwargs):
    kb = load_keyboard(**kwargs)

    # Later we can do a better checking of the JSON content, for now this is ok
    assert "layout" in kb
    assert "settings" in kb
    assert "keyboard" in kb
    assert "char_dict" in kb


def test_load_keyboard_non_existing_language():
    with pytest.raises(FileNotFoundError):
        load_keyboard(lang="klingon")


@pytest.mark.parametrize("inp, out", [("éclair", "eclair"), ("ça", "ca")])
def test_strip_accents_with_accents(inp, out):
    assert strip_accents(inp) == out


@pytest.mark.parametrize("word", ["great", "great!", "¡great!"])
def test_strip_accents_without_accents(word):
    assert strip_accents(word) == word


@pytest.mark.parametrize("p", [1.5, 10, -0.999])
def test_sample_invalid_probability(p):
    with pytest.raises(AssertionError):
        sample(p)


def test_sample_edge_case_0():
    assert sample(0) is False


def test_sample_edge_case_1():
    assert sample(1) is True


def test_sample_general_case():
    # We should do a proper statistical test (with enough sampling)
    # But using the right seed allows us to speed up the test !
    random.seed(20)
    results = []
    for _ in range(100):
        results.append(sample(0.9))

    c = Counter(results)
    assert c[True] == 90 and c[False] == 10


@pytest.mark.parametrize("p", [{"a": -0.3}, {"a": 1.7}, {"a": 0.6, "b": 0.6}])
def test_sample_among_invalid_probabilities(p):
    with pytest.raises(AssertionError):
        sample_among(p)


def test_sample_among_with_none():
    random.seed(36)
    assert sample_among({"a": 0.1, "b": 0.1}) is None


def test_sample_among_without_none():
    random.seed(36)
    assert sample_among({"a": 0.9, "b": 0.1}, with_none=False) == "a"


def test_sample_partial_word_basic():
    w = "absolutely"
    partial_list, partial_w = sample_partial_word(list(range(len(w))), w, w)

    assert len(partial_list) == len(partial_w)
    assert w.startswith(partial_w)


@pytest.mark.parametrize(
    "tp, tn, fp, fn, acc", [(1, 0, 1, 0, 1 / 2), (0, 1, 1, 1, 1 / 3), (66, 3, 6, 7, 69 / 82), (0, 0, 0, 0, 0)]
)
def test_accuracy(tp, tn, fp, fn, acc):
    assert accuracy(tp, tn, fp, fn) == acc


@pytest.mark.parametrize("tp, fp, p", [(1, 1, 1 / 2), (3, 1, 3 / 4), (0, 0, 0)])
def test_precision(tp, fp, p):
    assert precision(tp, fp) == p


@pytest.mark.parametrize("tp, fn, r", [(1, 1, 1 / 2), (3, 1, 3 / 4), (0, 0, 0)])
def test_recall(tp, fn, r):
    assert recall(tp, fn) == r


@pytest.mark.parametrize(
    "p, r, score", [(0.4, 0.5, 0.4 / 0.9), (0.5, 0.4, 0.4 / 0.9), (0.2, 0.1, 0.04 / 0.3), (0, 0, 0)]
)
def test_fbeta_score_with_default_beta(p, r, score):
    assert fbeta(p, r) == score


@pytest.mark.parametrize("p, r, beta, score", [(0.4, 0.5, 0.5, 0.25 / 0.6), (0.4, 0.5, 1.5, 0.65 / 1.4), (0, 0, 0, 0)])
def test_fbeta_score(p, r, beta, score):
    assert fbeta(p, r, beta) == score


@pytest.mark.parametrize("inp, n, out", [(0.473568, 2, 0.47), (0.476568, 2, 0.48), (0.5, 2, 0.5), (0.5, 0, 0)])
def test_round_to_n(inp, n, out):
    assert round_to_n(inp, n) == out
