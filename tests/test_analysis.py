import math

from aquila.analyze_aquila_results import mean_interval, wilson_interval
from ankaa3.analyze_parity import coefficient_of_determination, compute_parity


def test_wilson_interval_contains_observed_proportion():
    low, high = wilson_interval(10, 20)
    assert 0 <= low <= 0.5 <= high <= 1


def test_mean_interval_is_centered_on_mean():
    low, high = mean_interval([0, 1, 2, 3])
    assert low < 1.5 < high


def test_parity_standard_error_includes_factor_two():
    result = compute_parity({"0000": 50, "0001": 50}, 4)
    assert math.isclose(result["parity"], 0.0)
    assert math.isclose(result["error"], 0.1)
    assert result["parity_ci95"][0] < 0 < result["parity_ci95"][1]


def test_fit_quality_statistic_is_one_for_exact_fit():
    assert math.isclose(
        coefficient_of_determination([1, 2, 3], [1, 2, 3]),
        1.0,
    )
