"""Floating-point addition/subtraction as used in computer organization courses.

The representation follows the textbook convention:
- exponent: double-sign two's complement (变形补码) with exponent_width bits
- mantissa: single-sign two's complement with mantissa_width bits
"""
from typing import List, Tuple
from .models import FloatingPointResult, Step, HighlightRange, BitPattern


def _parse_signed_binary(value: str) -> Tuple[bool, str]:
    """Parse '+0.110101' or '-0.111010' into (negative, '0.110101')."""
    value = value.strip()
    negative = value.startswith("-")
    if negative:
        value = value[1:]
    elif value.startswith("+"):
        value = value[1:]
    if not value.startswith("0."):
        raise ValueError("尾数必须是形如 +0.110101 的二进制规格化小数")
    digits = set(value) - {".", "-", "+"}
    if not digits <= {"0", "1"}:
        raise ValueError("尾数只能包含 0 和 1")
    return negative, value


def _parse_exponent(exp: str) -> int:
    """Parse exponent as signed integer or binary string."""
    exp = exp.strip()
    negative = exp.startswith("-")
    if exp.startswith("+") or exp.startswith("-"):
        body = exp[1:]
    else:
        body = exp
    body = body.strip()
    if not body:
        raise ValueError("阶码为空")
    if set(body) <= {"0", "1"}:
        value = int(body, 2)
    else:
        value = int(body)
    return -value if negative else value


def _int_to_double_sign_comp(value: int, width: int) -> str:
    """Convert signed integer to double-sign two's complement."""
    if value >= 2 ** (width - 1):
        raise ValueError(f"阶码 {value} 超出 {width} 位变形补码范围")
    if value < -(2 ** (width - 1)):
        raise ValueError(f"阶码 {value} 超出 {width} 位变形补码范围")
    if value >= 0:
        return "0" * 2 + format(value, f"0{width - 2}b")
    # negative
    raw = 2 ** width + value
    return format(raw, f"0{width}b")


def _double_sign_comp_to_int(comp: str) -> int:
    width = len(comp)
    sign = comp[:2]
    val = int(comp, 2)
    if sign == "11":
        val -= 2 ** width
    return val


def _mantissa_to_comp(negative: bool, mag: str, width: int) -> str:
    """Convert signed binary fraction magnitude to single-sign two's complement.
    width includes the sign bit."""
    if len(mag) > width - 1:
        raise ValueError(f"尾数有效位超过 {width - 1} 位")
    mag = mag.ljust(width - 1, "0")  # pad with zeros after decimal
    if not negative:
        return "0" + mag
    # Negative: invert + 1
    inverted = "".join("1" if c == "0" else "0" for c in mag)
    carry = 1
    result = []
    for ch in reversed(inverted):
        total = int(ch) + carry
        result.append(str(total % 2))
        carry = total // 2
    return "1" + "".join(reversed(result))[-(width - 1):]


def _comp_to_mantissa(comp: str) -> Tuple[bool, str]:
    """Convert single-sign two's complement mantissa back to (negative, '0.xxx')."""
    width = len(comp)
    sign = comp[0]
    mag_bits = comp[1:]
    if sign == "0":
        return False, "0." + mag_bits
    # Negative
    inverted = "".join("1" if c == "0" else "0" for c in mag_bits)
    carry = 1
    result = []
    for ch in reversed(inverted):
        total = int(ch) + carry
        result.append(str(total % 2))
        carry = total // 2
    mag = "".join(reversed(result))[-(width - 1):]
    return True, "0." + mag


def _add_binary(a: str, b: str) -> Tuple[str, str]:
    """Add equal-length binary strings. Return (sum, carry_string MSB->LSB)."""
    if len(a) != len(b):
        raise ValueError("位数不一致")
    res = []
    carries = []
    carry = 0
    for i in range(len(a) - 1, -1, -1):
        total = int(a[i]) + int(b[i]) + carry
        res.append(str(total % 2))
        carry = total // 2
        carries.append(str(carry))
    return "".join(reversed(res)), "".join(reversed(carries))


def _shift_right_arith(comp: str, bits: int) -> Tuple[str, str]:
    """Arithmetic right shift of mantissa (including sign bit). Return (shifted, dropped_bits)."""
    if bits <= 0:
        return comp, ""
    sign = comp[0]
    body = comp[1:]
    if bits >= len(comp):
        return sign * len(comp), body
    dropped = body[-bits:] if bits <= len(body) else body
    shifted_body = sign * bits + body[:-bits]
    return sign + shifted_body, dropped


def _is_normalized(comp: str) -> bool:
    """Normalized if positive mantissa is 0.1xxx or negative is 1.0xxx (complement)."""
    if comp[0] == "0":
        return comp[1] == "1"
    else:
        return comp[1] == "0"


def _format_float(machine: str, exp_width: int) -> str:
    exp = machine[:exp_width]
    mant = machine[exp_width:]
    mant_with_point = mant[0] + "." + mant[1:] if mant else mant
    return f"[{exp} , {mant_with_point}]"


def _exp_mant_groups(exp_width: int, mantissa_width: int) -> List[HighlightRange]:
    return [
        HighlightRange(0, exp_width, label="阶码", color="exponent"),
        HighlightRange(exp_width, exp_width + mantissa_width, label="尾数", color="mantissa"),
    ]


def _sign_mag_groups(mantissa_width: int) -> List[HighlightRange]:
    return [
        HighlightRange(0, 1, label="符号", color="sign"),
        HighlightRange(1, mantissa_width, label="数值", color="magnitude"),
    ]


def compute(x_mantissa: str, x_exponent: str, y_mantissa: str, y_exponent: str,
            operation: str = "add", exponent_width: int = 6, mantissa_width: int = 7) -> FloatingPointResult:
    if operation not in ("add", "sub"):
        raise ValueError("operation 只能是 add 或 sub")

    x_neg, x_mag = _parse_signed_binary(x_mantissa)
    y_neg, y_mag = _parse_signed_binary(y_mantissa)
    x_exp = _parse_exponent(x_exponent)
    y_exp = _parse_exponent(y_exponent)

    # Mantissa for subtraction: flip y sign
    original_y_neg = y_neg
    if operation == "sub":
        y_neg = not y_neg

    x_comp = _mantissa_to_comp(x_neg, x_mag[2:], mantissa_width)
    y_comp = _mantissa_to_comp(y_neg, y_mag[2:], mantissa_width)
    x_exp_comp = _int_to_double_sign_comp(x_exp, exponent_width)
    y_exp_comp = _int_to_double_sign_comp(y_exp, exponent_width)

    x_machine = _format_float(x_exp_comp + x_comp, exponent_width)
    y_machine = _format_float(y_exp_comp + y_comp, exponent_width)

    steps: List[Step] = []

    # Step 1: x and y machine representations
    steps.append(
        Step(
            title="Step 1a：写出 [x]浮",
            description=f"x = {'-' if x_neg else '+'}{x_mag} × 2^{x_exp}\n" +
                        f"阶码 Ex = {x_exp}，双符号位补码：{x_exp_comp}\n" +
                        f"尾数 Mx = {x_mag}，单符号位补码：{_format_float(x_comp, 1)}\n" +
                        f"[x]浮 = {x_machine}",
            bits=x_exp_comp + x_comp,
            bit_groups=_exp_mant_groups(exponent_width, mantissa_width),
        )
    )
    steps.append(
        Step(
            title="Step 1b：写出 [y]浮",
            description=f"y = {'-' if original_y_neg else '+'}{y_mag} × 2^{y_exp}\n" +
                        (f"运算为减法，[-y]补 = {y_comp}（{y_mag} 取反加 1）\n" if operation == "sub" else "") +
                        f"阶码 Ey = {y_exp}，双符号位补码：{y_exp_comp}\n" +
                        f"[y]浮 = {y_machine}",
            bits=y_exp_comp + y_comp,
            bit_groups=_exp_mant_groups(exponent_width, mantissa_width),
        )
    )

    # Step 2: align exponents
    delta = x_exp - y_exp
    aligned_y_comp = y_comp
    aligned_y_exp_comp = y_exp_comp
    align_detail = ""
    dropped_bits = ""

    if delta == 0:
        align_detail = f"ΔE = Ex - Ey = {x_exp} - {y_exp} = 0，阶码相同，无需对阶。"
    elif delta > 0:
        # y exponent smaller, shift y right by delta, add delta to y exponent
        aligned_y_comp, dropped_bits = _shift_right_arith(y_comp, delta)
        new_y_exp = y_exp + delta
        aligned_y_exp_comp = _int_to_double_sign_comp(new_y_exp, exponent_width)
        align_detail = (
            f"ΔE = Ex - Ey = {x_exp} - {y_exp} = {delta} > 0，y 的阶码较小。\n"
            f"将 My 算术右移 {delta} 位，Ey 加 {delta}：\n"
            f"  原 My：{_format_float(y_comp, 1)}\n"
            f"  右移 {delta} 位后：{_format_float(aligned_y_comp, 1)}，移出位：{dropped_bits if dropped_bits else '无'}\n"
            f"  新 Ey = {y_exp} + {delta} = {new_y_exp}，补码：{aligned_y_exp_comp}"
        )
    else:
        # x exponent smaller, shift x right by -delta
        x_comp, dropped_bits_x = _shift_right_arith(x_comp, -delta)
        new_x_exp = x_exp + (-delta)
        x_exp_comp = _int_to_double_sign_comp(new_x_exp, exponent_width)
        x_machine = _format_float(x_exp_comp + x_comp, exponent_width)
        align_detail = (
            f"ΔE = Ex - Ey = {x_exp} - {y_exp} = {delta} < 0，x 的阶码较小。\n"
            f"将 Mx 算术右移 {-delta} 位，Ex 加 {-delta}：\n"
            f"  原 Mx：{_format_float(x_comp, 1)}\n"
            f"  右移 {-delta} 位后：{_format_float(x_comp, 1)}，移出位：{dropped_bits_x if dropped_bits_x else '无'}\n"
            f"  新 Ex = {x_exp} + {-delta} = {new_x_exp}，补码：{x_exp_comp}\n"
            f"  新 [x]浮 = {x_machine}"
        )

    aligned_y_machine = _format_float(aligned_y_exp_comp + aligned_y_comp, exponent_width)

    steps.append(
        Step(
            title="Step 2：对阶（使两数阶码相同）",
            description=align_detail,
            bit_patterns=[
                BitPattern(
                    label=f"[x]浮 = {x_machine}",
                    bits=x_exp_comp + x_comp,
                    groups=_exp_mant_groups(exponent_width, mantissa_width),
                ),
                BitPattern(
                    label=f"[y]浮（对阶后）= {aligned_y_machine}",
                    bits=aligned_y_exp_comp + aligned_y_comp,
                    groups=_exp_mant_groups(exponent_width, mantissa_width),
                ),
            ],
        )
    )

    # Step 3: mantissa add/sub
    sum_comp, carries = _add_binary(x_comp, aligned_y_comp)
    carry_out = carries[0] if carries else "0"
    steps.append(
        Step(
            title="Step 3：尾数求和（补码加法）",
            description=(
                f"{_format_float(x_comp, 1)} + {_format_float(aligned_y_comp, 1)}\n"
                f"  = {sum_comp}（最高位进位 {carry_out} 自然丢弃）\n"
                f"逐位进位（从低位到高位）：{carries[::-1]}"
            ),
            bit_patterns=[
                BitPattern(
                    label="Mx",
                    bits=x_comp,
                    groups=_sign_mag_groups(mantissa_width),
                ),
                BitPattern(
                    label="My'",
                    bits=aligned_y_comp,
                    groups=_sign_mag_groups(mantissa_width),
                ),
                BitPattern(
                    label="和（进位丢弃）",
                    bits=sum_comp,
                    groups=_sign_mag_groups(mantissa_width),
                ),
            ],
        )
    )

    # Step 4: normalization
    norm_comp = sum_comp
    norm_exp_comp = x_exp_comp if delta >= 0 else aligned_y_exp_comp
    shift_count = 0
    norm_detail = ""

    overflow_right = False
    if (x_neg == (y_neg if operation == "add" else not y_neg)) and (x_neg != (sum_comp[0] == "1")):
        overflow_right = True

    if overflow_right:
        norm_comp_before = norm_comp
        norm_comp, dropped = _shift_right_arith(sum_comp, 1)
        new_exp = _double_sign_comp_to_int(norm_exp_comp) + 1
        norm_exp_comp = _int_to_double_sign_comp(new_exp, exponent_width)
        shift_count = -1
        norm_detail = (
            f"两个同号数相加，结果符号位与操作数不同（{sum_comp[0]}），发生尾数溢出。\n"
            f"右规 1 位：{norm_comp_before} → {norm_comp}，移出位：{dropped if dropped else '无'}\n"
            f"阶码加 1：{_double_sign_comp_to_int(norm_exp_comp)} - 1 的补码 → {norm_exp_comp}（即 {new_exp}）"
        )
    elif not _is_normalized(sum_comp):
        max_left = mantissa_width - 1
        left_shift = 0
        temp = sum_comp
        while left_shift < max_left and not _is_normalized(temp):
            temp = temp[1:] + "0"
            left_shift += 1
        if left_shift > 0:
            norm_comp_before = sum_comp
            norm_comp = temp
            old_exp = _double_sign_comp_to_int(norm_exp_comp)
            new_exp = old_exp - left_shift
            norm_exp_comp = _int_to_double_sign_comp(new_exp, exponent_width)
            shift_count = left_shift
            norm_detail = (
                f"结果 {norm_comp_before} 非规格化（正数首位应为 0.1xxx，负数补码首位应为 1.0xxx）。\n"
                f"左规 {left_shift} 位：{norm_comp_before} → {norm_comp}\n"
                f"阶码减 {left_shift}：{old_exp} → {new_exp}，补码：{norm_exp_comp}"
            )
        else:
            norm_detail = "尾数已是规格化形式，无需规格化。"
    else:
        norm_detail = "尾数已是规格化形式，无需规格化。"

    steps.append(
        Step(
            title="Step 4：规格化处理",
            description=norm_detail,
            bits=norm_comp,
            bit_groups=_sign_mag_groups(mantissa_width),
        )
    )

    # Step 5: rounding
    round_detail = ""
    if dropped_bits:
        action = "进位（末位加 1）" if dropped_bits[-1] == "1" else "舍去"
        round_detail = (
            f"对阶时移出低位：{dropped_bits}\n"
            f"按“0 舍 1 入”规则，末尾为 {dropped_bits[-1]}，执行：{action}"
        )
        if dropped_bits[-1] == "1":
            norm_comp_before = norm_comp
            norm_comp, _ = _add_binary(norm_comp, "0" * (mantissa_width - 1) + "1")
            round_detail += f"\n舍入后尾数：{norm_comp_before} → {norm_comp}"
    else:
        round_detail = "对阶过程没有移出低位，无需舍入处理。"
    steps.append(
        Step(
            title="Step 5：舍入处理",
            description=round_detail,
            bits=norm_comp,
            bit_groups=_sign_mag_groups(mantissa_width),
        )
    )

    # Step 6: overflow detection on exponent
    exp_int = _double_sign_comp_to_int(norm_exp_comp)
    max_exp = 2 ** (exponent_width - 1) - 1
    min_exp = -(2 ** (exponent_width - 1))
    overflow = False
    overflow_note = ""
    if exp_int > max_exp:
        overflow = True
        overflow_note = f"阶码 {exp_int} 上溢，结果溢出。"
    elif exp_int < min_exp:
        overflow = True
        overflow_note = f"阶码 {exp_int} 下溢，结果溢出。"
    else:
        overflow_note = f"阶码 {exp_int} 在合法范围 [{min_exp}, {max_exp}] 内，无溢出。"

    steps.append(
        Step(
            title="Step 6：判溢出（检查阶码是否越界）",
            description=overflow_note,
            bits=norm_exp_comp,
            bit_groups=[HighlightRange(0, exponent_width, label="阶码", color="exponent")],
        )
    )

    final_machine = norm_exp_comp + norm_comp
    neg_final, mag_final = _comp_to_mantissa(norm_comp)
    final_value = f"{'-' if neg_final else '+'}{mag_final} × 2^{exp_int}"

    # Step 7: convert machine result back to true value
    true_value_detail = (
        f"结果机器数：[结果]浮 = {_format_float(final_machine, exponent_width)}\n"
        f"1) 阶码 {norm_exp_comp} 是双符号位补码，真值为 {exp_int}。\n"
        f"2) 尾数 {_format_float(norm_comp, 1)} 是单符号位补码，"
    )
    if neg_final:
        true_value_detail += (
            f"负数。由补码求真值：连同符号位取反加 1，得 {mag_final}。\n"
        )
    else:
        true_value_detail += f"正数，补码与原码相同，即 {mag_final}。\n"
    true_value_detail += (
        f"3) 真值 = (-1)^{final_machine[0]} × {mag_final} × 2^{exp_int} = {final_value}"
    )

    steps.append(
        Step(
            title="Step 7：将结果机器数转换为真值",
            description=true_value_detail,
            bits=norm_comp,
            bit_groups=_sign_mag_groups(mantissa_width),
        )
    )

    steps.append(
        Step(
            title="Step 8：最终结果",
            description=(
                f"[结果]浮 = {_format_float(final_machine, exponent_width)}\n"
                f"符号位 {final_machine[0]}，阶码 {norm_exp_comp}（真值 {exp_int}），尾数 {_format_float(norm_comp, 1)}\n"
                f"真值：{final_value}"
            ),
            bits=final_machine,
            bit_groups=_exp_mant_groups(exponent_width, mantissa_width),
        )
    )

    return FloatingPointResult(
        x=f"{'-' if x_neg else '+'}{x_mag} × 2^{x_exp}",
        y=f"{'-' if original_y_neg else '+'}{y_mag} × 2^{y_exp}",
        operation=operation,
        exponent_width=exponent_width,
        mantissa_width=mantissa_width,
        x_machine=x_machine,
        y_machine=y_machine,
        aligned_y_machine=aligned_y_machine,
        mantissa_sum=sum_comp,
        normalized=_format_float(final_machine, exponent_width),
        final=final_value,
        overflow=overflow,
        steps=steps,
        note=overflow_note if overflow else None,
    )
