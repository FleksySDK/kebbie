import pickle

import pytest

import kebbie
from kebbie import Corrector
from kebbie.correctors import EmulatorCorrector


def test_default_behavior_of_corrector():
    corrector = Corrector()

    assert corrector.auto_correct("", [], "") == []
    assert corrector.auto_complete("", [], "") == []
    assert corrector.resolve_swipe("", []) == []
    assert corrector.predict_next_word("") == []


class MockEmulator:
    def __init__(self, *args, **kwargs):
        self.text = ""
        self.unpickable_attribute = lambda x: x

    def type_characters(self, s: str):
        self.text += s

    def paste(self, s: str):
        self.text = s

    def get_text(self):
        return self.text

    def get_predictions(self):
        return ["These", "are", "predictions"]


@pytest.fixture
def mock_emulator(monkeypatch):
    monkeypatch.setattr(kebbie.correctors, "Emulator", MockEmulator)


def test_corrector_with_emulator_is_pickable(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android")

    # Will crash if not pickable
    pickle.dumps(corrector)


def test_cached_type(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android")

    corrector.cached_type("This ", "is")
    assert corrector.emulator.text == "This is"

    corrector.cached_type("This is ", "great")
    assert corrector.emulator.text == "This is great"

    # Different context will trigger a paste in the emulator
    corrector.cached_type("That ", "is")
    assert corrector.emulator.text == "That is"


def test_auto_correct_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android")

    candidates = corrector.auto_correct("This ", [], "is")
    assert len(candidates) == 1 and candidates[0] == "is"


def test_auto_correct_not_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.auto_correct("This ", [], "is")
    assert len(candidates) == 3
    assert candidates[0] == "is"
    assert candidates[1] == "are"
    assert candidates[2] == "predictions"


def test_auto_complete_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android")

    candidates = corrector.auto_complete("It's ", [], "grea")
    assert len(candidates) == 0


def test_auto_complete_not_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.auto_complete("It's ", [], "grea")
    assert len(candidates) == 3
    assert candidates[0] == "These"
    assert candidates[1] == "are"
    assert candidates[2] == "predictions"


def test_predict_next_word_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android")

    candidates = corrector.predict_next_word("It's ")
    assert len(candidates) == 0


def test_predict_next_word_not_fast_mode(mock_emulator):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.predict_next_word("It's ")
    assert len(candidates) == 3
    assert candidates[0] == "These"
    assert candidates[1] == "are"
    assert candidates[2] == "predictions"


class MockEmulatorWithEmptyPreds(MockEmulator):
    def get_predictions(self):
        return ["These", "", "predictions"]


@pytest.fixture
def mock_emulator_with_empty_preds(monkeypatch, mock_emulator):
    monkeypatch.setattr(kebbie.correctors, "Emulator", MockEmulatorWithEmptyPreds)


def test_auto_correct_clean_empty_preds(mock_emulator_with_empty_preds):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.auto_correct("This ", [], "is")
    assert len(candidates) == 2
    assert candidates[0] == "is"
    assert candidates[1] == "predictions"


def test_auto_complete_clean_empty_preds(mock_emulator_with_empty_preds):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.auto_complete("It's ", [], "grea")
    assert len(candidates) == 2
    assert candidates[0] == "These"
    assert candidates[1] == "predictions"


def test_predict_next_word_clean_empty_preds(mock_emulator_with_empty_preds):
    corrector = EmulatorCorrector("gboard", "android", fast_mode=False)

    candidates = corrector.predict_next_word("It's ")
    assert len(candidates) == 2
    assert candidates[0] == "These"
    assert candidates[1] == "predictions"
