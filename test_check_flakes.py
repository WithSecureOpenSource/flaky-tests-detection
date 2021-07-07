from check_flakes import calc_fliprate, non_overlapping_window_fliprate

import pandas as pd
from pandas.testing import assert_series_equal
import pytest


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (["pass"], 0.0),
        (["fail", "fail"], 0.0),
        (["pass", "fail", "fail"], 0.5),
        ([0, 1, 0, 1], 1),
    ],
)
def test_calc_fliprate(test_input, expected) -> None:
    test_results = pd.Series(test_input)
    assert calc_fliprate(test_results) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            (["pass", "pass", "fail", "pass", "pass", "fail"], 2, 3),
            ([1, 2, 3], [0.0, 1.0, 1.0]),
        ),
        (
            (["pass", "pass"], 2, 1),
            ([1], [0.0]),
        ),
        (
            ([0], 15, 1),
            ([1], [0.0]),
        ),
        (
            (["fail", "fail"], 2, 5),
            ([5], [0.0]),
        ),
    ],
)
def test_non_overlapping_window_fliprate(test_input, expected) -> None:
    test_results = pd.Series(test_input[0])
    window_size = test_input[1]
    window_count = test_input[2]

    result = non_overlapping_window_fliprate(test_results, window_size, window_count)
    expected_result = pd.Series(index=expected[0], data=expected[1])

    assert_series_equal(result, expected_result)
