"""Application service for machine number representations."""
from ..domain.machine_number import convert_machine_number
from ..domain.models import MachineNumberResult


def convert(value: str, width: int = 8, is_fraction: bool = False, double_sign: bool = False) -> MachineNumberResult:
    return convert_machine_number(value, width, is_fraction, double_sign)
