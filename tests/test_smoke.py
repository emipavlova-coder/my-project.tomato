"""Scaffold smoke test: the package and its modules import cleanly.

Keeps `pytest` green at the scaffold stage. Real module tests are added
one at a time in Step 2.
"""
import importlib


def test_package_version():
    import tomato_coach

    assert tomato_coach.__version__ == "0.1.0"


def test_modules_importable():
    for name in ("data", "advisor", "app"):
        importlib.import_module(f"tomato_coach.{name}")
