import pytest
from backend.domain.machine_number import convert_machine_number


def test_positive_integer():
    res = convert_machine_number("13", width=8)
    assert res.sign_magnitude == "00001101"
    assert res.ones_complement == "00001101"
    assert res.twos_complement == "00001101"
    assert res.offset_binary == "10001101"


def test_negative_integer():
    res = convert_machine_number("-13", width=8)
    assert res.sign_magnitude == "10001101"
    assert res.ones_complement == "11110010"
    assert res.twos_complement == "11110011"


def test_negative_fraction():
    res = convert_machine_number("-0.625", width=8, is_fraction=True)
    # 0.625 = 0.101
    assert res.sign_magnitude == "11010000"
    assert res.twos_complement == "10110000"


def test_double_sign():
    res = convert_machine_number("-13", width=8, double_sign=True)
    assert res.sign_magnitude.startswith("11")
    assert res.twos_complement.startswith("11")


def test_out_of_range():
    with pytest.raises(ValueError):
        convert_machine_number("300", width=8)


def test_auto_detect_fraction():
    # Entering a decimal value without is_fraction should auto-switch to fraction mode
    res = convert_machine_number("-0.625", width=8, is_fraction=False)
    assert res.is_fraction is True
    assert res.twos_complement == "10110000"
