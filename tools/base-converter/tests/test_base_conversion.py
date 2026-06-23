import pytest
from backend.domain.base_conversion import convert


def test_decimal_to_binary_integer():
    res = convert("13", 10, 2)
    assert res.result == "1101"


def test_decimal_to_binary_fraction():
    res = convert("13.625", 10, 2)
    assert res.result == "1101.101"


def test_binary_to_decimal():
    res = convert("1101.101", 2, 10)
    assert res.result == "13.625"


def test_binary_to_hex():
    res = convert("1101011.101", 2, 16)
    assert res.result == "6B.A"


def test_hex_to_binary():
    res = convert("6B.A", 16, 2)
    # Each hex digit expands to 4 bits; teaching display keeps leading zeros
    assert res.result == "01101011.1010"


def test_negative_decimal_to_binary():
    res = convert("-13", 10, 2)
    assert res.result == "-1101"


def test_fraction_precision():
    res = convert("0.1", 10, 2, precision=4)
    assert res.result.startswith("0.0001")
    assert res.note is not None


def test_zero():
    res = convert("0", 10, 2)
    assert res.result == "0"


def test_invalid_digit():
    with pytest.raises(ValueError):
        convert("12", 2, 10)
