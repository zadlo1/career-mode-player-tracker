"""Dopasowuje model potencjału do pliku CSV z zawodnikami gry (kolumny jak w zbiorze FC26 z Kaggle/GitHub).

Użycie: python tools/fit_potential_model.py FC26.csv [data_odniesienia]
Wynik: potential_coefs.py (współczynniki używane przez potential.py).
"""
import sys
from datetime import date

import numpy as np
import pandas as pd

AGE_POWERS = 4


def design(age, ovr, ln_value, gk, with_value):
    a = (np.asarray(age) - 22) / 4
    o = (np.asarray(ovr) - 65) / 10
    g = np.asarray(gk)
    if with_value:
        v = (np.asarray(ln_value) - 13.5) / 2
        base = [np.ones_like(o), o, v, g, o * o, v * v, o * v]
    else:
        base = [np.ones_like(o), o, g, o * o]
    cols = []
    for power in range(AGE_POWERS):
        cols += [b * a**power for b in base]
    return np.column_stack(cols)


def main():
    path = sys.argv[1]
    ref = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2025, 7, 1)
    d = pd.read_csv(path, low_memory=False)
    d = d[d.overall.notna() & d.potential.notna() & d.dob.notna()].copy()
    d["age_exact"] = (pd.Timestamp(ref) - pd.to_datetime(d.dob)).dt.days / 365.25
    d = d[(d.age_exact >= 15.5) & (d.age_exact <= 29.5)]
    d["gk"] = d.player_positions.str.contains("GK").astype(int)
    d["gap"] = d.potential - d.overall
    with_value = d[d.value_eur > 0]

    c_val = np.linalg.lstsq(
        design(with_value.age_exact, with_value.overall, np.log(with_value.value_eur), with_value.gk, True),
        with_value.gap.values, rcond=None)[0]
    c_no = np.linalg.lstsq(design(d.age_exact, d.overall, 0, d.gk, False), d.gap.values, rcond=None)[0]

    with open("potential_coefs.py", "w", encoding="utf-8") as f:
        f.write(f"# wygenerowane przez tools/fit_potential_model.py ({len(with_value)} zawodników, stan na {ref})\n")
        f.write(f"WITH_VALUE = {[round(float(x), 6) for x in c_val]}\n")
        f.write(f"WITHOUT_VALUE = {[round(float(x), 6) for x in c_no]}\n")
    print("zapisano potential_coefs.py")


if __name__ == "__main__":
    main()