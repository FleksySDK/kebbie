import builtins
import json
import sys

import pytest

import kebbie
from kebbie.cmd import cli, instantiate_correctors


class MockEmulator:
    def __init__(self, *args, **kwargs):
        pass

    def get_android_devices():
        return ["emulator-5554", "emulator-5558"]

    def get_ios_devices():
        return [("iPhone 15 Pro", "17.4"), ("iPhone_15_2", "17.4")]

    def show_keyboards(self):
        pass

    def get_predictions(self):
        return ["These", "are", "predictions"]


@pytest.fixture
def mock_emulator(monkeypatch):
    monkeypatch.setattr(kebbie.correctors, "Emulator", MockEmulator)
    monkeypatch.setattr(kebbie.cmd, "Emulator", MockEmulator)


@pytest.mark.parametrize("fast_mode", [True, False])
@pytest.mark.parametrize("instantiate_emulator", [True, False])
@pytest.mark.parametrize(
    "kb_name, expected_platform",
    [
        ("gboard", "android"),
        ("tappa", "android"),
        ("ios", "ios"),
        ("fleksy", "ios"),
        ("kbkitpro", "ios"),
        ("kbkitoss", "ios"),
    ],
)
def test_instantiate_correctors(mock_emulator, kb_name, expected_platform, fast_mode, instantiate_emulator):
    correctors = instantiate_correctors(kb_name, fast_mode=fast_mode, instantiate_emulator=instantiate_emulator)

    # The mock emulator has 2 instances, so we should have 2 correctors
    assert len(correctors) == 2

    for c in correctors:
        assert c.platform == expected_platform
        assert c.fast_mode == fast_mode

        if instantiate_emulator:
            assert isinstance(c.emulator, MockEmulator)
        else:
            assert c.emulator is None


def test_cli_help():
    sys.argv = ["kebbie", "-h"]
    with pytest.raises(SystemExit) as e:
        cli()

    assert e.value.code == 0


def test_cli_no_subcommand():
    sys.argv = ["kebbie"]
    with pytest.raises(SystemExit) as e:
        cli()

    assert e.value.code == 1


@pytest.mark.parametrize("sub_command", ["evaluate", "show_layout"])
def test_cli_missing_keyboard_argument(sub_command):
    sys.argv = ["kebbie", sub_command]
    with pytest.raises(SystemExit) as e:
        cli()

    assert e.value.code > 0


@pytest.mark.parametrize("sub_command", ["evaluate", "show_layout"])
def test_cli_wrong_argument(sub_command):
    sys.argv = ["kebbie", sub_command, "--test_argument_that_does_not_exist"]
    with pytest.raises(SystemExit) as e:
        cli()

    assert e.value.code > 0


@pytest.fixture
def mock_evaluate(monkeypatch):
    def mock_evaluate(*args, **kwargs):
        return {"overall_score": 100}

    monkeypatch.setattr(kebbie.cmd, "evaluate", mock_evaluate)


class MockOpen:
    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass


@pytest.fixture
def mock_json_dump(monkeypatch):
    def mock_dump(*args, **kwargs):
        pass

    monkeypatch.setattr(json, "dump", mock_dump)

    def mock_open(*args, **kwargs):
        return MockOpen()

    monkeypatch.setattr(builtins, "open", mock_open)


def test_cli_evaluate_basic(mock_emulator, mock_load_dataset, mock_evaluate, mock_json_dump, capsys):
    sys.argv = ["kebbie", "evaluate", "-K", "gboard"]
    cli()

    captured = capsys.readouterr()
    assert captured.out == "Overall score :  100\n"


def test_cli_evaluate_with_all_arguments(mock_emulator, mock_load_dataset, mock_evaluate, mock_json_dump, capsys):
    sys.argv = [
        "kebbie",
        "evaluate",
        "-K",
        "gboard",
        "-R",
        "whatever.json",
        "--all_tasks",
        "--n_sentences",
        "3",
        "--track_mistakes",
    ]
    cli()

    captured = capsys.readouterr()
    assert captured.out == "Overall score :  100\n"


def test_cli_show_layout_basic(mock_emulator, capsys):
    sys.argv = ["kebbie", "show_layout", "-K", "gboard"]
    cli()

    captured = capsys.readouterr()
    # Notice the `* 2`, that's because there is 2 emulated devices
    assert captured.out == "Predictions : ['These', 'are', 'predictions']\n" * 2
