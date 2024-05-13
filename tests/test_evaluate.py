import pytest

import kebbie
from kebbie import Corrector, UnsupportedLanguage, evaluate


class MockOracle:
    def __init__(self, *args, **kwargs):
        pass

    def test(self, *args, **kwargs):
        return None


@pytest.fixture
def dummy_oracle(monkeypatch):
    # Oracle is already unit-tested, so here just use a dummy oracle
    monkeypatch.setattr(kebbie, "Oracle", MockOracle)


class DummyCorrector(Corrector):
    pass


def test_evaluate_basic(dummy_oracle, mock_load_dataset):
    corrector = DummyCorrector()
    assert evaluate(corrector) is None


def test_evaluate_unknown_lang(dummy_oracle):
    with pytest.raises(UnsupportedLanguage):
        corrector = DummyCorrector()
        evaluate(corrector, lang="Klingon")
