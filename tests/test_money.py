import math

import pytest

from careertracker.domain.money import format_money, format_plain_money, parse_money


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("3.000.000", 3_000_000),
        ("3000000", 3_000_000),
        ("3 000 000", 3_000_000),
        ("3\u00a0000\u00a0000", 3_000_000),
        ("3\u202f000\u202f000", 3_000_000),
        ("400.000 €", 400_000),
        ("€ 400.000", 400_000),
        ("  5.000  ", 5_000),
        ("0", 0),
        (1500, 1500),
    ],
)
def test_parse_money(text, value):
    assert parse_money(text) == value


@pytest.mark.parametrize("blank", ["", "   ", None, float("nan"), "€"])
def test_blank_means_no_value(blank):
    assert parse_money(blank) is None


@pytest.mark.parametrize("text", ["abc", "3M", "12a3", "-5", "1e6"])
def test_invalid_money_raises(text):
    with pytest.raises(ValueError):
        parse_money(text)


@pytest.mark.parametrize(
    ("value", "text"),
    [(5_000_000, "5.000.000 €"), (400_000, "400.000 €"), (999, "999 €"), (0, "0 €")],
)
def test_format_money(value, text):
    assert format_money(value) == text


@pytest.mark.parametrize("missing", [None, float("nan")])
def test_missing_value_is_dash(missing):
    assert format_money(missing) == "-"
    assert format_plain_money(missing) == ""


def test_format_plain_money_has_no_euro_sign():
    assert format_plain_money(3_000_000) == "3.000.000"


def test_format_and_parse_roundtrip():
    for value in (0, 1, 999, 1_000, 12_345, 3_000_000, 250_000_000):
        assert parse_money(format_money(value)) == value


def test_nan_is_really_handled_not_formatted():
    assert not math.isnan(parse_money("1") or 0)
