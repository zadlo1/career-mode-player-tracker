import pytest

from careertracker.domain import potential as pot
from careertracker.domain.seasons import next_season


def season(ovr, age, value=None, position="ST", matches=30, goals=8, assists=3):
    return {
        "ovr": ovr,
        "age": age,
        "value_eur": value,
        "position": position,
        "matches": matches,
        "goals": goals,
        "assists": assists,
    }


def pots(seasons, **kwargs):
    return [r["pot"] if r else None for r in pot.estimate_potentials(seasons, **kwargs)]


# ---------- krzywe pomocnicze (wartości kontrolne z wersji Streamlit) ----------


@pytest.mark.parametrize(
    ("age", "gap"),
    [(15, 30), (17, 30), (20, 22), (25, 8), (29, 2), (30, 0), (35, 0)],
)
def test_max_gap_by_age(age, gap):
    assert pot.max_gap(age) == gap


@pytest.mark.parametrize(
    ("age", "growth"),
    [(15, 4.5), (17, 4.5), (20, 3.0), (25, 0.5), (29, -0.5), (30, -1.0), (35, -3.5)],
)
def test_expected_growth_by_age(age, growth):
    assert pot.expected_growth(age) == pytest.approx(growth)


def test_max_gap_never_grows_with_age():
    gaps = [pot.max_gap(age) for age in range(15, 40)]
    assert gaps == sorted(gaps, reverse=True)


def test_base_value_is_exponential_in_ovr():
    assert pot.base_value(60) == 200_000
    assert pot.base_value(70) == pytest.approx(2_014_885, rel=1e-4)
    assert pot.base_value(80) == pytest.approx(20_298_806, rel=1e-4)
    assert pot.base_value(71) > pot.base_value(70)


@pytest.mark.parametrize(
    ("args", "gap", "extra"),
    [
        ((70, 19, 5_000_000, False), 15.204, 3.935),
        ((70, 19, None, False), 12.693, 0.0),
        ((70, 19, 5_000_000, True), 16.809, 3.935),
        ((80, 24, 40_000_000, False), 3.684, 2.936),
        ((65, 29, 1_000_000, False), 0.291, 2.281),
        ((50, 16, 100_000, False), 9.856, 6.999),
    ],
)
def test_value_signal_regression(args, gap, extra):
    got_gap, got_extra = pot.value_signal(*args)
    assert got_gap == pytest.approx(gap, abs=1e-3)
    assert got_extra == pytest.approx(extra, abs=1e-3)


# ---------- trend rozwoju ----------


def test_trend_without_history_is_zero():
    assert pot.development_trend([]) == 0.0
    assert pot.development_trend([{"age": 18, "ovr": 60}]) == 0.0


def test_trend_matches_expected_growth_is_zero():
    history = [{"age": 18, "ovr": 60}, {"age": 19, "ovr": 64}]
    assert pot.development_trend(history) == pytest.approx(0.0)


def test_trend_is_positive_for_fast_growth_and_negative_for_stagnation():
    fast = [{"age": 18, "ovr": 60}, {"age": 19, "ovr": 70}]
    stagnation = [{"age": 18, "ovr": 60}, {"age": 19, "ovr": 60}]
    assert pot.development_trend(fast) == pytest.approx(6.0)
    assert pot.development_trend(stagnation) == pytest.approx(-4.0)


# ---------- szacowanie POT (bez modelu) ----------


def test_young_player_who_keeps_growing():
    youth = [
        season(62, 17, 800_000),
        season(68, 18, 2_500_000),
        season(74, 19, 9_000_000),
        season(79, 20, 22_000_000),
    ]
    assert pots(youth) == [76, 80, 85, 86]


def test_estimate_without_value_is_flagged():
    result = pot.estimate_potentials([season(62, 17), season(68, 18)])
    assert [(r["pot"], r["has_value"]) for r in result] == [(80, False), (82, False)]


def test_potential_equals_ovr_after_last_potential_age():
    veteran = [season(80, 29, 30_000_000), season(79, 30, 20_000_000), season(78, 31)]
    assert pots(veteran) == [80, 79, 78]


def test_seasons_without_ovr_or_age_have_no_estimate():
    seasons = [{"ovr": None, "age": 20}, {"ovr": 70, "age": None}, season(70, 20)]
    result = pot.estimate_potentials(seasons)
    assert result[:2] == [None, None]
    assert result[2] == {"pot": 81, "has_value": False}


def test_goalkeepers_are_estimated_with_their_own_signal():
    keepers = [
        season(60, 18, 500_000, "GK", 20, 8, 0),
        season(66, 19, 1_500_000, "GK", 30, 12, 0),
    ]
    assert pots(keepers) == [72, 77]


def test_default_position_is_used_when_season_has_none():
    row = {"ovr": 66, "age": 19, "value_eur": 1_500_000, "matches": 30, "goals": 12}
    assert pots([{**row, "assists": 0}], default_position="GK") == [78]


def test_missing_numbers_in_dataframe_style_nan_are_ignored():
    row = season(70, 20, float("nan"), matches=float("nan"), goals=float("nan"))
    result = pot.estimate_potentials([row])
    assert result[0]["has_value"] is False
    assert 70 <= result[0]["pot"] <= 99


def test_very_high_rating_is_capped_at_99():
    assert pots([season(95, 21, 150_000_000)]) == [95]


@pytest.mark.parametrize("position", ["ST", "GK"])
@pytest.mark.parametrize("value", [None, 100_000, 5_000_000, 100_000_000])
def test_potential_is_always_between_ovr_and_99(position, value):
    for ovr in range(40, 96, 5):
        for age in range(16, 36):
            result = pot.estimate_potentials([season(ovr, age, value, position)])[0]
            assert ovr <= result["pot"] <= 99
            if age > pot.LAST_POTENTIAL_AGE:
                assert result["pot"] == ovr


@pytest.mark.parametrize("ovr", [55, 70])
def test_potential_gap_shrinks_with_age_for_typical_players(ovr):
    gaps = [pots([season(ovr, age)])[0] - ovr for age in range(16, 30)]
    assert gaps == sorted(gaps, reverse=True)


# ---------- uczenie modelu z bazy ----------


def make_player(start_ovr, growth, first_age=18, first_season="2020/21"):
    """Zawodnik z kolejnymi sezonami (wiek rośnie o 1, OVR wg listy przyrostów)."""
    seasons, ovr, label = [], start_ovr, first_season
    for i, step in enumerate([0, *growth]):
        ovr += step
        seasons.append(
            {**season(ovr, first_age + i, 400_000 * (1 + i)), "season": label}
        )
        label = next_season(label)
    return seasons


GROWTH = [3, 3, 2, 2, 1, 1, 1, 0, 0]  # sezony w wieku 18-27


def mature_players(count):
    return [(make_player(52 + 2 * i, GROWTH), "ST") for i in range(count)]


def test_empty_model_is_inactive_and_does_not_correct():
    model = pot.train_model([])
    assert not model.active
    assert (model.mature_players, model.samples) == (0, 0)
    assert model.correction([1, 2, 3, 4, 5, 6]) == 0.0


def test_too_few_mature_players_keep_model_inactive():
    model = pot.train_model(mature_players(pot.MIN_TRAIN_PLAYERS - 1))
    assert not model.active
    assert model.mature_players == pot.MIN_TRAIN_PLAYERS - 1


def test_young_players_are_not_counted_as_mature():
    young = [(make_player(55, [3, 3, 2], first_age=17), "ST") for _ in range(10)]
    model = pot.train_model(young)
    assert model.mature_players == 0
    assert not model.active


def test_enough_mature_players_activate_the_model():
    model = pot.train_model(mature_players(8))
    assert model.active
    assert len(model.coef) == 6
    assert model.mature_players == 8
    assert model.samples == 8 * (len(GROWTH) + 1)


def test_correction_is_clamped():
    model = pot.PotentialModel(coef=(100.0,) * 6)
    assert model.correction([1.0] * 6) == pot.CORRECTION_LIMIT
    assert model.correction([-1.0] * 6) == -pot.CORRECTION_LIMIT
    assert model.correction(None) == 0.0


def test_estimates_with_active_model_stay_in_bounds():
    model = pot.train_model(mature_players(8))
    youth = [
        season(60, 18, 600_000),
        season(66, 19, 2_000_000),
        season(71, 20, 6_000_000),
    ]
    for row, estimate in zip(youth, pots(youth, model=model), strict=True):
        assert row["ovr"] <= estimate <= 99


def test_train_from_rows_matches_train_model():
    players = mature_players(7)
    rows, starts = [], {}
    for pid, (seasons, position) in enumerate(players, start=1):
        starts[pid] = position
        rows.extend({**s, "player_id": pid} for s in seasons)
    from_rows = pot.train_from_rows(rows, starts)
    direct = pot.train_model(players)
    assert from_rows.mature_players == direct.mature_players
    assert from_rows.samples == direct.samples
    assert from_rows.coef == pytest.approx(direct.coef)
