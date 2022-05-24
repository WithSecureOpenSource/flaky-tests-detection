# Flaky tests detection
Visualise tests whose state changes most often. During software development, it is often common that some tests start to randomly fail,
but finding those tests is a tedious and time consuming problem. Flaky tests detection solves that problem by processing historical xunit test
results and cheks which tests changes state most often. Flaky tests detection is available as Github Action plugin and
[Python package](https://pypi.org/project/flaky-tests-detection/). For usage, see [example](https://github.com/F-Secure/flaky-test-ci)
at the `actions` page.

Implementation is based on ["Modeling and ranking flaky tests at Apple"](https://dl.acm.org/doi/10.1145/3377813.3381370) by Kowalczyk, Emily & Nair, Karan & Gao, Zebao & Silberstein, Leo & Long, Teng & Memon, Atif.

## Features

* Prints out top test names and their latest calculation window scores (normal fliprate and exponentially weighted moving average fliprate that take previous calculation windows into account).
* Calculation grouping options:
  * `n` days.
  * `n` runs.
* Heatmap visualization of the scores and history.
  
## Parameters

### Data options (choose one)

* `--test-history-csv`
  * Give a path to a test history csv file which includes three fields: `timestamp`, `test_identifier` and `test_status`.
* `--junit-files`
  * Give a path to a folder with `JUnit` test results.
  
### Calculation options

* `--grouping-option`
  * `days` to use `n` days for fliprate calculation windows.
  * `runs` to use `n` runs for fliprate calculation windows.
  
* `--window-size`
  * Fliprate calculation window size `n`.
  
* `--window-count`
  * History size for exponentially weighted moving average calculations.
  
* `--top-n`
  * How many top highest scoring tests to print out.
### Heatmap generation
* `--heatmap`
  * Turn heatmap generation on.
  * Two pictures generated: normal fliprate and exponentially weighted moving average fliprate score.
  * Same parameters used as with the printed statistics.
  
### Full examples

* Precomputed `test_history.csv` with daily calulations. 1 day windows, 7 day history and 5 tests printed out.
  * `--test-history-csv=example_history/test_history.csv --grouping-option=days --window-size=1 --window-count=7 --top-n=5`
* `JUnit` files with calculations per 5 runs. 15 runs history and 5 tests printed out.
  * `--junit-files=example_history/junit_files --grouping-option=runs --window-size=5 --window-count=3 --top-n=5`
* Precomputed `test_history.csv` with daily calculations and heatmap generation. 1 day windows, 7 day history and 50 tests printed and generated to heatmaps.
  * `--test-history-csv=example_history/test_history.csv --grouping-option=days --window-size=1 --window-count=7 --top-n=50 --heatmap` 

## Install module

* `make install`

## Install module and development packages

* `make install_dev`

## Run pytest

* `make run_test`

## Acknowledgement

The package was developed by [F-Secure Corporation][f-secure] and [University of Helsinki][hy] in the scope of [IVVES project][ivves]. This work was labelled by [ITEA3][itea3] and funded by local authorities under grant agreement “ITEA-2019-18022-IVVES”

[ivves]: http://ivves.eu/
[itea3]: https://itea3.org/
[f-secure]: https://www.f-secure.com/en
[hy]: https://www.helsinki.fi/en/computer-science
