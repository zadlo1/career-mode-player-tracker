import math
from dataclasses import dataclass

import numpy as np

from potential_coefs import WITH_VALUE, WITHOUT_VALUE
from ratings import POSITION_GROUPS

# Krzywa wartości: wartość rynkowa zawodnika w dojrzałym wieku rośnie wykładniczo wraz z OVR.
BASE_OVR = 60
BASE_VALUE = 200_000
VALUE_SLOPE = 0.231  # przyrost ln(wartości) na 1 punkt OVR

# Po 28. roku życia wartość spada niezależnie od OVR (używane tylko do cechy "nadwyżka wartości").
AGE_VALUE_FACTOR = {29: 0.93, 30: 0.80, 31: 0.65, 32: 0.50, 33: 0.40, 34: 0.30}
OLD_VALUE_FACTOR = 0.20

# Wiek w bazie to wiek na początek roku, a w grze (wzorce w potential_coefs.py) średnio pół roku więcej.
AGE_SHIFT = 0.5
MIN_MODEL_AGE, MAX_MODEL_AGE = 15.5, 29.5
MIN_LN_VALUE, MAX_LN_VALUE = math.log(10_000), math.log(250_000_000)

# Maksymalna realna różnica potencjał - OVR dla danego wieku.
MAX_GAP = {
    17: 30, 18: 28, 19: 25, 20: 22, 21: 18, 22: 15, 23: 12,
    24: 10, 25: 8, 26: 6, 27: 4, 28: 3, 29: 2,
}

# Typowy roczny przyrost OVR w danym wieku.
EXPECTED_GROWTH = {
    17: 4.5, 18: 4.0, 19: 3.5, 20: 3.0, 21: 2.5, 22: 2.0, 23: 1.5,
    24: 1.0, 25: 0.5, 26: 0.2, 27: 0.0, 28: 0.0, 29: -0.5,
}

TREND_WEIGHTS = (1.0, 0.6, 0.35)
TREND_GAIN = 0.5
TREND_LIMIT = 3.0
SMOOTHING = 0.25           # udział poprzedniej estymaty w nowej
LAST_POTENTIAL_AGE = 28

# Nauka z bazy: dojrzali zawodnicy pokazują, jak naprawdę skończył się rozwój.
MATURE_AGE = 26             # zawodnik z ostatnim sezonem w tym wieku lub starszym ma "wynik końcowy"
MIN_TRAIN_PLAYERS = 6
MIN_TRAIN_SAMPLES = 20
RIDGE = 6.0                 # im wyżej, tym wolniej model odchodzi od wzoru bazowego
CORRECTION_LIMIT = 6.0      # maksymalna korekta wzoru w punktach
FULL_SEASON_MATCHES = 40
TYPICAL_OUTPUT = {"GK": 0.35, "DEF": 0.12, "MID": 0.35, "ATT": 0.7}  # (G+A) lub CS na mecz


def base_value(ovr: float) -> float:
    return BASE_VALUE * math.exp(VALUE_SLOPE * (ovr - BASE_OVR))


def _age_value_factor(age: int) -> float:
    if age <= 28:
        return 1.0
    return AGE_VALUE_FACTOR.get(age, OLD_VALUE_FACTOR)


def _lookup(table: dict, age: int, default_low: float, default_high: float) -> float:
    if age in table:
        return table[age]
    return default_low if age < min(table) else default_high


def max_gap(age: int) -> float:
    return _lookup(MAX_GAP, age, MAX_GAP[17], 0)


def expected_growth(age: int) -> float:
    if age > 29:
        return -1.0 - 0.5 * (age - 30)
    return _lookup(EXPECTED_GROWTH, age, EXPECTED_GROWTH[17], -0.5)


def _design(age: float, ovr: float, ln_value: float, gk: int, with_value: bool) -> list:
    a = (age - 22) / 4
    o = (ovr - 65) / 10
    if with_value:
        v = (ln_value - 13.5) / 2
        base = [1.0, o, v, float(gk), o * o, v * v, o * v]
    else:
        base = [1.0, o, float(gk), o * o]
    return [b * a**power for power in range(4) for b in base]


def value_signal(ovr: float, age: int, value, is_gk: bool = False):
    """Zwraca (różnica POT - OVR z modelu dopasowanego do zawodników gry, nadwyżka wartości w pkt OVR)."""
    age_eff = min(max(age + AGE_SHIFT, MIN_MODEL_AGE), MAX_MODEL_AGE)
    ovr_c = min(max(ovr, 40), 92)
    has_value = value is not None and value > 0
    if has_value:
        ln_value = min(max(math.log(value), MIN_LN_VALUE), MAX_LN_VALUE)
        coef, features = WITH_VALUE, _design(age_eff, ovr_c, ln_value, int(is_gk), True)
        expected = base_value(ovr) * _age_value_factor(age)
        extra = math.log(value / expected) / VALUE_SLOPE
    else:
        coef, features = WITHOUT_VALUE, _design(age_eff, ovr_c, 0.0, int(is_gk), False)
        extra = 0.0
    gap = float(np.dot(coef, features))
    return max(0.0, gap), extra


def development_trend(history: list) -> float:
    """Średnia nadwyżka wzrostu OVR ponad typowy wzrost dla wieku (z ostatnich przejść)."""
    surpluses = []
    for prev, cur in zip(history, history[1:]):
        years = max(1, cur["age"] - prev["age"])
        expected = sum(expected_growth(prev["age"] + i) for i in range(years))
        surpluses.append((cur["ovr"] - prev["ovr"]) - expected)
    recent = surpluses[::-1][: len(TREND_WEIGHTS)]
    if not recent:
        return 0.0
    weights = TREND_WEIGHTS[: len(recent)]
    return sum(w * s for w, s in zip(weights, recent)) / sum(weights)


def _num(value):
    if value is None or value != value:
        return None
    return value


def _play_features(season: dict, position):
    """Czas gry i skuteczność w sezonie względem typowej dla pozycji."""
    matches = _num(season.get("matches")) or 0
    playtime = min(matches, 50) / FULL_SEASON_MATCHES - 0.75
    group = POSITION_GROUPS.get(str(position).upper(), "MID")
    output = 0.0
    if matches >= 5:
        goals = _num(season.get("goals")) or 0
        assists = _num(season.get("assists")) or 0
        total = goals if group == "GK" else goals + assists
        output = max(-1.0, min(2.0, (total / matches) / TYPICAL_OUTPUT[group] - 1))
    return playtime, output


def _analyze(seasons: list, default_position=None) -> list:
    """Dla każdego sezonu: cechy i bazowa różnica POT - OVR (bez modelu i wygładzania)."""
    results = []
    history = []
    for s in seasons:
        ovr, age, value = _num(s.get("ovr")), _num(s.get("age")), _num(s.get("value_eur"))
        if ovr is None or age is None:
            results.append(None)
            continue

        ovr, age = int(ovr), int(age)
        history.append({"ovr": ovr, "age": age})
        item = {"ovr": ovr, "age": age, "has_value": value is not None and value > 0,
                "base_gap": 0.0, "features": None}

        if age <= LAST_POTENTIAL_AGE:
            position = s.get("position") or default_position
            gap, extra = value_signal(ovr, age, value, str(position).upper() == "GK")
            youth = min(1.0, (LAST_POTENTIAL_AGE + 1 - age) / 8)
            trend = development_trend(history)
            adjustment = max(-TREND_LIMIT, min(TREND_LIMIT, TREND_GAIN * trend * youth))
            gap = max(0.0, min(gap + adjustment, max_gap(age)))
            playtime, output = _play_features(s, position)
            raw = [gap / 10, max(-5.0, min(15.0, extra)) / 5, trend / 3, playtime, output, 1.0]
            item["base_gap"] = gap
            item["features"] = [youth * x for x in raw]
        results.append(item)
    return results


@dataclass
class PotentialModel:
    coef: tuple = None
    mature_players: int = 0
    samples: int = 0

    @property
    def active(self) -> bool:
        return self.coef is not None

    def correction(self, features) -> float:
        if not self.active or features is None:
            return 0.0
        value = float(np.dot(self.coef, features))
        return max(-CORRECTION_LIMIT, min(CORRECTION_LIMIT, value))


def train_model(players_seasons: list) -> PotentialModel:
    """Uczy korektę wzoru bazowego na zawodnikach, którzy już skończyli rozwój.

    Wynik końcowy = najwyższy OVR osiągnięty od danego sezonu wzwyż.
    Brany jest tylko zawodnik, który ma sezon w wieku MATURE_AGE lub starszym.
    """
    rows, targets = [], []
    mature = 0
    for seasons, default_position in players_seasons:
        analyzed = _analyze(seasons, default_position)
        valid = [a for a in analyzed if a is not None]
        if not valid or valid[-1]["age"] < MATURE_AGE:
            continue
        mature += 1
        future_peak = 0
        for a in reversed(valid):
            future_peak = max(future_peak, a["ovr"])
            if a["features"] is None:
                continue
            rows.append(a["features"])
            targets.append((future_peak - a["ovr"]) - a["base_gap"])

    if mature < MIN_TRAIN_PLAYERS or len(rows) < MIN_TRAIN_SAMPLES:
        return PotentialModel(None, mature, len(rows))

    X = np.array(rows, dtype=float)
    y = np.array(targets, dtype=float)
    coef = np.linalg.solve(X.T @ X + RIDGE * np.eye(X.shape[1]), X.T @ y)
    return PotentialModel(tuple(coef), mature, len(rows))


def train_from_rows(season_rows: list, start_positions: dict) -> PotentialModel:
    by_player = {}
    for row in season_rows:
        by_player.setdefault(row["player_id"], []).append(row)
    data = [
        (sorted(rows, key=lambda r: r["season"]), start_positions.get(pid))
        for pid, rows in by_player.items()
    ]
    return train_model(data)


def estimate_potentials(seasons: list, default_position=None, model: PotentialModel = None) -> list:
    """Dla każdego sezonu (od najstarszego) zwraca {'pot': int, 'has_value': bool} albo None."""
    results = []
    previous = None

    for a in _analyze(seasons, default_position):
        if a is None:
            results.append(None)
            continue

        ovr, age = a["ovr"], a["age"]
        if age > LAST_POTENTIAL_AGE:
            pot = float(ovr)
        else:
            gap = a["base_gap"]
            if model is not None:
                gap += model.correction(a["features"])
            gap = max(0.0, min(gap, max_gap(age)))
            pot = ovr + gap
            if previous is not None:
                pot = (1 - SMOOTHING) * pot + SMOOTHING * previous

        pot = max(float(ovr), min(99.0, pot))
        previous = pot
        results.append({"pot": int(round(pot)), "has_value": a["has_value"]})

    return results