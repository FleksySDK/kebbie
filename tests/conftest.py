import random

import pytest


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    # Make sure unit-tests don't use any resources pulled from the internet
    # using `requests`
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture
def seeded():
    random.seed(36)
