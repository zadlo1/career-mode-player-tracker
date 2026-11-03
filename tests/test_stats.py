import pytest

from careertracker.domain.stats import format_rate, per_match


def test_per_match():
    assert per_match(10, 5) == 2.0
    assert per_match(0, 30) == 0.0
    assert per_match(7, 28) == pytest.approx(0.25)


@pytest.mark.parametrize("matches", [0, None, -3])
def test_per_match_without_matches_is_none(matches):
    assert per_match(10, matches) is None


@pytest.mark.parametrize(
    ("value", "text"),
    [(0.5, "0,50"), (0.0, "0,00"), (1.0, "1,00"), (0.826, "0,83"), (12.0, "12,00")],
)
def test_format_rate(value, text):
    assert format_rate(value) == text


@pytest.mark.parametrize(
    ("value", "text"),
    [(0.447, "45%"), (0.389, "39%"), (1.0, "100%"), (0.0, "0%")],
)
def test_format_rate_percent(value, text):
    assert format_rate(value, percent=True) == text


@pytest.mark.parametrize("missing", [None, float("nan")])
def test_missing_rate_is_dash(missing):
    assert format_rate(missing) == "-"
    assert format_rate(missing, percent=True) == "-"
