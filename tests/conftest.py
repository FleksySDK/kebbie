import random
import shutil

import datasets
import pytest
import requests

import kebbie
from kebbie.noise_model import NoiseModel, Typo


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    # Make sure unit-tests don't use any resources pulled from the internet
    # using `requests`
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


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


class MockDataset:
    def __init__(self):
        self.n = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.n += 1

        if self.n > 20:
            raise StopIteration

        # A dummy dataset of 20 similar sentences
        return {
            "narrative": f"He, in fact, didn't have {self.n} wooden sticks.",
            "dialogue": [
                f"I have {self.n} wooden sticks.",
                "Yes, I'm sure.",
                "No way !",
            ],
        }

    def shuffle(self, seed: int = 0):
        return self


@pytest.fixture
def mock_load_dataset(monkeypatch):
    # Mock dataset to avoid downloading a full-fledge dataset
    def mock_load_dataset(*args, **kwargs):
        return MockDataset()

    monkeypatch.setattr(datasets, "load_dataset", mock_load_dataset)


@pytest.fixture
def seeded():
    random.seed(36)
