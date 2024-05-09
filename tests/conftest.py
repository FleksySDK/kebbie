import random

import pytest


@pytest.fixture
def seeded():
    random.seed(36)
