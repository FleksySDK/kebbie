from kebbie.gesture import MAX_N_POINTS_PER_DIST, MIN_N_POINTS_PER_DIST, make_swipe_gesture
from kebbie.utils import euclidian_dist


def test_make_swipe_gesture_between_2_points(seeded):
    control_points = [(0, 0), (100, 100)]

    points = make_swipe_gesture(control_points)

    d = euclidian_dist(control_points[0], control_points[1])
    assert int(d * MIN_N_POINTS_PER_DIST) <= len(points) <= int(d * MAX_N_POINTS_PER_DIST)


def test_make_swipe_gesture_between_more_points(seeded):
    points = make_swipe_gesture([(0, 0), (100, 100), (50, 80), (-100, 10)])
    assert len(points) > 4


def test_make_swipe_gesture_single_control_point():
    assert make_swipe_gesture([(0, 0)]) == [(0, 0)]


def test_make_swipe_gesture_same_points():
    assert make_swipe_gesture([(0, 0), (0, 0)]) == [(0, 0)]


def test_make_swipe_gesture_too_small_points(seeded):
    points = make_swipe_gesture([(0, 0), (0.1, 0)])
    assert len(points) > 2
