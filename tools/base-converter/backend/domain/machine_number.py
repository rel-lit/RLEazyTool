"""Machine number representations: sign-magnitude, 1's/2's complement, offset binary."""
from typing import List, Tuple
from .models import MachineNumberResult, Step, HighlightRange


def _parse_decimal(value: str) -> Tuple[bool, float]:
    """Return (is_negative, absolute_value as float)."""
    value = value.strip()
    if not value:
        raise ValueError("输入为空")
    negative = value.startswith("-")
    if negative:
        value = value[1:]
    if not value:
        raise ValueError("仅包含负号")
    try:
        num = float(value)
    except ValueError:
        raise ValueError("请输入合法的十进制数")
    if num < 0:
        raise ValueError("输入包含多余符号")
    return negative, num


def _fraction_to_binary(numerator: int, denominator: int, bits: int) -> Tuple[str, bool]:
    """Convert a fraction numerator/denominator to binary with given bits.
    Returns (binary_string, exact)."""
    if numerator == 0:
        return "0" * bits, True
    result = []
    seen = {}
    exact = True
    n = numerator
    pos = 0
    while pos < bits:
        if n == 0:
            result.append("0" * (bits - pos))
            break
        if n in seen:
            exact = False
            break
        seen[n] = pos
        n *= 2
        bit = n // denominator
        n = n % denominator
        result.append(str(bit))
        pos += 1
    if len("".join(result)) < bits:
        exact = False
    return "".join(result)[:bits], exact


def _integer_to_binary(value: int, bits: int) -> str:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value >= 2 ** bits:
        raise ValueError(f"数值超出 {bits} 位能表示的范围")
    return format(value, f"0{bits}b")


def _add_one(binary: str) -> str:
    """Add 1 to a binary string."""
    result = []
    carry = 1
    for ch in reversed(binary):
        total = int(ch) + carry
        result.append(str(total % 2))
        carry = total // 2
    if carry:
        result.append("1")
    return "".join(reversed(result))[-len(binary):]


def _flip_bits(binary: str) -> str:
    return "".join("1" if c == "0" else "0" for c in binary)


def _build_codes(sign: str, magnitude: str, width: int, double_sign: bool) -> Tuple[str, str, str]:
    """Build sign-magnitude, 1's comp, 2's comp from sign bit(s) and magnitude."""
    if double_sign:
        sign_bits = "11" if sign == "1" else "00"
        mag_width = width - 2
    else:
        sign_bits = sign
        mag_width = width - 1

    if len(magnitude) > mag_width:
        raise ValueError(f"数值超出 {width} 位{'变形补码' if double_sign else ''}能表示的范围")
    mag = magnitude.zfill(mag_width)

    sign_mag = sign_bits + mag
    if sign == "0":
        ones = sign_bits + mag
        twos = sign_bits + mag
    else:
        ones = sign_bits + _flip_bits(mag)
        twos = sign_bits + _add_one(_flip_bits(mag))
    return sign_mag, ones, twos


def _offset_binary(value: int, width: int) -> str:
    offset = 2 ** (width - 1)
    biased = value + offset
    if biased < 0 or biased >= 2 ** width:
        raise ValueError(f"数值超出 {width} 位移码能表示的范围")
    return format(biased, f"0{width}b")


def _value_to_binary_parts(negative: bool, abs_value: float, width: int, is_fraction: bool, double_sign: bool) -> Tuple[str, str, str, bool]:
    """Return (sign_bit, magnitude_bits, decimal_str, exact)."""
    sign = "1" if negative else "0"
    mag_bits = width - 2 if double_sign else width - 1

    if is_fraction:
        if abs_value >= 1:
            raise ValueError("纯小数必须满足 |x| < 1")
        # Convert decimal fraction to integer numerator/denominator
        frac_str = str(abs_value)
        if "." in frac_str:
            frac_len = len(frac_str.split(".")[1])
        else:
            frac_len = 0
        numerator = int(round(abs_value * (10 ** frac_len)))
        denominator = 10 ** frac_len
        mag, exact = _fraction_to_binary(numerator, denominator, mag_bits)
        decimal_repr = f"{'-' if negative else ''}{abs_value}"
    else:
        int_val = int(abs_value)
        if abs_value != int_val:
            raise ValueError("定点整数请输入整数")
        mag = _integer_to_binary(int_val, mag_bits)
        exact = True
        decimal_repr = f"{'-' if negative else ''}{int_val}"

    return sign, mag, decimal_repr, exact


def convert_machine_number(value: str, width: int = 8, is_fraction: bool = False, double_sign: bool = False) -> MachineNumberResult:
    if width < 2:
        raise ValueError("位宽至少为 2")
    if double_sign and width < 3:
        raise ValueError("变形补码位宽至少为 3")

    negative, abs_value = _parse_decimal(value)
    # Auto-detect fraction mode if the value contains a decimal part
    if not is_fraction and abs_value != int(abs_value):
        is_fraction = True

    sign, mag, decimal_repr, exact = _value_to_binary_parts(negative, abs_value, width, is_fraction, double_sign)

    sign_mag, ones, twos = _build_codes(sign, mag, width, double_sign)

    # Offset binary: based on the true integer value; if fraction, scale back to integer interpretation
    if is_fraction:
        # Interpret fraction as scaled integer: value * 2^(width-1)
        scale = 2 ** (width - 1)
        int_repr = int(round(abs_value * scale)) * (-1 if negative else 1)
    else:
        int_repr = int(decimal_repr)
    offset = _offset_binary(int_repr, width)

    # Build visualization steps
    steps: List[Step] = []
    sign_bits = "11" if (double_sign and sign == "1") else ("00" if double_sign else sign)
    sign_label = "符号位"
    mag_label = "数值位"

    steps.append(
        Step(
            title="Step 1：确定符号与数值",
            description=f"输入真值 {decimal_repr}，{'纯小数' if is_fraction else '定点整数'}，位宽 {width} 位" +
                        ("，采用双符号位" if double_sign else ""),
            bits=sign_bits + mag,
            bit_groups=[
                HighlightRange(0, len(sign_bits), label=sign_label, color="sign"),
                HighlightRange(len(sign_bits), len(sign_bits) + len(mag), label=mag_label, color="magnitude"),
            ],
        )
    )

    steps.append(
        Step(
            title="Step 2：原码",
            description="符号位 + 绝对值的二进制",
            bits=sign_mag,
            bit_groups=[
                HighlightRange(0, len(sign_bits), label="符号", color="sign"),
                HighlightRange(len(sign_bits), width, label="数值", color="magnitude"),
            ],
        )
    )

    if sign == "1":
        steps.append(
            Step(
                title="Step 3：反码",
                description="负数：符号位不变，数值位按位取反；正数与原码相同",
                bits=ones,
                bit_groups=[
                    HighlightRange(0, len(sign_bits), label="符号", color="sign"),
                    HighlightRange(len(sign_bits), width, label="取反后的数值", color="magnitude"),
                ],
            )
        )
        steps.append(
            Step(
                title="Step 4：补码",
                description="负数：反码末位加 1；正数与原码相同",
                bits=twos,
                bit_groups=[
                    HighlightRange(0, len(sign_bits), label="符号", color="sign"),
                    HighlightRange(len(sign_bits), width, label="加 1 后的数值", color="magnitude"),
                ],
            )
        )
    else:
        steps.append(
            Step(
                title="Step 3：反码",
                description="正数反码与原码相同",
                bits=ones,
            )
        )
        steps.append(
            Step(
                title="Step 4：补码",
                description="正数补码与原码相同",
                bits=twos,
            )
        )

    steps.append(
        Step(
            title="Step 5：移码",
            description=f"移码 = 真值 + 偏移量 2^{width-1}，再写成 {width} 位无符号二进制",
            bits=offset,
        )
    )

    note = None
    if not exact:
        note = f"注意：该小数无法用 {width} 位精确表示，已按位数截断"

    return MachineNumberResult(
        decimal=decimal_repr,
        width=width,
        is_fraction=is_fraction,
        sign_magnitude=sign_mag,
        ones_complement=ones,
        twos_complement=twos,
        offset_binary=offset,
        steps=steps,
        note=note,
    )
