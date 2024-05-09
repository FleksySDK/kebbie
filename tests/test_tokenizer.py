import pytest

from kebbie.tokenizer import BasicTokenizer


@pytest.fixture
def tokenizer():
    return BasicTokenizer()


@pytest.mark.parametrize("x", ['I"m', "I“m", "I”m", "I„m"])
def test_normalization_of_double_quotes(tokenizer, x):
    assert tokenizer.preprocess(x) == "I m"


@pytest.mark.parametrize("x", ["I'm", "I’m", "Iʻm", "I‘m", "I´m", "Iʼm"])
def test_normalization_of_single_quotes(tokenizer, x):
    assert tokenizer.preprocess(x) == "I'm"


@pytest.mark.parametrize("x", ["in-depth", "in–depth", "in—depth", "in‑depth", "in−depth", "inーdepth"])
def test_normalization_of_dash(tokenizer, x):
    assert tokenizer.preprocess(x) == "in-depth"


@pytest.mark.parametrize("x, out", [("this.", "this "), ("this․", "this "), ("this...", "this "), ("this…", "this "), ("this,", "this "), ("this‚", "this ")])
def test_normalization_of_other_symbols(tokenizer, x, out):
    assert tokenizer.preprocess(x) == out


@pytest.mark.parametrize("x", ["a,b", "a, b", "a ,b", "a , b", "a . b", "a ... b", "a. b", "a... b", "a?  b", "a  !b", "a  :    b"])
def test_punctuations_removal(tokenizer, x):
    assert tokenizer.preprocess(x) == "a b"


@pytest.mark.parametrize("inp, out", [("Several words", ["Several", "words"]), (" Several words ", ["Several", "words"])])
def test_word_split(tokenizer, inp, out):
    assert tokenizer.word_split(inp) == out


def test_update_context(tokenizer):
    assert tokenizer.update_context("This is ", "great") == "This is great "
