"""Application service for fixed-point complement arithmetic."""
from ..domain.fixed_point import compute
from ..domain.models import FixedPointResult


def add_sub(value_x: str, value_y: str, width: int = 8, double_sign: bool = False,
            operation: str = "add", is_fraction: bool = False) -> FixedPointResult:
    return compute(value_x, value_y, width, double_sign, operation, is_fraction)
