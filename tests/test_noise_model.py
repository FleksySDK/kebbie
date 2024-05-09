import shutil

import pytest
import requests

import kebbie
from kebbie.noise_model import NoiseModel, Typo


@pytest.fixture(scope="session")
def tmp_cache():
    return "/tmp/kebbie_test"


class MockCommonTypos:
    def __init__(self):
        self.text = "\n".join(
            [
                "\t".join(
                    ["intvite", "invite", "IN", "in<t>vite", "google_wave_intvite(2)", "google_wave_invite(38802)"]
                ),
                "\t".join(["goole", "google", "RM", "goo(g)le", "my_goole_wave(1)", "my_google_wave(35841)"]),
                "\t".join(["goolge", "google", "R1", "goo[l/g]e", "a_goolge_wave(1)", "a_google_wave(42205)"]),
                "\t".join(["waze", "wave", "R2", "wa[z:v]e", "google_waxe_invite(2)", "google_wave_invite(38802)"]),
            ]
        )


@pytest.fixture(scope="session")
def noisy(monkeypatch_session, tmp_cache):
    # Change the cache directory to a temporary folder, to not impact the
    # current cache
    monkeypatch_session.setattr(kebbie.noise_model, "CACHE_DIR", tmp_cache)

    # Make sure the cache folder is empty
    try:
        shutil.rmtree(tmp_cache)
    except FileNotFoundError:
        pass

    # Patch `requests` temporarily, so a custom list of common typos is used
    with monkeypatch_session.context() as m:

        def mock_get(*args, **kwargs):
            return MockCommonTypos()

        m.setattr(requests, "get", mock_get)

        # Create a clean noise model (which will populate the cache with the
        # mocked list of common typos)
        # Note that we initialize it with all typo probabilities set to 0, and
        # each test will individually change these probabilities
        return NoiseModel(lang="en-US", typo_probs={t: 0.0 for t in Typo}, x_ratio=float("inf"), y_ratio=float("inf"))


def test_retrieve_common_typos_cached(noisy):
    # The common typos were retrieved in the fixture, and cached
    # So, when rebuilding another noise model, the data from the cache should
    # be retrieved (without pulling the data from the internet)
    noisy2 = NoiseModel("en-US")
    assert noisy.common_typos == noisy2.common_typos


def test_common_typos_with_unsupported_language(noisy):
    noisy2 = NoiseModel("en-US")
    noisy2.lang = "fr-FR"  # We don't have a list of common typos for French
    assert noisy2._get_common_typos() == {}


@pytest.mark.parametrize(
    "x", ["great", "Great", "GREAT", "grEAT", "éthéré", "éthÉré", "한국", "I'm", "in-depth", "gr8t"]
)
def test_correctable_words(noisy, x):
    assert noisy._is_correctable(x)


@pytest.mark.parametrize("x", ["667", ";", "???"])
def test_non_correctable_words(noisy, x):
    assert not noisy._is_correctable(x)


def test_create_swipe_gesture_for_correctable_word(noisy, seeded):
    points = noisy.swipe("make")
    assert len(points) > 4


def test_cant_create_swipe_gesture_for_non_correctable_word(noisy, seeded):
    assert noisy.swipe("667") is None


def test_perfect_fuzzy_type_normal_word(noisy, seeded):
    word = "great"
    keystrokes, typed_word, typos = noisy._fuzzy_type(word)

    assert len(keystrokes) == len(word)
    assert all(k is not None for k in keystrokes)
    assert typed_word == word
    assert len(typos) == 0


def test_perfect_fuzzy_type_word_with_characters_from_another_layer(noisy, seeded):
    word = "greAt"
    keystrokes, typed_word, typos = noisy._fuzzy_type(word)

    assert len(keystrokes) == len(word)
    assert keystrokes[3] is None
    assert typed_word == word
    assert len(typos) == 0


def test_perfect_fuzzy_type_word_with_unknown_characters(noisy, seeded):
    word = "gr☂t"
    keystrokes, typed_word, typos = noisy._fuzzy_type(word)

    assert len(keystrokes) == len(word)
    assert keystrokes[2] is None
    assert typed_word == word
    assert len(typos) == 0


def test_very_fuzzy_typing(noisy, seeded, monkeypatch):
    word = "great"
    with monkeypatch.context() as m:
        # Set Gaussian standard deviation to 1, which means more chance
        # to type outside of the intended key press (giving a fuzzy typo)
        m.setattr(noisy, "x_ratio", 1)
        m.setattr(noisy, "y_ratio", 1)

        keystrokes, typed_word, typos = noisy._fuzzy_type(word)

    assert len(keystrokes) == len(word)
    assert typed_word != word
    assert len(typos) > 0
    assert all(t == Typo.SUBSTITUTE_CHAR for t in typos)


def test_introduce_typos_no_typos(noisy):
    s = "This"
    noisy_s, typos = noisy._introduce_typos(s, error_free=True)
    assert noisy_s == s
    assert len(typos) == 0


def test_introduce_typos_common_typos(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.COMMON_TYPO, 1)

        noisy_s, typos = noisy._introduce_typos("wave")

    assert noisy_s == "waze"
    assert len(typos) == 1 and typos[0] == Typo.COMMON_TYPO


def test_introduce_typos_simplify_accent(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.SIMPLIFY_ACCENT, 1)

        noisy_s, typos = noisy._introduce_typos("cassé")

    assert noisy_s == "casse"
    assert len(typos) == 1 and typos[0] == Typo.SIMPLIFY_ACCENT


def test_introduce_typos_simplify_case(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.SIMPLIFY_CASE, 1)

        noisy_s, typos = noisy._introduce_typos("This")

    assert noisy_s == "this"
    assert len(typos) == 1 and typos[0] == Typo.SIMPLIFY_CASE


def test_introduce_typos_dont_simplify_case_for_full_uppercase(noisy, seeded, monkeypatch):
    s = "HELLYEAH"
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.SIMPLIFY_CASE, 1)

        noisy_s, typos = noisy._introduce_typos(s)

    assert noisy_s == s
    assert len(typos) == 0


def test_introduce_typos_transposition(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.TRANSPOSE_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos("hi")

    assert noisy_s == "ih"
    assert len(typos) == 1 and typos[0] == Typo.TRANSPOSE_CHAR


def test_introduce_typos_no_transposition_on_different_layer(noisy, seeded, monkeypatch):
    s = "Hi"
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.TRANSPOSE_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos(s)

    assert noisy_s == s
    assert len(typos) == 0


def test_introduce_typos_no_transposition_on_unknown_character(noisy, seeded, monkeypatch):
    s = "a⛬"
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.TRANSPOSE_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos(s)

    assert noisy_s == s
    assert len(typos) == 0


def test_introduce_typos_delete_spelling_symbol(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_SPELLING_SYMBOL, 1)

        noisy_s, typos = noisy._introduce_typos("I'm")

    assert noisy_s == "Im"
    assert len(typos) == 1 and typos[0] == Typo.DELETE_SPELLING_SYMBOL


def test_introduce_typos_add_spelling_symbol(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_SPELLING_SYMBOL, 1)

        noisy_s, typos = noisy._introduce_typos("I'm")

    assert noisy_s == "I''m"
    assert len(typos) == 1 and typos[0] == Typo.ADD_SPELLING_SYMBOL


def test_introduce_typos_delete_space(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_SPACE, 1)

        noisy_s, typos = noisy._introduce_typos("This is")

    assert noisy_s == "Thisis"
    assert len(typos) == 1 and typos[0] == Typo.DELETE_SPACE


def test_introduce_typos_delete_single_space(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_SPACE, 1)

        noisy_s, typos = noisy._introduce_typos(" ")

    assert noisy_s == ""
    assert len(typos) == 1 and typos[0] == Typo.DELETE_SPACE


def test_introduce_typos_add_space(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_SPACE, 1)

        noisy_s, typos = noisy._introduce_typos("This is")

    assert noisy_s == "This  is"
    assert len(typos) == 1 and typos[0] == Typo.ADD_SPACE


def test_introduce_typos_delete_punctuation(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_PUNCTUATION, 1)

        noisy_s, typos = noisy._introduce_typos("This, and")

    assert noisy_s == "This and"
    assert len(typos) == 1 and typos[0] == Typo.DELETE_PUNCTUATION


def test_introduce_typos_add_punctuation(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_PUNCTUATION, 1)

        noisy_s, typos = noisy._introduce_typos("This, and")

    assert noisy_s == "This,, and"
    assert len(typos) == 1 and typos[0] == Typo.ADD_PUNCTUATION


def test_introduce_typos_delete_char(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos("hi")

    # Note, the last character is never deleted, because this is an auto-completion case
    assert noisy_s == "i"
    assert len(typos) == 1 and typos[0] == Typo.DELETE_CHAR


def test_introduce_typos_add_char(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos("hi")

    assert noisy_s == "hhii"
    assert len(typos) == 2 and all(t == Typo.ADD_CHAR for t in typos)


def test_introduce_typos_dont_add_typos_on_numbers(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos("he11o")

    assert noisy_s == "hhee11oo"


def test_introduce_typos_dont_add_typos_on_unknown_characters(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.ADD_CHAR, 1)

        noisy_s, typos = noisy._introduce_typos("h⛬e")

    assert noisy_s == "hh⛬ee"


def test_perfect_type_till_space(noisy, seeded):
    keystrokes, typed, n_words, typos = noisy.type_till_space(["This", "is", "great"])

    assert len(keystrokes) == len("This")
    assert typed == "This"
    assert n_words == 1
    assert len(typos) == 0


def test_imperfect_type_till_space_both_fuzzy_and_other_typo(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set Gaussian standard deviation to 1, which means more chance
        # to type outside of the intended key press (giving a fuzzy typo)
        m.setattr(noisy, "x_ratio", 1)
        m.setattr(noisy, "y_ratio", 1)

        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.SIMPLIFY_CASE, 1)

        keystrokes, typed, n_words, typos = noisy.type_till_space(["Hello", "there"])

    assert len(keystrokes) == len("Hello")
    assert typed != "Hello"
    assert n_words == 1
    assert len(typos) > 2
    assert Typo.SIMPLIFY_CASE in typos and Typo.SUBSTITUTE_CHAR in typos


def test_type_till_space_with_missing_space_typo(noisy, seeded, monkeypatch):
    with monkeypatch.context() as m:
        # Set probability of typo to 1 for this test, to ensure it's generated
        m.setitem(noisy.probs, Typo.DELETE_SPACE, 1)
        m.setattr(kebbie.noise_model, "FRONT_DELETION_MULTIPLIER", 1)

        keystrokes, typed, n_words, typos = noisy.type_till_space(["Hello", "there"])

    assert len(keystrokes) == len("Hello") + len("there")
    assert typed == "Hellothere"
    assert n_words == 2
    assert len(typos) > 0 and all(t == Typo.DELETE_SPACE for t in typos)
