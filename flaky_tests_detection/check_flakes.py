import argparse
import logging
from decimal import getcontext, Decimal, ROUND_UP
from pathlib import Path
from typing import Dict, NamedTuple, Set

from junitparser import JUnitXml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys

EWM_ALPHA = 0.1
EWM_ADJUST = False
HEATMAP_FIGSIZE = (100, 50)

PrintData = NamedTuple(
    "PrintData",
    [
        ("top_normal_scores", Dict[str, Decimal]),
        ("top_ewm_scores", Dict[str, Decimal]),
    ],
)

TableData = NamedTuple(
    "TableData",
    [
        ("normal_table", pd.DataFrame),
        ("ewm_table", pd.DataFrame),
    ],
)


def calc_fliprate(testruns: pd.Series) -> float:
    """Calculate test result fliprate from given test results series"""
    if len(testruns) < 2:
        return 0.0
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


def non_overlapping_window_fliprate(testruns: pd.Series, window_size: int, window_count: int) -> pd.Series:
    """Reverse given testruns to latest first and calculate flip rate for non-overlapping run windows"""
    testruns_reversed = testruns.iloc[::-1]
    fliprate_groups = (
        testruns_reversed.groupby(np.arange(len(testruns_reversed)) // window_size)
        .apply(calc_fliprate)
        .iloc[:window_count]
    )
    return fliprate_groups.rename(lambda x: window_count - x).sort_index()


def calculate_n_days_fliprate_table(testrun_table: pd.DataFrame, days: int, window_count: int) -> pd.DataFrame:
    """Select given history amount and calculate fliprates for given n day windows.

    Return a table containing the results.
    """
    data = testrun_table[testrun_table.index >= (testrun_table.index.max() - pd.Timedelta(days=days * window_count))]

    fliprates = data.groupby([pd.Grouper(freq=f"{days}D"), "test_identifier"])["test_status"].apply(calc_fliprate)

    fliprate_table = fliprates.rename("flip_rate").reset_index()
    fliprate_table["flip_rate_ewm"] = (
        fliprate_table.groupby("test_identifier")["flip_rate"]
        .ewm(alpha=EWM_ALPHA, adjust=EWM_ADJUST)
        .mean()
        .droplevel("test_identifier")
    )

    return fliprate_table[fliprate_table.flip_rate != 0]


def calculate_n_runs_fliprate_table(testrun_table: pd.DataFrame, window_size: int, window_count: int) -> pd.DataFrame:
    """Calculate fliprates for given n run window and select m of those windows
    Return a table containing the results.
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

    return fliprate_table[fliprate_table.flip_rate != 0]


def get_top_fliprates(fliprate_table: pd.DataFrame, top_n: int, precision: int) -> PrintData:
    """Look at the last calculation window for each test from the fliprate table
    and return the top n highest scoring test identifiers and their scores
    """
    context = getcontext()
    context.prec = precision
    context.rounding = ROUND_UP
    last_window_values = fliprate_table.groupby("test_identifier").last()

    top_fliprates = last_window_values.nlargest(top_n, "flip_rate")[["flip_rate"]].reset_index()

    top_fliprates_ewm = last_window_values.nlargest(top_n, "flip_rate_ewm")[["flip_rate_ewm"]].reset_index()

    #  Context precision and rounding only come into play during arithmetic operations. Therefore * 1
    top_fliprates_dict = {testname: Decimal(score) * 1 for testname, score in top_fliprates.to_records(index=False)}

    top_fliprates_ewm_dict = {
        testname: Decimal(score) * 1 for testname, score in top_fliprates_ewm.to_records(index=False)
    }

    return PrintData(top_normal_scores=top_fliprates_dict, top_ewm_scores=top_fliprates_ewm_dict)


def get_image_tables_from_fliprate_table(
    fliprate_table: pd.DataFrame,
    top_identifiers: Set[str],
    top_identifiers_ewm: Set[str],
) -> TableData:
    """Construct tables for heatmap generation from the fliprate table.
    Rows contain the test identifier and
    columns contain the window as timestamp for daily grouping or integer for grouping with runs.
    """
    pivot_columns = "timestamp" if "timestamp" in fliprate_table.columns else "window"
    image = fliprate_table.pivot(index="test_identifier", columns=pivot_columns, values="flip_rate")
    image_ewm = fliprate_table.pivot(index="test_identifier", columns=pivot_columns, values="flip_rate_ewm")

    image = image[image.index.isin(top_identifiers)]
    image_ewm = image_ewm[image_ewm.index.isin(top_identifiers_ewm)]

    return TableData(normal_table=image, ewm_table=image_ewm)


def generate_image(image: pd.DataFrame, title: str, filename: str) -> None:
    """Save a seaborn heatmap with given data"""
    plt.figure(figsize=HEATMAP_FIGSIZE)
    plt.title(title, fontsize=50)
    sns.heatmap(data=image, linecolor="black", linewidths=0.1, annot=True).set_facecolor("black")
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def parse_junit_to_df(folderpath: Path) -> pd.DataFrame:
    """Read JUnit test result files to a test history dataframe"""
    dataframe_entries = []

    for filepath in folderpath.glob("*.xml"):
        xml = JUnitXml.fromfile(filepath)
        for suite in xml:
            time = suite.timestamp
            for testcase in suite:
                test_identifier = testcase.classname + "::" + testcase.name

                # junitparser has "failure", "skipped" or "error" in result list if any
                if not testcase.result:
                    test_status = "pass"
                else:
                    test_status = testcase.result[0]._tag
                    if test_status == "skipped":
                        continue

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


def main(argv):
    """Print out top flaky tests and their fliprate scores.
    Also generate seaborn heatmaps visualizing the results if wanted.
    """

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--junit-files",
        help="provide path for a folder with JUnit xml test history files",
    )
    group.add_argument("--test-history-csv", help="provide path for precomputed test history csv")
    parser.add_argument(
        "--grouping-option",
        choices=["days", "runs"],
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
    parser.add_argument(
        "--precision, -p",
        type=int,
        help="Precision of the flip rate score, default is 4",
        default=4,
        dest="decimal_count",
    )
    parser.add_argument("--heatmap", action="store_true", default=False)
    args = parser.parse_args()
    precision = args.decimal_count

    if args.junit_files:
        df = parse_junit_to_df(Path(args.junit_files))
    else:
        df = pd.read_csv(
            args.test_history_csv,
            index_col="timestamp",
            parse_dates=["timestamp"],
        )

    df = df.sort_index()

    if args.grouping_option == "days":
        fliprate_table = calculate_n_days_fliprate_table(df, args.window_size, args.window_count)
    else:
        fliprate_table = calculate_n_runs_fliprate_table(df, args.window_size, args.window_count)

    printdata = get_top_fliprates(fliprate_table, args.top_n, precision)

    logging.info("Top %s flaky tests based on latest window fliprate", args.top_n)
    for testname, score in printdata.top_normal_scores.items():
        logging.info("%s --- score: %s", testname, score)
    logging.info(
        "\nTop %s flaky tests based on latest window exponential weighted moving average fliprate score",
        args.top_n,
    )
    for testname, score in printdata.top_ewm_scores.items():
        logging.info("%s --- score: %s", testname, score)

    if args.heatmap:
        logging.info("\n\nGenerating heatmap images...")
        top_identifiers = set(printdata.top_normal_scores.keys())
        top_identifiers_ewm = set(printdata.top_normal_scores.keys())

        tabledata = get_image_tables_from_fliprate_table(fliprate_table, top_identifiers, top_identifiers_ewm)

        if args.grouping_option == "days":
            title = f"Top {args.top_n} of tests with highest latest window fliprate - no exponentially weighted moving average - last {args.window_size * args.window_count} days of data"
            filename = f"{args.window_size}day_flip_rate_top{args.top_n}.png"
            title_ewm = f"Top {args.top_n} of tests with highest latest window exponentially weighted moving average fliprate score - alpha (smoothing factor) = {EWM_ALPHA} - last {args.window_size * args.window_count} days of data"
            filename_ewm = f"{args.window_size}day_flip_rate_ewm_top{args.top_n}.png"
        else:
            title = f"Top {args.top_n} of tests with highest latest window fliprate - no exponentially weighted moving average - {args.window_size} last runs fliprate and {args.window_size * args.window_count} last runs data"
            filename = f"{args.window_size}runs_flip_rate_top{args.top_n}.png"
            title_ewm = f"Top {args.top_n} of tests with highest latest window exponentially weighted moving average fliprate score - alpha (smoothing factor) = {EWM_ALPHA} - {args.window_size} last runs fliprate and {args.window_size * args.window_count} last runs data"
            filename_ewm = f"{args.window_size}runs_flip_rate_ewm_top{args.top_n}.png"
        generate_image(tabledata.normal_table, title, filename)
        generate_image(tabledata.ewm_table, title_ewm, filename_ewm)
        logging.info("%s and %s generated.", filename, filename_ewm)


if __name__ == "__main__":
    main(sys.argv)
