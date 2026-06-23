"""Fixed-point two's complement addition and subtraction with overflow detection."""
from typing import List, Tuple
from .models import FixedPointResult, Step, HighlightRange
from .machine_number import convert_machine_number, _parse_decimal


def _binary_add(a: str, b: str) -> Tuple[str, str]:
    """Add two binary strings of equal length. Return (sum, carries_string)."""
    if len(a) != len(b):
        raise ValueError("二进制位数不一致")
    result = []
    carries = []
    carry = 0
    for i in range(len(a) - 1, -1, -1):
        total = int(a[i]) + int(b[i]) + carry
        result.append(str(total % 2))
        carry = total // 2
        carries.append(str(carry))
    sum_str = "".join(reversed(result))
    carry_str = "".join(reversed(carries))
    return sum_str, carry_str


def _negate_complement(comp: str) -> str:
    """Compute [-y]补 from [y]补: invert all bits and add 1."""
    inverted = "".join("1" if c == "0" else "0" for c in comp)
    carry = 1
    result = []
    for ch in reversed(inverted):
        total = int(ch) + carry
        result.append(str(total % 2))
        carry = total // 2
    return "".join(reversed(result))[-len(comp):]


def _comp_to_decimal(comp: str, width: int, is_fraction: bool, double_sign: bool) -> str:
    """Convert a two's complement bit string back to decimal string."""
    if double_sign:
        sign_bits = comp[:2]
        mag_bits = comp[2:]
        if sign_bits == "00":
            sign = 1
        elif sign_bits == "11":
            sign = -1
        else:
            return "溢出"
        # Two's complement value
        value = int(comp, 2)
        if sign == -1:
            value = value - (2 ** width)
    else:
        value = int(comp, 2)
        if comp[0] == "1":
            value = value - (2 ** width)

    if is_fraction:
        scale = 2 ** (width - (2 if double_sign else 1))
        return str(value / scale)
    return str(value)


def compute(value_x: str, value_y: str, width: int = 8, double_sign: bool = False,
            operation: str = "add", is_fraction: bool = False) -> FixedPointResult:
    if operation not in ("add", "sub"):
        raise ValueError("运算只能是 add 或 sub")

    # Auto-detect fraction mode if any operand has a decimal part
    _, x_abs = _parse_decimal(value_x)
    _, y_abs = _parse_decimal(value_y)
    if not is_fraction and (x_abs != int(x_abs) or y_abs != int(y_abs)):
        is_fraction = True

    x_res = convert_machine_number(value_x, width, is_fraction, double_sign)
    y_res = convert_machine_number(value_y, width, is_fraction, double_sign)

    x_comp = x_res.twos_complement
    y_comp = y_res.twos_complement
    neg_y_comp = _negate_complement(y_comp)

    operand_b = y_comp if operation == "add" else neg_y_comp
    result_comp, carries = _binary_add(x_comp, operand_b)

    # Overflow detection
    overflow = False
    overflow_method = ""
    if double_sign:
        sign_bits = result_comp[:2]
        if sign_bits == "01":
            overflow = True
            overflow_method = "变形补码：结果符号位为 01，正溢出"
        elif sign_bits == "10":
            overflow = True
            overflow_method = "变形补码：结果符号位为 10，负溢出"
        else:
            overflow_method = "变形补码：结果符号位为 00 或 11，无溢出"
    else:
        # Single sign bit: compare carry into sign and carry out of sign
        # carries string aligns with bit positions from MSB to LSB; sign is position 0
        carry_into_sign = carries[1] if len(carries) > 1 else "0"
        carry_out_of_sign = carries[0]
        if carry_into_sign != carry_out_of_sign:
            overflow = True
            overflow_method = f"单符号位：符号位进位 ({carry_into_sign}) ≠ 最高数值位进位 ({carry_out_of_sign})，溢出"
        else:
            overflow_method = f"单符号位：符号位进位 ({carry_into_sign}) = 最高数值位进位 ({carry_out_of_sign})，无溢出"

    result_decimal = _comp_to_decimal(result_comp, width, is_fraction, double_sign) if not overflow else "溢出，无有效真值"

    sign_len = 2 if double_sign else 1
    mag_len = width - sign_len

    steps: List[Step] = []
    steps.append(
        Step(
            title=f"Step 1：求 [x]补",
            description=f"x = {value_x} 的{'变形' if double_sign else ''}补码",
            bits=x_comp,
            bit_groups=[
                HighlightRange(0, sign_len, label="符号", color="sign"),
                HighlightRange(sign_len, width, label="数值", color="magnitude"),
            ],
        )
    )
    steps.append(
        Step(
            title=f"Step 2：求 [y]补" + (" 及 [-y]补" if operation == "sub" else ""),
            description=f"y = {value_y} 的{'变形' if double_sign else ''}补码" +
                        ("；减法需将其连同符号位一起取反加 1 得到 [-y]补" if operation == "sub" else ""),
            bits=y_comp,
            bit_groups=[
                HighlightRange(0, sign_len, label="符号", color="sign"),
                HighlightRange(sign_len, width, label="数值", color="magnitude"),
            ],
        )
    )
    if operation == "sub":
        steps.append(
            Step(
                title="Step 2b：[-y]补",
                description="[y]补 连同符号位取反加 1",
                bits=neg_y_comp,
                bit_groups=[
                    HighlightRange(0, sign_len, label="符号", color="sign"),
                    HighlightRange(sign_len, width, label="数值", color="magnitude"),
                ],
            )
        )

    op_label = "加" if operation == "add" else "减"
    steps.append(
        Step(
            title=f"Step 3：执行 [x]补 {op_label} [y]补",
            description=f"{x_comp} + {operand_b} = {result_comp}",
            bits=result_comp,
            bit_groups=[
                HighlightRange(0, sign_len, label="符号", color="sign"),
                HighlightRange(sign_len, width, label="数值", color="magnitude"),
            ],
        )
    )

    steps.append(
        Step(
            title="Step 4：溢出判断",
            description=overflow_method,
        )
    )

    steps.append(
        Step(
            title="Step 5：结果",
            description=f"结果补码：{result_comp}，真值：{result_decimal}",
            bits=result_comp,
        )
    )

    return FixedPointResult(
        x=value_x,
        y=value_y,
        width=width,
        double_sign=double_sign,
        operation=operation,
        x_comp=x_comp,
        y_comp=y_comp,
        neg_y_comp=neg_y_comp,
        result_comp=result_comp,
        overflow=overflow,
        overflow_method=overflow_method,
        result_decimal=result_decimal,
        steps=steps,
    )
