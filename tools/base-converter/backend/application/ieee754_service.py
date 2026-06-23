"""Application service for IEEE 754 floating-point conversion."""
from ..domain.ieee754 import convert


def convert_float(value: str, precision: str = "float32", direction: str = "to_ieee") -> dict:
    return convert(value, precision, direction)
