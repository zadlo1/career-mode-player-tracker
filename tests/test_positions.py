import pytest

from careertracker.domain.positions import (
    GROUP_COLORS,
    POSITION_GROUPS,
    POSITIONS,
    UNKNOWN_COLOR,
    is_goalkeeper,
    position_color,
    position_group,
    position_sort_key,
)


def test_positions_list():
    assert POSITIONS[0] == "GK"
    assert len(POSITIONS) == 15
    assert len(set(POSITIONS)) == 15


def test_every_position_has_a_known_group_with_a_color():
    for position in POSITIONS:
        assert POSITION_GROUPS[position] in GROUP_COLORS


@pytest.mark.parametrize(
    ("position", "group"),
    [("GK", "GK"), ("CB", "DEF"), ("RWB", "DEF"), ("CAM", "MID"), ("LM", "MID"),
     ("RW", "ATT"), ("ST", "ATT"), ("st", "ATT"), ("Cm", "MID")],
)  # fmt: skip
def test_position_group(position, group):
    assert position_group(position) == group


def test_unknown_position_uses_default():
    assert position_group("XX") is None
    assert position_group("XX", default="MID") == "MID"
    assert position_group(None) is None


def test_is_goalkeeper():
    assert is_goalkeeper("GK")
    assert is_goalkeeper("gk")
    assert not is_goalkeeper("CB")
    assert not is_goalkeeper(None)


def test_position_color():
    assert position_color("GK") == GROUP_COLORS["GK"]
    assert position_color("st") == GROUP_COLORS["ATT"]
    assert position_color("XX") == UNKNOWN_COLOR


def test_groups_have_distinct_colors():
    assert len(set(GROUP_COLORS.values())) == len(GROUP_COLORS)


def test_sort_key_orders_goalkeepers_defenders_midfielders_attackers():
    shuffled = ["ST", "XX", "CM", "GK", "RB", "CAM", "LW", "CB"]
    ordered = sorted(shuffled, key=position_sort_key)
    assert ordered[0] == "GK"
    assert ordered[-1] == "XX"
    groups = [position_group(p, default="?") for p in ordered]
    assert groups == ["GK", "DEF", "DEF", "MID", "MID", "ATT", "ATT", "?"]
