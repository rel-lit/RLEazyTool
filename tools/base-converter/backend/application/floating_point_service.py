"""Application service for floating-point addition/subtraction."""
from ..domain.floating_point import compute
from ..domain.models import FloatingPointResult


def add_sub(x_mantissa: str, x_exponent: str, y_mantissa: str, y_exponent: str,
            operation: str = "add", exponent_width: int = 6, mantissa_width: int = 7) -> FloatingPointResult:
    return compute(x_mantissa, x_exponent, y_mantissa, y_exponent, operation, exponent_width, mantissa_width)
