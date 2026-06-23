"""Application service for base conversion."""
from ..domain.base_conversion import convert
from ..domain.models import BaseConversionResult


def convert_base(value: str, from_base: int, to_base: int, precision: int = 8) -> BaseConversionResult:
    return convert(value, from_base, to_base, precision)
