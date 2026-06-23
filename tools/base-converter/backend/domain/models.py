"""Domain models shared across base-converter modules."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class HighlightRange:
    """A half-open range [start, end) to highlight in a bit string."""
    start: int
    end: int
    label: str = ""
    color: str = ""


@dataclass(frozen=True)
class BitPattern:
    """A labeled bit pattern for side-by-side display."""
    label: str
    bits: str
    groups: List[HighlightRange] = field(default_factory=list)


@dataclass(frozen=True)
class Step:
    """One visualization step of a calculation process."""
    title: str
    description: str = ""
    table: List[List[str]] = field(default_factory=list)
    table_headers: List[str] = field(default_factory=list)
    bits: str = ""
    bit_groups: List[HighlightRange] = field(default_factory=list)
    bit_patterns: List[BitPattern] = field(default_factory=list)
    note: str = ""


@dataclass(frozen=True)
class BaseConversionResult:
    source_value: str
    source_base: int
    target_base: int
    result: str
    steps: List[Step]
    note: Optional[str] = None


@dataclass(frozen=True)
class MachineNumberResult:
    decimal: str
    width: int
    is_fraction: bool
    sign_magnitude: str
    ones_complement: str
    twos_complement: str
    offset_binary: str
    steps: List[Step]
    note: Optional[str] = None


@dataclass(frozen=True)
class FixedPointResult:
    x: str
    y: str
    width: int
    double_sign: bool
    operation: str  # "add" or "sub"
    x_comp: str
    y_comp: str
    neg_y_comp: str
    result_comp: str
    overflow: bool
    overflow_method: str
    result_decimal: str
    steps: List[Step]
    note: Optional[str] = None


@dataclass(frozen=True)
class FloatingPointResult:
    x: str
    y: str
    operation: str  # "add" or "sub"
    exponent_width: int
    mantissa_width: int
    x_machine: str
    y_machine: str
    aligned_y_machine: str
    mantissa_sum: str
    normalized: str
    final: str
    overflow: bool
    steps: List[Step]
    note: Optional[str] = None


@dataclass(frozen=True)
class ErrorResult:
    error: str
