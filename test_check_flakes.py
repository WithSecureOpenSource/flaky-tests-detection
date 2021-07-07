from check_flakes import (
    calc_fliprate,
    calculate_n_day_flipdata,
    calculate_n_runs_flipdata,
    non_overlapping_window_fliprate,
)

import pandas as pd
from pandas.testing import assert_series_equal
import pytest


def create_test_history_df() -> pd.DataFrame:
    """Create some fake test history.
    test1 is flaky.
    """
    timestamps = [
        "2021-07-01 07:00:00",
        "2021-07-01 07:00:00",
        "2021-07-01 08:00:00",
        "2021-07-01 08:00:00",
        "2021-07-02 07:00:00",
        "2021-07-02 07:00:00",
        "2021-07-02 08:00:00",
        "2021-07-02 08:00:00",
        "2021-07-03 07:00:00",
        "2021-07-03 07:00:00",
        "2021-07-03 08:00:00",
        "2021-07-03 08:00:00",
        "2021-07-03 09:00:00",
    ]
    test_identifiers = [
        "test1",
        "test2",
        "test1",
        "test2",
        "test1",
        "test2",
        "test1",
        "test2",
        "test1",
        "test2",
        "test1",
        "test2",
        "test1",
    ]
    test_statutes = [
        "pass",
        "pass",
        "fail",
        "pass",
        "pass",
        "pass",
        "fail",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "fail",
    ]
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "test_identifier": test_identifiers,
            "test_status": test_statutes,
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    return df


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
    """Test fliprate calculation for different test histories"""
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
    """Test different window fliprate calculations"""
    test_results = pd.Series(test_input[0])
    window_size = test_input[1]
    window_count = test_input[2]

    result = non_overlapping_window_fliprate(test_results, window_size, window_count)
    expected_result = pd.Series(index=expected[0], data=expected[1])

    assert_series_equal(result, expected_result)


def test_calculate_n_day_flipdata() -> None:
    """Test that the correct flaky test output is calculated when grouping with days.
    Moving average (ewm) fliprate depends on EWM value but should be higher than latest normal fliprate.
    """
    top_n = 1
    day_window = 1
    day_window_count = 3

    df = create_test_history_df()
    top_fliprates, top_fliprates_ewm = calculate_n_day_flipdata(
        df, top_n, day_window, day_window_count
    )

    top_flaky_test_name, top_flaky_test_score = top_fliprates[0]
    top_flaky_test_name_ewm, top_flaky_test_score_ewm = top_fliprates_ewm[0]

    assert top_flaky_test_name == "test1"
    assert top_flaky_test_score == 0.5

    assert top_flaky_test_name_ewm == "test1"
    assert top_flaky_test_score_ewm > 0.5


def test_calculate_n_runs_flipdata() -> None:
    """Test that the correct flaky test output is calculated when grouping with runs.
    Moving average (ewm) fliprate depends on EWM value but should be higher than latest normal fliprate.
    """
    top_n = 1
    run_window = 3
    run_window_count = 2

    df = create_test_history_df()
    top_fliprates, top_fliprates_ewm = calculate_n_runs_flipdata(
        df, top_n, run_window, run_window_count
    )

    top_flaky_test_name, top_flaky_test_score = top_fliprates[0]
    top_flaky_test_name_ewm, top_flaky_test_score_ewm = top_fliprates_ewm[0]

    assert top_flaky_test_name == "test1"
    assert top_flaky_test_score == 0.5

    assert top_flaky_test_name_ewm == "test1"
    assert top_flaky_test_score_ewm > 0.5
