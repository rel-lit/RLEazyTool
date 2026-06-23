import pytest
import math
from backend.domain.ieee754 import convert


def test_decimal_to_float32():
    res = convert("13.625", precision="float32", direction="to_ieee")
    assert res["bits"] == "01000001010110100000000000000000"
    assert res["hex"] == "0x415A0000"
    assert res["sign"] == "0"
    assert res["biased_exponent"] == 130
    assert res["unbiased_exponent"] == 3


def test_decimal_to_float64():
    res = convert("-13.625", precision="float64", direction="to_ieee")
    assert res["bits"].startswith("1")
    assert res["hex"] == "0xC02B400000000000"


def test_binary_to_decimal_float32():
    res = convert("01000001010110100000000000000000", precision="float32", direction="to_decimal")
    assert abs(res["decimal_value"] - 13.625) < 1e-6


def test_zero():
    res = convert("0.0", precision="float32", direction="to_ieee")
    assert res["bits"] == "0" * 32


def test_invalid_binary_length():
    with pytest.raises(ValueError):
        convert("0101", precision="float32", direction="to_decimal")


def test_nan():
    res = convert("nan", precision="float32", direction="to_ieee")
    assert math.isnan(res["decimal_value"])
