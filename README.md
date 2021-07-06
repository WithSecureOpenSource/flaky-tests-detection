# fliprate_actions

Github actions plugin to check flakiness of tests by calculating fliprates. Usage demonstrated [here](https://github.com/guotin/flaky-test-ci) at the `actions` page.

## Features

* Prints out top test names and their latest calculation window scores (normal fliprate and exponentially weighted moving average fliprate that take previous calculation windows into account)
* Calculation grouping options:
  * `n` days
  * `n` runs
  
## Parameters

### Data options (choose one)

* `--test-history-csv`
  * Give a path to a test history csv file which includes three fields: `timestamp`, `test_identifier` and `test_status`
* `--junit-files`
  * Give a path to a folder with `JUnit` test results
  
### Calculation options

* `--grouping-option`
  * `days` to use `n` days for fliprate calculation windows
  * `runs` to use `n` runs for fliprate calculation windows
  
* `--window-size`
  * Fliprate calculation window size `n`
  
* `--window-count`
  * History size for exponentially weighted moving average calculations 
  
* `--top-n`
  * How many top highest scoring tests to print out
  
### Full examples

* Precomputed `test_history.csv` with daily calulations. 1 day windows, 7 day history and 5 tests printed out
  * `--test-history-csv=example_history/test_history.csv --grouping-option=days --window-size=1 --window-count=7 --top-n=5`
* `JUnit` files with calculations per 5 runs. 15 runs history and 5 tests printed out
  * `--junit-files=example_history/junit_files --grouping-option=runs --window-size=5 --window-count=3 --top-n=5`
