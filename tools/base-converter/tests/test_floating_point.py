import pytest
from backend.domain.floating_point import compute


def test_pdf_example_add():
    # x = +0.110101 × 2^+0011
    # y = -0.111010 × 2^+0010
    res = compute(
        x_mantissa="+0.110101", x_exponent="+0011",
        y_mantissa="-0.111010", y_exponent="+0010",
        operation="add", exponent_width=6, mantissa_width=7
    )
    assert res.normalized == "[000010 , 0.110000]"
    assert res.final == "+0.110000 × 2^2"
    assert not res.overflow


def test_float_sub():
    res = compute(
        x_mantissa="+0.110000", x_exponent="+0010",
        y_mantissa="+0.010000", y_exponent="+0001",
        operation="sub", exponent_width=6, mantissa_width=7
    )
    assert not res.overflow
