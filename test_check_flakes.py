from check_flakes import calc_fliprate

import pandas as pd
import pytest

@pytest.mark.parametrize("test_input,expected", [(["pass"], 0),(["fail","fail"], 0), (["pass","fail","fail"], 0.5), ([0,1,0,1], 1)])
def test_calc_fliprate(test_input, expected) -> None:
    test_results = pd.Series(test_input)
    assert calc_fliprate(test_results) == expected
