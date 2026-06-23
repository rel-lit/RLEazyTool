import pytest
from backend.domain.fixed_point import compute


def test_add_no_overflow():
    res = compute("5", "3", width=8, double_sign=False, operation="add")
    assert res.result_decimal == "8"
    assert not res.overflow


def test_sub_no_overflow():
    res = compute("5", "3", width=8, double_sign=False, operation="sub")
    assert res.result_decimal == "2"
    assert not res.overflow


def test_overflow_positive():
    res = compute("100", "50", width=8, double_sign=False, operation="add")
    assert res.overflow


def test_double_sign_overflow():
    # With width=8 double sign, range is [-64, 63]; 40+30=70 overflows
    res = compute("40", "30", width=8, double_sign=True, operation="add")
    assert res.overflow
    assert "01" in res.overflow_method or "10" in res.overflow_method


def test_fraction_add():
    res = compute("0.5", "0.25", width=8, is_fraction=True, operation="add")
    assert res.result_decimal == "0.75"


def test_auto_detect_fraction():
    # Entering decimal operands without is_fraction should auto-switch
    res = compute("0.5", "0.25", width=8, is_fraction=False, operation="add")
    assert res.result_decimal == "0.75"
