import math

# Krzywa wartości: wartość rynkowa zawodnika w dojrzałym wieku rośnie wykładniczo wraz z OVR.
BASE_OVR = 60
BASE_VALUE = 200_000
VALUE_SLOPE = 0.231  # przyrost ln(wartości) na 1 punkt OVR

# Po 28. roku życia wartość spada niezależnie od OVR.
AGE_VALUE_FACTOR = {29: 0.93, 30: 0.80, 31: 0.65, 32: 0.50, 33: 0.40, 34: 0.30}
OLD_VALUE_FACTOR = 0.20

# Jaką część "punktów ponad krzywą" wyjaśnia potencjał (reszta to wiek, kontrakt itp.).
YOUNG_WEIGHT = 0.5
OLD_WEIGHT = 0.3

# Maksymalna realna różnica potencjał - OVR dla danego wieku.
MAX_GAP = {
    17: 30, 18: 28, 19: 25, 20: 22, 21: 18, 22: 15, 23: 12,
    24: 10, 25: 8, 26: 6, 27: 4, 28: 3, 29: 2,
}

# Typowa różnica potencjał - OVR, gdy nie znamy wartości.
PRIOR_GAP = {
    17: 12, 18: 10, 19: 8, 20: 7, 21: 5.5, 22: 4, 23: 3,
    24: 2.5, 25: 2, 26: 1.5, 27: 1, 28: 0.5,
}

# Typowy roczny przyrost OVR w danym wieku.
EXPECTED_GROWTH = {
    17: 4.5, 18: 4.0, 19: 3.5, 20: 3.0, 21: 2.5, 22: 2.0, 23: 1.5,
    24: 1.0, 25: 0.5, 26: 0.2, 27: 0.0, 28: 0.0, 29: -0.5,
}

NO_VALUE_PRIOR_SHARE = 0.6  # bez wartości opieramy się tylko na wieku, ostrożniej
VALUE_SHARE = 0.8          # udział oceny z wartości względem typowej różnicy dla wieku
TREND_WEIGHTS = (1.0, 0.6, 0.35)
TREND_GAIN = 1.0
TREND_LIMIT = 5.0
SMOOTHING = 0.3            # udział poprzedniej estymaty w nowej
LAST_POTENTIAL_AGE = 28


def base_value(ovr: float) -> float:
    return BASE_VALUE * math.exp(VALUE_SLOPE * (ovr - BASE_OVR))


def _age_value_factor(age: int) -> float:
    if age <= 28:
        return 1.0
    return AGE_VALUE_FACTOR.get(age, OLD_VALUE_FACTOR)


def _potential_weight(age: int) -> float:
    if age <= 23:
        return YOUNG_WEIGHT
    return YOUNG_WEIGHT + (OLD_WEIGHT - YOUNG_WEIGHT) * (min(age, 28) - 23) / 5


def _lookup(table: dict, age: int, default_low: float, default_high: float) -> float:
    if age in table:
        return table[age]
    return default_low if age < min(table) else default_high


def max_gap(age: int) -> float:
    return _lookup(MAX_GAP, age, MAX_GAP[17], 0)


def prior_gap(age: int) -> float:
    return _lookup(PRIOR_GAP, age, PRIOR_GAP[17], 0)


def expected_growth(age: int) -> float:
    if age > 29:
        return -1.0 - 0.5 * (age - 30)
    return _lookup(EXPECTED_GROWTH, age, EXPECTED_GROWTH[17], -0.5)


def value_gap(ovr: float, age: int, value) -> float:
    """Różnica potencjał - OVR wynikająca z wartości rynkowej."""
    if value is None or value <= 0:
        return NO_VALUE_PRIOR_SHARE * prior_gap(age)
    expected = base_value(ovr) * _age_value_factor(age)
    extra_points = math.log(value / expected) / VALUE_SLOPE
    gap = max(0.0, extra_points / _potential_weight(age))
    return VALUE_SHARE * gap + (1 - VALUE_SHARE) * prior_gap(age)


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


def estimate_potentials(seasons: list) -> list:
    """Dla każdego sezonu (od najstarszego) zwraca {'pot': int, 'has_value': bool} albo None."""
    results = []
    history = []
    previous = None

    for s in seasons:
        ovr, age, value = _num(s.get("ovr")), _num(s.get("age")), _num(s.get("value_eur"))
        if ovr is None or age is None:
            results.append(None)
            continue

        ovr, age = int(ovr), int(age)
        history.append({"ovr": ovr, "age": age})
        if age > LAST_POTENTIAL_AGE:
            pot = float(ovr)
        else:
            gap = value_gap(ovr, age, value)
            youth = min(1.0, (LAST_POTENTIAL_AGE + 1 - age) / 8)
            trend = development_trend(history)
            adjustment = max(-TREND_LIMIT, min(TREND_LIMIT, TREND_GAIN * trend * youth))
            gap = max(0.0, min(gap + adjustment, max_gap(age)))
            pot = ovr + gap
            if previous is not None:
                pot = (1 - SMOOTHING) * pot + SMOOTHING * previous

        pot = max(float(ovr), min(99.0, pot))
        previous = pot
        results.append({"pot": int(round(pot)), "has_value": value is not None and value > 0})

    return results