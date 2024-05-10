from collections import defaultdict

import pytest

from kebbie.noise_model import Typo
from kebbie.scorer import Count, Scorer, dd_x_layers


def test_count_addition():
    c1 = Count(56, 133, 356)
    c2 = Count(3, 23, 25)

    c3 = c1 + c2

    assert c3.correct == 56 + 3
    assert c3.correct_3 == 133 + 23
    assert c3.total == 356 + 25


def test_count_multiplication_int():
    c1 = Count(56, 133, 356)

    c2 = c1 * 34

    assert c2.correct == 56 * 34
    assert c2.correct_3 == 133 * 34
    assert c2.total == 356 * 34


def test_count_multiplication_float():
    c1 = Count(56, 133, 356)

    c2 = c1 * 0.3

    assert c2.correct == round(56 * 0.3)
    assert c2.correct_3 == round(133 * 0.3)
    assert c2.total == round(356 * 0.3)


def test_dd_x_layers_1_layer():
    d = dd_x_layers()

    assert isinstance(d, defaultdict)
    assert isinstance(d[0], Count)


def test_dd_x_layers_multiple_layers():
    d = dd_x_layers(3)

    assert isinstance(d, defaultdict)
    assert isinstance(d[0], defaultdict)
    assert isinstance(d[0][0], defaultdict)
    assert isinstance(d[0][0][0], Count)


@pytest.mark.parametrize("memory", [3476, -1])
@pytest.mark.parametrize("runtime", [29, -1])
@pytest.mark.parametrize("word, correct, correct_3", [("ok", 1, 1), ("ok3", 0, 1), ("ok4", 0, 0)])
def test_scorer_record_nwp_prediction(word, correct, correct_3, memory, runtime):
    s = Scorer([])

    s.nwp(
        true_word=word,
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        context=None,
        memory=memory,
        runtime=runtime,
    )

    assert s.nwp_c[None].correct == correct
    assert s.nwp_c[None].correct_3 == correct_3
    assert s.nwp_c[None].total == 1
    assert len(s.nwp_memories) == int(memory >= 0)
    assert len(s.nwp_runtimes) == int(runtime >= 0)


@pytest.mark.parametrize("memory", [3476, -1])
@pytest.mark.parametrize("runtime", [29, -1])
@pytest.mark.parametrize("word, correct, correct_3", [("ok", 1, 1), ("ok3", 0, 1), ("ok4", 0, 0)])
def test_scorer_record_acp_prediction_without_typo(word, correct, correct_3, memory, runtime):
    s = Scorer([])

    s.acp(
        true_word=word,
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        partial_word="o",
        context=None,
        memory=memory,
        runtime=runtime,
    )

    completion_rate = round(len("o") / len(word), 2)
    assert s.acp_c[None]["without_typo"][completion_rate].correct == correct
    assert s.acp_c[None]["without_typo"][completion_rate].correct_3 == correct_3
    assert s.acp_c[None]["without_typo"][completion_rate].total == 1
    assert len(s.acp_memories) == int(memory >= 0)
    assert len(s.acp_runtimes) == int(runtime >= 0)


@pytest.mark.parametrize("memory", [3476, -1])
@pytest.mark.parametrize("runtime", [29, -1])
@pytest.mark.parametrize("word, correct, correct_3", [("ok", 1, 1), ("ok3", 0, 1), ("ok4", 0, 0)])
def test_scorer_record_acp_prediction_with_typo(word, correct, correct_3, memory, runtime):
    s = Scorer([])

    s.acp(
        true_word=word,
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        partial_word="p",
        context=None,
        memory=memory,
        runtime=runtime,
    )

    completion_rate = round(len("o") / len(word), 2)
    assert s.acp_c[None]["with_typo"][completion_rate].correct == correct
    assert s.acp_c[None]["with_typo"][completion_rate].correct_3 == correct_3
    assert s.acp_c[None]["with_typo"][completion_rate].total == 1
    assert len(s.acp_memories) == int(memory >= 0)
    assert len(s.acp_runtimes) == int(runtime >= 0)


@pytest.mark.parametrize("memory", [3476, -1])
@pytest.mark.parametrize("runtime", [29, -1])
@pytest.mark.parametrize("typos", [[], [Typo.SIMPLIFY_ACCENT], [Typo.SIMPLIFY_ACCENT, Typo.DELETE_CHAR]])
@pytest.mark.parametrize("word, correct, correct_3", [("ok", 1, 1), ("ok3", 0, 1), ("ok4", 0, 0)])
def test_scorer_record_acr_prediction_without_typo(word, correct, correct_3, memory, runtime, typos):
    s = Scorer([])

    s.acr(
        true_word=word,
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        typed_word=word,
        context=None,
        typos=typos,
        memory=memory,
        runtime=runtime,
    )

    typo_type = None if not typos else (typos[0] if len(typos) == 1 else len(typos))
    assert s.acr_c[None][typo_type].correct == correct
    assert s.acr_c[None][typo_type].correct_3 == correct_3
    assert s.acr_c[None][typo_type].total == 1
    assert len(s.acr_memories) == int(memory >= 0)
    assert len(s.acr_runtimes) == int(runtime >= 0)


@pytest.mark.parametrize("memory", [3476, -1])
@pytest.mark.parametrize("runtime", [29, -1])
@pytest.mark.parametrize("word, correct, correct_3", [("ok", 1, 1), ("ok3", 0, 1), ("ok4", 0, 0)])
def test_scorer_record_swp_prediction(word, correct, correct_3, memory, runtime):
    s = Scorer([])

    s.swp(
        true_word=word,
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        context=None,
        memory=memory,
        runtime=runtime,
    )

    assert s.swp_c[None].correct == correct
    assert s.swp_c[None].correct_3 == correct_3
    assert s.swp_c[None].total == 1
    assert len(s.swp_memories) == int(memory >= 0)
    assert len(s.swp_runtimes) == int(runtime >= 0)


def test_set_domain():
    s = Scorer([])

    s.nwp_c["domain1"] = Count(56, 133, 356)
    s.nwp_c[None] = Count(2, 4, 6)

    s.acp_c["domain1"] = Count(56, 133, 356)
    s.acp_c[None] = Count(2, 4, 6)

    s.acr_c["domain1"] = Count(56, 133, 356)
    s.acr_c[None] = Count(2, 4, 6)

    s.swp_c["domain1"] = Count(56, 133, 356)
    s.swp_c[None] = Count(2, 4, 6)

    s.set_domain("domain2")

    assert s.nwp_c["domain2"] == Count(2, 4, 6)
    assert s.acp_c["domain2"] == Count(2, 4, 6)
    assert s.acr_c["domain2"] == Count(2, 4, 6)
    assert s.swp_c["domain2"] == Count(2, 4, 6)


@pytest.mark.parametrize("metric", ["accuracy", "top3_accuracy"])
def test_score_nwp_between_domains(metric):
    s = Scorer([])

    s.nwp_c["domain1"] = Count(56, 133, 356)
    s.nwp_c["domain2"] = Count(2, 4, 6)

    score = s.score()

    assert (
        score["next_word_prediction"]["per_domain"]["domain1"][metric]
        < score["next_word_prediction"]["per_domain"]["domain2"][metric]
    )
    assert score["next_word_prediction"]["score"][metric] > 0
    assert score["next_word_prediction"]["score"]["n"] > 0


@pytest.mark.parametrize("metric", ["accuracy", "top3_accuracy"])
def test_score_acp_between_completion_rates(metric):
    s = Scorer([])

    s.acp_c["domain1"]["without_typo"][0.12] = Count(5, 6, 10)
    s.acp_c["domain1"]["without_typo"][0.33] = Count(5, 6, 9)
    s.acp_c["domain1"]["without_typo"][0.51] = Count(5, 6, 8)
    s.acp_c["domain1"]["without_typo"][0.52] = Count(5, 6, 8)
    s.acp_c["domain1"]["without_typo"][0.9] = Count(5, 6, 7)

    score = s.score()

    assert (
        score["auto_completion"]["per_completion_rate"]["<25%"][metric]
        < score["auto_completion"]["per_completion_rate"]["25%~50%"][metric]
    )
    assert (
        score["auto_completion"]["per_completion_rate"]["25%~50%"][metric]
        < score["auto_completion"]["per_completion_rate"]["50%~75%"][metric]
    )
    assert (
        score["auto_completion"]["per_completion_rate"]["50%~75%"][metric]
        < score["auto_completion"]["per_completion_rate"][">75%"][metric]
    )
    assert score["auto_completion"]["score"][metric] > 0
    assert score["auto_completion"]["score"]["n"] > 0


@pytest.mark.parametrize("metric", ["accuracy", "top3_accuracy"])
def test_score_acp_between_typo_no_typo(metric):
    s = Scorer([])

    s.acp_c["domain1"]["without_typo"][0.88] = Count(5, 6, 10)
    s.acp_c["domain1"]["with_typo"][0.33] = Count(5, 6, 4658)

    score = s.score()

    assert (
        score["auto_completion"]["per_other"]["with_typo"][metric]
        < score["auto_completion"]["per_other"]["without_typo"][metric]
    )
    assert score["auto_completion"]["score"][metric] > 0
    assert score["auto_completion"]["score"]["n"] > 0


@pytest.mark.parametrize(
    "metric",
    ["accuracy", "precision", "recall", "fscore", "top3_accuracy", "top3_precision", "top3_recall", "top3_fscore"],
)
def test_score_acr_between_typo_type(metric):
    s = Scorer([])

    s.acr_c["domain1"][None] = Count(5, 6, 12)
    s.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] = Count(5, 6, 10)
    s.acr_c["domain1"][Typo.DELETE_CHAR] = Count(5, 6, 4658)

    score = s.score()

    assert (
        score["auto_correction"]["per_typo_type"][Typo.DELETE_CHAR.name][metric]
        < score["auto_correction"]["per_typo_type"][Typo.SIMPLIFY_ACCENT.name][metric]
    )
    assert score["auto_correction"]["score"][metric] > 0
    assert score["auto_correction"]["score"]["n_typo"] > 0
    assert score["auto_correction"]["score"]["n"] > 0


@pytest.mark.parametrize(
    "metric",
    ["accuracy", "precision", "recall", "fscore", "top3_accuracy", "top3_precision", "top3_recall", "top3_fscore"],
)
def test_score_acr_between_number_of_typo(metric):
    s = Scorer([])

    s.acr_c["domain1"][None] = Count(1, 4, 12)
    s.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] = Count(5, 6, 10)
    s.acr_c["domain1"][Typo.DELETE_CHAR] = Count(5, 6, 120)
    s.acr_c["domain1"][2] = Count(5, 6, 458)
    s.acr_c["domain1"][3] = Count(5, 6, 580)
    s.acr_c["domain1"][5] = Count(5, 6, 986)

    score = s.score()

    assert (
        score["auto_correction"]["per_number_of_typos"]["3+"][metric]
        < score["auto_correction"]["per_number_of_typos"]["2"][metric]
    )
    assert (
        score["auto_correction"]["per_number_of_typos"]["2"][metric]
        < score["auto_correction"]["per_number_of_typos"]["1"][metric]
    )
    assert score["auto_correction"]["score"][metric] > 0
    assert score["auto_correction"]["score"]["n_typo"] > 0
    assert score["auto_correction"]["score"]["n"] > 0


def test_score_swp_performances_human_readable():
    s = Scorer([])

    s.swp_c["domain1"] = Count(56, 133, 356)
    s.swp_memories = [63, 75, 82, 47, 58]
    s.swp_runtimes = [623, 745, 812, 417, 583]

    score = s.score()

    assert score["swipe_resolution"]["performances"]["mean_memory"] == "65 B"
    assert score["swipe_resolution"]["performances"]["min_memory"] == "47 B"
    assert score["swipe_resolution"]["performances"]["max_memory"] == "82 B"
    assert score["swipe_resolution"]["performances"]["mean_runtime"] == "636 ns"
    assert score["swipe_resolution"]["performances"]["fastest_runtime"] == "417 ns"
    assert score["swipe_resolution"]["performances"]["slowest_runtime"] == "812 ns"


def test_score_swp_performances_non_human_readable():
    s = Scorer([], human_readable=False)

    s.swp_c["domain1"] = Count(56, 133, 356)
    s.swp_memories = [63, 75, 82, 47, 58]
    s.swp_runtimes = [623, 745, 812, 417, 583]

    score = s.score()

    assert score["swipe_resolution"]["performances"]["mean_memory"] == 65
    assert score["swipe_resolution"]["performances"]["min_memory"] == 47
    assert score["swipe_resolution"]["performances"]["max_memory"] == 82
    assert score["swipe_resolution"]["performances"]["mean_runtime"] == 636
    assert score["swipe_resolution"]["performances"]["fastest_runtime"] == 417
    assert score["swipe_resolution"]["performances"]["slowest_runtime"] == 812


def test_score_overall_score():
    s = Scorer([])

    s.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] = Count(5, 6, 10)
    s.acp_c["domain1"]["with_typo"][0.33] = Count(5, 6, 4658)
    s.nwp_c["domain2"] = Count(2, 4, 6)

    score = s.score()

    assert score["overall_score"] > 0


def test_score_empty_overall_score_but_with_default_domains():
    s = Scorer(["domain1", "domain2"])

    score = s.score()

    assert len(score["next_word_prediction"]["per_domain"].keys()) == 2
    assert len(score["auto_completion"]["per_domain"].keys()) == 2
    assert len(score["auto_correction"]["per_domain"].keys()) == 2
    assert len(score["swipe_resolution"]["per_domain"].keys()) == 2


def test_save_mistakes_nwp():
    s = Scorer([], track_mistakes=True)

    s.nwp(true_word="ok4", predicted_words=["ok", "ok2", "ok3", "ok4"], context=None, memory=-1, runtime=-1)

    m = s.nwp_mistakes.most_common()[0]
    assert m[0].actual == "ok4"
    assert m[0].preds == ["ok", "ok2", "ok3"]
    assert m[0].context is None
    assert m[1] == 1


def test_save_mistakes_acp():
    s = Scorer([], track_mistakes=True)

    s.acp(
        true_word="ok4",
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        partial_word="o",
        context="",
        memory=-1,
        runtime=-1,
    )

    m = s.acp_mistakes.most_common()[0]
    assert m[0].actual == "ok4"
    assert m[0].preds == ["ok", "ok2", "ok3"]
    assert m[0].context == "o"
    assert m[1] == 1


def test_save_mistakes_acr():
    s = Scorer([], track_mistakes=True)

    s.acr(
        true_word="ok4",
        predicted_words=["ok", "ok2", "ok3", "ok4"],
        typed_word="ok4",
        context="",
        typos=[],
        memory=-1,
        runtime=-1,
    )

    m = s.acr_mistakes.most_common()[0]
    assert m[0].actual == "ok4"
    assert m[0].preds == ["ok", "ok2", "ok3"]
    assert m[0].context == "ok4"
    assert m[1] == 1


def test_save_mistakes_swp():
    s = Scorer([], track_mistakes=True)

    s.swp(true_word="ok4", predicted_words=["ok", "ok2", "ok3", "ok4"], context=None, memory=-1, runtime=-1)

    m = s.swp_mistakes.most_common()[0]
    assert m[0].actual == "ok4"
    assert m[0].preds == ["ok", "ok2", "ok3"]
    assert m[0].context is None
    assert m[1] == 1


def test_add_scorers():
    s1 = Scorer([], track_mistakes=True)

    s1.swp(true_word="ok4", predicted_words=["ok", "ok2", "ok3", "ok4"], context=None, memory=-1, runtime=-1)
    s1.acp_c["domain1"]["without_typo"][0.12] = Count(5, 6, 10)
    s1.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] = Count(5, 6, 10)
    s1.nwp_c["domain2"] = Count(56, 133, 356)
    s1.swp_memories = [63, 75, 82, 47, 58]
    s1.swp_runtimes = [623, 745, 812, 417, 583]

    s2 = Scorer([], track_mistakes=True)

    s2.swp(true_word="ko4", predicted_words=["ko", "ko2", "ko3", "ko4"], context=None, memory=-1, runtime=-1)
    s2.nwp(true_word="ok4", predicted_words=["ok", "ok2", "ok3", "ok4"], context=None, memory=-1, runtime=-1)
    s2.acp_c["domain1"]["without_typo"][0.24] = Count(5, 6, 10)
    s2.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] = Count(55, 666, 1000)
    s2.nwp_c["domain1"] = Count(56, 133, 356)
    s2.swp_memories = [1]
    s2.swp_runtimes = [2]

    s1.add(s2)

    assert len(s1.swp_memories) == 6
    assert len(s1.swp_runtimes) == 6
    assert len(s1.swp_mistakes.most_common()) == 2
    assert len(s1.nwp_mistakes.most_common()) == 1
    assert s1.acp_c["domain1"]["without_typo"][0.12] == Count(5, 6, 10)
    assert s1.acp_c["domain1"]["without_typo"][0.24] == Count(5, 6, 10)
    assert s1.acr_c["domain1"][Typo.SIMPLIFY_ACCENT] == Count(5, 6, 10) + Count(55, 666, 1000)
    assert s1.nwp_c["domain1"] == Count(56, 133, 356)
    assert s1.nwp_c["domain2"] == Count(56, 133, 356)
