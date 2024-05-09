import pytest

from kebbie.layout import LayoutHelper


@pytest.fixture
def layout():
    return LayoutHelper()


def test_get_existing_key_info_same_layer(layout):
    q_info = layout.get_key_info("q")
    w_info = layout.get_key_info("w")

    q_width, q_height, q_x_center, q_y_center, q_layer = q_info
    w_width, w_height, w_x_center, w_y_center, w_layer = w_info
    assert q_width == w_width
    assert q_height == w_height
    assert q_x_center < w_x_center
    assert q_y_center == w_y_center
    assert q_layer == w_layer


def test_get_existing_key_info_different_layer(layout):
    q_info = layout.get_key_info("q")
    uq_info = layout.get_key_info("Q")

    q_width, q_height, q_x_center, q_y_center, q_layer = q_info
    uq_width, uq_height, uq_x_center, uq_y_center, uq_layer = uq_info
    assert q_width == uq_width
    assert q_height == uq_height
    assert q_x_center == uq_x_center
    assert q_y_center == uq_y_center
    assert q_layer < uq_layer


def test_get_existing_key_info_accent(layout):
    e_info = layout.get_key_info("e")
    é_info = layout.get_key_info("é")

    e_width, e_height, e_x_center, e_y_center, e_layer = e_info
    é_width, é_height, é_x_center, é_y_center, é_layer = é_info
    assert e_width == é_width
    assert e_height == é_height
    assert e_layer < é_layer


def test_get_non_existing_key_info(layout):
    with pytest.raises(KeyError):
        layout.get_key_info("☯")


def test_get_key_within_bounds(layout):
    f_info = layout.get_key_info("f")
    f_width, f_height, f_x_center, f_y_center, f_layer = f_info

    assert layout.get_key((f_x_center, f_y_center), 0) == "f"
    assert layout.get_key((f_x_center + f_width / 3, f_y_center + f_height / 3), 0) == "f"
    assert layout.get_key((f_x_center - f_width / 3, f_y_center - f_height / 3), 0) == "f"

    assert layout.get_key((f_x_center, f_y_center), 1) == "F"


def test_get_key_outside_of_bounds(layout):
    f_info = layout.get_key_info("f")
    f_width, f_height, f_x_center, f_y_center, f_layer = f_info

    assert layout.get_key((f_x_center + f_width + 1, f_y_center), 0) != "f"
    assert layout.get_key((f_x_center, f_y_center + f_height + 1), 0) != "f"


def test_get_closest_border_key(layout):
    assert layout.get_key((-5000, -5000), 0) == "q"


def test_ignore_additional_keyboard_layers():
    layout = LayoutHelper(ignore_layers_after=0)
    with pytest.raises(KeyError):
        layout.get_key_info("Q")


@pytest.mark.parametrize("k", [" ", "."])
def test_special_keys_that_should_exist(layout, k):
    try:
        layout.get_key_info(k)
    except KeyError:
        pytest.fail(f"Key `{k}` is not part of the layout")


@pytest.mark.parametrize("k", ["shift", "SHIFT", "mic"])
def test_special_keys_that_should_not_exist(layout, k):
    with pytest.raises(KeyError):
        layout.get_key_info(k)
