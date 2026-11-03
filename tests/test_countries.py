import re
from pathlib import Path

import pytest

import careertracker
from careertracker.domain.countries import (
    CODES,
    COUNTRIES,
    NAME_TO_CODE,
    country_name,
)

FLAGS_DIR = Path(careertracker.__file__).parent / "web" / "static" / "flags"


def test_codes_have_expected_format():
    for code in COUNTRIES:
        assert re.fullmatch(r"[A-Z]{2}(-[A-Z]{3})?", code), code


def test_names_are_filled_and_unique():
    names = list(COUNTRIES.values())
    assert all(name.strip() for name in names)
    assert len(names) == len(set(names))


def test_home_nations_are_separate_countries():
    assert COUNTRIES["GB-ENG"] == "Anglia"
    assert COUNTRIES["GB-SCT"] == "Szkocja"
    assert COUNTRIES["GB-WLS"] == "Walia"
    assert COUNTRIES["GB-NIR"] == "Irlandia Północna"
    assert "GB" not in COUNTRIES


@pytest.mark.parametrize(
    ("name", "code"),
    [("tunezja", "TN"), ("polska", "PL"), ("usa", "US"), ("anglia", "GB-ENG")],
)
def test_name_lookup_is_lowercase(name, code):
    assert NAME_TO_CODE[name] == code


def test_country_name_known_and_unknown():
    assert country_name("TN") == "Tunezja"
    assert country_name("ZZ") == "ZZ"


def test_codes_contain_every_country_once():
    assert sorted(CODES) == sorted(COUNTRIES)


def test_codes_are_sorted_with_polish_letters_as_base_letters():
    # "Litwa" < "Łotwa" < "Luksemburg", a nie "Ł" na końcu alfabetu
    assert CODES.index("LT") < CODES.index("LV") < CODES.index("LU")
    assert CODES.index("PL") < CODES.index("PT")


def test_every_country_has_a_flag_file():
    missing = [c for c in COUNTRIES if not (FLAGS_DIR / f"{c.lower()}.svg").exists()]
    assert missing == []


def test_every_flag_file_belongs_to_a_country():
    flags = {p.stem.upper() for p in FLAGS_DIR.glob("*.svg")}
    assert flags - set(COUNTRIES) == set()


def test_flag_files_are_svg():
    for code in ("PL", "GB-ENG", "TN"):
        assert "<svg" in (FLAGS_DIR / f"{code.lower()}.svg").read_text(encoding="utf-8")


def test_flag_license_is_kept_next_to_flags():
    assert (FLAGS_DIR / "LICENSE-flag-icons.txt").exists()
