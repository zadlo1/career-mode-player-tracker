import importlib
import re

import careertracker


def test_version_has_semver_format():
    assert re.fullmatch(r"\d+\.\d+\.\d+.*", careertracker.__version__)


def test_subpackages_import():
    for name in ("domain", "db", "services", "web"):
        assert importlib.import_module(f"careertracker.{name}")