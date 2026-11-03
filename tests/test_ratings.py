import re

import pytest

from careertracker.domain.ratings import RATING_COLORS, rating_color


@pytest.mark.parametrize(
    ("ovr", "color"),
    [
        (99, "#0f7a3d"), (90, "#0f7a3d"),
        (89, "#1e9e4a"), (85, "#1e9e4a"),
        (84, "#3fbf4f"), (80, "#3fbf4f"),
        (79, "#8cc63f"), (75, "#8cc63f"),
        (74, "#c5d334"), (70, "#c5d334"),
        (69, "#f2c230"), (65, "#f2c230"),
        (64, "#f59e2c"), (60, "#f59e2c"),
        (59, "#ee6a2b"), (50, "#ee6a2b"),
        (49, "#d63a2f"), (0, "#d63a2f"), (-5, "#d63a2f"),
    ],
)  # fmt: skip
def test_rating_color_boundaries(ovr, color):
    assert rating_color(ovr) == color


def test_thresholds_are_descending_and_end_at_zero():
    thresholds = [t for t, _ in RATING_COLORS]
    assert thresholds == sorted(thresholds, reverse=True)
    assert thresholds[-1] == 0


def test_colors_are_hex():
    for _, color in RATING_COLORS:
        assert re.fullmatch(r"#[0-9a-f]{6}", color)


def test_better_rating_never_gets_a_worse_bucket():
    buckets = [
        next(i for i, (t, _) in enumerate(RATING_COLORS) if o >= t) for o in range(100)
    ]
    assert buckets == sorted(buckets, reverse=True)
