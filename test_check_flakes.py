from check_flakes import (
    calc_fliprate,
    calculate_n_days_fliprate_table,
    calculate_n_runs_fliprate_table,
    get_top_fliprates,
    non_overlapping_window_fliprate,
)

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
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


def test_calculate_n_days_fliprate_table() -> None:
    """Test calculation of the fliprate table with valid daily grouping settings.
    Ignore checking correctness of flip_rate and flip_rate_ewm numeric values.
    """
    df = create_test_history_df()
    result_fliprate_table = calculate_n_days_fliprate_table(df, 1, 3)

    # check correct columns
    assert list(result_fliprate_table.columns) == [
        "timestamp",
        "test_identifier",
        "flip_rate",
        "flip_rate_ewm",
    ]

    result_fliprate_table = result_fliprate_table.drop(
        ["flip_rate", "flip_rate_ewm"], axis=1
    )

    expected_fliprate_table = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2021-07-01",
                    "2021-07-01",
                    "2021-07-02",
                    "2021-07-02",
                    "2021-07-03",
                    "2021-07-03",
                ]
            ),
            "test_identifier": ["test1", "test2", "test1", "test2", "test1", "test2"],
        }
    )
    # check other than fliprate values correctness
    assert_frame_equal(result_fliprate_table, expected_fliprate_table)


def test_calculate_n_runs_fliprate_table() -> None:
    """Test calculation of the fliprate table with valid grouping by runs settings.
    Ignore checking correctness of flip_rate and flip_rate_ewm numeric values.
    """
    df = create_test_history_df()
    result_fliprate_table = calculate_n_runs_fliprate_table(df, 2, 3)

    # check correct columns
    assert list(result_fliprate_table.columns) == [
        "test_identifier",
        "window",
        "flip_rate",
        "flip_rate_ewm",
    ]

    result_fliprate_table = result_fliprate_table.drop(
        ["flip_rate", "flip_rate_ewm"], axis=1
    )

    expected_fliprate_table = pd.DataFrame(
        {
            "test_identifier": ["test1", "test1", "test1", "test2", "test2", "test2"],
            "window": [1, 2, 3, 1, 2, 3],
        }
    )

    # check other than fliprate values correctness
    assert_frame_equal(result_fliprate_table, expected_fliprate_table)


def test_get_top_fliprates_from_run_windows() -> None:
    """Test calculating the top fliprates from fliprate table with n runs group windows"""
    fliprate_table = pd.DataFrame(
        {
            "test_identifier": ["test1", "test2", "test1", "test2", "test1", "test2"],
            "window": [1, 1, 2, 2, 3, 3],
            "flip_rate": [0.0, 0.0, 1.0, 0.0, 0.5, 0.0],
            "flip_rate_ewm": [0.0, 0.0, 0.95, 0.0, 0.7, 0.0],
        }
    )

    result = get_top_fliprates(fliprate_table, 1)

    assert result.top_normal_scores == {"test1": 0.5}
    assert result.top_ewm_scores == {"test1": 0.7}


def test_get_top_fliprates_from_day_windows() -> None:
    """Test calculating the top fliprates from fliprate table with n days group windows"""
    fliprate_table = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2021-07-01",
                    "2021-07-01",
                    "2021-07-01",
                    "2021-07-02",
                    "2021-07-02",
                    "2021-07-02",
                    "2021-07-03",
                    "2021-07-03",
                    "2021-07-03",
                ]
            ),
            "test_identifier": [
                "test1",
                "test2",
                "test3",
                "test1",
                "test2",
                "test3",
                "test1",
                "test2",
                "test3",
            ],
            "flip_rate": [0.0, 0.0, 0.5, 1.0, 0.0, 0.0, 0.5, 0.0, 0.3],
            "flip_rate_ewm": [0.0, 0.0, 0.5, 0.95, 0.0, 0.5, 0.7, 0.0, 0.2],
        }
    )
    result = get_top_fliprates(fliprate_table, 2)

    assert result.top_normal_scores == {"test1": 0.5, "test3": 0.3}
    assert result.top_ewm_scores == {"test1": 0.7, "test3": 0.2}
