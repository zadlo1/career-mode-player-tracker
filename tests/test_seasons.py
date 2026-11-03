import pytest

from careertracker.domain.seasons import is_valid_season, next_season


@pytest.mark.parametrize(
    "text",
    ["2026/27", "2029/30", "1999/00", "2026", "1999", " 2026/27 ", "2000/01"],
)
def test_valid_seasons(text):
    assert is_valid_season(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "26/27",
        "2026/28",
        "2026/26",
        "2026-27",
        "2026/2027",
        "abcd",
        "20266",
        "2026/",
    ],
)
def test_invalid_seasons(text):
    assert not is_valid_season(text)


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        ("2026/27", "2027/28"),
        ("2028/29", "2029/30"),
        ("2029/30", "2030/31"),
        ("1999/00", "2000/01"),
        ("2026", "2027"),
        (" 2026/27 ", "2027/28"),
    ],
)
def test_next_season(current, expected):
    assert next_season(current) == expected


@pytest.mark.parametrize("current", ["", None, "26/27", "2026/28", "abc"])
def test_next_season_of_invalid_input_is_empty(current):
    assert next_season(current) == ""


def test_next_season_is_always_valid():
    season = "2026/27"
    for _ in range(30):
        season = next_season(season)
        assert is_valid_season(season)
