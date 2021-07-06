import argparse
import glob
from typing import List, Tuple

from junitparser import JUnitXml
import pandas as pd
import numpy as np

EWM_ALPHA = 0.1
EWM_ADJUST = False


def calc_fliprate(testruns: pd.Series) -> float:
    """Calculate test result fliprate from given test results series"""
    if len(testruns) == 1:
        return 0
    first = True
    previous = None
    flips = 0
    possible_flips = len(testruns) - 1
    for _, val in testruns.iteritems():
        if first:
            first = False
            previous = val
            continue
        if val != previous:
            flips += 1
        previous = val
    return flips / possible_flips


def non_overlapping_window_fliprate(
    testruns: pd.Series, window_size: int, window_count: int
) -> pd.Series:
    """Reverse given testruns to latest first and calculate flip rate for non-overlapping run windows"""
    testruns_reversed = testruns.iloc[::-1]
    fliprate_groups = (
        testruns_reversed.groupby(np.arange(len(testruns_reversed)) // window_size)
        .apply(calc_fliprate)
        .iloc[:window_count]
    )
    return fliprate_groups.rename(lambda x: window_count - x).sort_index()


def calculate_n_day_flipdata(
    testrun_table: pd.DataFrame, top_n: int, days: int, window_count: int
) -> Tuple[List, List]:
    """Select given history amount and calculate fliprates for given n day windows.
    Return top fliprates (moving average and without) for the latest window.
    """
    data = testrun_table[
        testrun_table.index
        >= (testrun_table.index.max() - pd.Timedelta(days=days * window_count))
    ]

    fliprates = data.groupby([pd.Grouper(freq=f"{days}D"), "test_identifier"])[
        "test_status"
    ].apply(calc_fliprate)

    fliprate_table = fliprates.rename("flip_rate").reset_index()
    fliprate_table["flip_rate_ewm"] = (
        fliprate_table.groupby("test_identifier")["flip_rate"]
        .ewm(alpha=EWM_ALPHA, adjust=EWM_ADJUST)
        .mean()
        .droplevel("test_identifier")
    )

    last_window_values = fliprate_table.groupby("test_identifier").last()

    top_fliprates = last_window_values.nlargest(top_n, "flip_rate")[
        ["flip_rate"]
    ].reset_index()

    top_fliprates_ewm = last_window_values.nlargest(top_n, "flip_rate_ewm")[
        ["flip_rate_ewm"]
    ].reset_index()

    return top_fliprates.to_records(index=False), top_fliprates_ewm.to_records(
        index=False
    )


def calculate_n_runs_flipdata(
    testrun_table: pd.DataFrame, top_n: int, window_size: int, window_count: int
) -> Tuple[List, List]:
    """Calculate fliprates for given n run window and select m of those windows
    Return top fliprates (moving average and without) for the latest window.
    """
    fliprates = testrun_table.groupby("test_identifier")["test_status"].apply(
        lambda x: non_overlapping_window_fliprate(x, window_size, window_count)
    )

    fliprate_table = fliprates.rename("flip_rate").reset_index()
    fliprate_table["flip_rate_ewm"] = (
        fliprate_table.groupby("test_identifier")["flip_rate"]
        .ewm(alpha=EWM_ALPHA, adjust=EWM_ADJUST)
        .mean()
        .droplevel("test_identifier")
    )
    fliprate_table = fliprate_table.rename(columns={"level_1": "window"})

    top_fliprates = fliprate_table[fliprate_table["window"] == window_count].nlargest(
        top_n, "flip_rate"
    )[["test_identifier", "flip_rate"]]

    top_fliprates_ewm = fliprate_table[
        fliprate_table["window"] == window_count
    ].nlargest(top_n, "flip_rate_ewm")[["test_identifier", "flip_rate_ewm"]]

    return top_fliprates.to_records(index=False), top_fliprates_ewm.to_records(
        index=False
    )


def parse_junit_to_df(folder_path: str) -> pd.DataFrame:
    """Read JUnit test result files to a test history dataframe"""
    dataframe_entries = []

    for filepath in glob.iglob(f"{folder_path}/*.xml"):
        xml = JUnitXml.fromfile(filepath)
        for suite in xml:
            time = suite.timestamp
            for testcase in suite:
                test_identifier = testcase.classname + "::" + testcase.name
                test_status = 0 if len(testcase.result) == 0 else 1

                dataframe_entries.append(
                    {
                        "timestamp": time,
                        "test_identifier": test_identifier,
                        "test_status": test_status,
                    }
                )

    df = pd.DataFrame(dataframe_entries)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    return df


if __name__ == "__main__":
    """Print out top flaky tests and their fliprate scores"""

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--junit-files",
        help="provide path for a folder with JUnit xml test history files",
    )
    group.add_argument(
        "--test-history-csv", help="provide path for precomputed test history csv"
    )
    parser.add_argument(
        "--grouping-option",
        help="flip rate calculation method - days or runs",
        required=True,
    )
    parser.add_argument(
        "--window-size",
        type=int,
        help="flip rate calculation window size",
        required=True,
    )
    parser.add_argument(
        "--window-count",
        type=int,
        help="flip rate calculation window count (history size)",
        required=True,
    )
    parser.add_argument(
        "--top-n",
        type=int,
        help="amount of unique tests and scores to print out",
        required=True,
    )

    args = parser.parse_args()

    if args.junit_files:
        df = parse_junit_to_df(args.junit_files)
    else:
        df = pd.read_csv(
            args.test_history_csv,
            index_col="timestamp",
            parse_dates=["timestamp"],
        )

    df = df.sort_index()

    if args.grouping_option == "days":
        top_fliprates, top_fliprates_ewm = calculate_n_day_flipdata(
            df, args.top_n, args.window_size, args.window_count
        )
    else:
        top_fliprates, top_fliprates_ewm = calculate_n_runs_flipdata(
            df, args.top_n, args.window_size, args.window_count
        )

    print(f"Top {args.top_n} flaky tests based on latest fliprate")
    for testname, score in top_fliprates:
        print(testname, "--- score:", score)
    print(
        f"\nTop {args.top_n} flaky tests based on latest exponential weighted moving average fliprate score"
    )
    for testname, score in top_fliprates_ewm:
        print(testname, "--- score:", score)
