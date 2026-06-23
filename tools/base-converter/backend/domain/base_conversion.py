"""Pure functions for base conversion with step-by-step visualization."""
from typing import List, Tuple
from .models import BaseConversionResult, Step, HighlightRange


def _validate(value: str, base: int) -> Tuple[str, bool]:
    """Return (cleaned_value, is_negative) and validate digits."""
    value = value.strip()
    if not value:
        raise ValueError("输入为空")
    negative = value.startswith("-")
    if negative:
        value = value[1:].strip()
    if not value:
        raise ValueError("仅包含负号")
    allowed = "0123456789abcdefABCDEF."
    if any(c not in allowed for c in value):
        raise ValueError(f"包含非法字符，仅允许 {allowed}")
    if value.count(".") > 1:
        raise ValueError("最多只能有一个小数点")
    if base == 2:
        digits = set(value) - {".", "-"}
        if not digits <= {"0", "1"}:
            raise ValueError("二进制只能包含 0 和 1")
    elif base == 10:
        digits = set(value) - {".", "-"}
        if not digits <= set("0123456789"):
            raise ValueError("十进制只能包含 0-9")
    elif base == 16:
        digits = set(value) - {".", "-"}
        if not digits <= set("0123456789abcdefABCDEF"):
            raise ValueError("十六进制只能包含 0-9, a-f, A-F")
    else:
        raise ValueError(f"不支持的进制: {base}")
    return value, negative


def _base_digit_to_int(ch: str) -> int:
    return int(ch, 16)


def _int_to_base_digit(n: int) -> str:
    if 0 <= n <= 9:
        return str(n)
    return chr(ord("A") + n - 10)


def _decimal_integer_to_base(integer_part: int, base: int) -> Tuple[str, List[Step]]:
    steps: List[Step] = []
    if integer_part == 0:
        steps.append(
            Step(
                title="整数部分：除基取余",
                description="整数为 0，直接记为 0",
            )
        )
        return "0", steps

    rows: List[List[str]] = []
    remainders: List[int] = []
    n = integer_part
    step_no = 1
    while n > 0:
        q = n // base
        r = n % base
        remainders.append(r)
        rows.append([str(step_no), str(n), f"÷ {base}", str(q), f"余 {_int_to_base_digit(r)}"])
        n = q
        step_no += 1

    reversed_remainders = list(reversed(remainders))
    result = "".join(_int_to_base_digit(r) for r in reversed_remainders)
    steps.append(
        Step(
            title="整数部分：除基取余，逆序排列",
            description=f"将 {integer_part} 反复除以 {base}，记录余数，再逆序读取",
            table_headers=["步骤", "被除数", "运算", "商", "余数"],
            table=rows,
        )
    )
    steps.append(
        Step(
            title="整数部分结果",
            description=f"余数序列：{' '.join(_int_to_base_digit(r) for r in remainders)}；逆序后：{result}",
        )
    )
    return result, steps


def _decimal_fraction_to_base(fraction_str: str, base: int, precision: int) -> Tuple[str, List[Step], str]:
    """fraction_str is the part after decimal point (e.g. '625')."""
    steps: List[Step] = []
    if not fraction_str or int(fraction_str) == 0:
        steps.append(
            Step(
                title="小数部分：乘基取整",
                description="小数部分为 0，无需转换",
            )
        )
        return "", steps, ""

    # Convert fraction_str to actual fraction numerator/denominator to avoid float errors
    denominator = 10 ** len(fraction_str)
    numerator = int(fraction_str)

    rows: List[List[str]] = []
    digits: List[int] = []
    seen: dict = {}
    terminated = False
    repeating = False
    repeat_start = -1
    note = ""
    frac_numerator = numerator
    step_no = 1

    while len(digits) < precision:
        if frac_numerator == 0:
            terminated = True
            break
        if frac_numerator in seen:
            repeating = True
            repeat_start = seen[frac_numerator]
            break
        seen[frac_numerator] = step_no

        frac_numerator *= base
        digit = frac_numerator // denominator
        frac_numerator = frac_numerator % denominator
        digits.append(digit)
        rows.append([
            str(step_no),
            f"{numerator if step_no == 1 else '...'}/{denominator}",
            f"× {base} = {digit * denominator + frac_numerator}/{denominator}",
            f"取整 {_int_to_base_digit(digit)}",
            f"余 {frac_numerator}/{denominator}"
        ])
        step_no += 1

    if repeating:
        note = f"小数部分在 {base} 进制下循环（从第 {repeat_start} 位开始），按题目要求保留 {precision} 位后截断"
    elif not terminated and len(digits) == precision:
        note = f"小数部分无法精确表示，按题目要求保留 {precision} 位后截断"

    if digits:
        result = "".join(_int_to_base_digit(d) for d in digits)
        steps.append(
            Step(
                title=f"小数部分：乘基取整，顺序排列（保留 {precision} 位）",
                description="将小数部分反复乘以目标进制，取整数位，顺序读取",
                table_headers=["步骤", "被乘数", "乘积", "整数位", "余数"],
                table=rows,
            )
        )
        steps.append(
            Step(
                title="小数部分结果",
                description=f"整数位序列：{' '.join(_int_to_base_digit(d) for d in digits)}；顺序读取：0.{result}",
            )
        )
    else:
        result = ""

    return result, steps, note


def _base_to_decimal_integer(value: str, base: int) -> Tuple[int, List[Step]]:
    total = 0
    rows: List[List[str]] = []
    length = len(value)
    for i, ch in enumerate(value):
        power = length - 1 - i
        digit = _base_digit_to_int(ch)
        contribution = digit * (base ** power)
        total += contribution
        rows.append([ch, str(power), f"{base}^{power}", str(digit * (base ** power)), str(total)])
    steps = [
        Step(
            title="整数部分：按权展开求和",
            description="每一位数字乘以对应位的权值，累加得到十进制整数",
            table_headers=["位", "位置", "权值", "贡献", "累加"],
            table=rows,
        )
    ]
    return total, steps


def _base_to_decimal_fraction(value: str, base: int) -> Tuple[float, List[Step]]:
    total = 0
    rows: List[List[str]] = []
    for i, ch in enumerate(value):
        power = -(i + 1)
        digit = _base_digit_to_int(ch)
        contribution = digit * (base ** power)
        total += contribution
        rows.append([ch, str(power), f"{base}^{power}", f"{digit * (base ** power)}", f"{total}"])
    steps = [
        Step(
            title="小数部分：按权展开求和",
            description="每一位数字乘以对应负权值，累加得到十进制小数",
            table_headers=["位", "位置", "权值", "贡献", "累加"],
            table=rows,
        )
    ]
    return total, steps


def _binary_hex_convert(value: str, from_base: int, to_base: int) -> Tuple[str, List[Step]]:
    if from_base not in (2, 16) or to_base not in (2, 16):
        raise ValueError("二 ↔ 十六转换仅支持 2 和 16 进制")
    if from_base == to_base:
        return value, [Step(title="无需转换", description="源进制与目标进制相同")]

    steps: List[Step] = []
    if "." in value:
        int_part, frac_part = value.split(".")
    else:
        int_part, frac_part = value, ""

    if from_base == 2 and to_base == 16:
        # Pad integer part left to multiple of 4
        pad_int = (4 - len(int_part) % 4) % 4
        padded_int = "0" * pad_int + int_part
        # Pad fractional part right to multiple of 4
        pad_frac = (4 - len(frac_part) % 4) % 4
        padded_frac = frac_part + "0" * pad_frac

        groups_int = [padded_int[i:i+4] for i in range(0, len(padded_int), 4)]
        groups_frac = [padded_frac[i:i+4] for i in range(0, len(padded_frac), 4)] if padded_frac else []

        result_int = "".join(_int_to_base_digit(int(g, 2)) for g in groups_int)
        result_frac = "".join(_int_to_base_digit(int(g, 2)) for g in groups_frac) if groups_frac else ""
        result = f"{result_int}.{result_frac}" if result_frac else result_int

        bit_groups = []
        pos = 0
        for g in groups_int:
            bit_groups.append(HighlightRange(start=pos, end=pos + 4, label=f"{int(g, 2):X}"))
            pos += 4
        if result_frac:
            pos = 0  # fractional visualization handled separately if needed

        steps.append(
            Step(
                title="二进制 → 十六进制：以小数点为界，每 4 位一组，不足补 0",
                description=f"整数部分左侧补 {pad_int} 个 0，小数部分右侧补 {pad_frac} 个 0，然后每组转 1 位十六进制",
                bits=padded_int + ("." + padded_frac if padded_frac else ""),
                table_headers=["二进制组", "十六进制"],
                table=[[g, _int_to_base_digit(int(g, 2))] for g in (groups_int + groups_frac)],
            )
        )
        return result, steps

    elif from_base == 16 and to_base == 2:
        int_digits = [c for c in int_part]
        frac_digits = [c for c in frac_part]
        result_int = "".join(f"{_base_digit_to_int(c):04b}" for c in int_digits)
        result_frac = "".join(f"{_base_digit_to_int(c):04b}" for c in frac_digits) if frac_digits else ""
        result = f"{result_int}.{result_frac}" if result_frac else result_int

        rows = []
        for c in int_digits + frac_digits:
            rows.append([c, f"{_base_digit_to_int(c):04b}"])

        steps.append(
            Step(
                title="十六进制 → 二进制：每位展开为 4 位二进制",
                description="以小数点为界，每一位十六进制直接写成 4 位二进制",
                table_headers=["十六进制位", "二进制"],
                table=rows,
            )
        )
        return result, steps

    raise ValueError("转换不支持")


def convert(value: str, from_base: int, to_base: int, precision: int = 8) -> BaseConversionResult:
    """Convert a number between bases 2, 10, 16 with detailed steps."""
    if from_base not in (2, 10, 16) or to_base not in (2, 10, 16):
        raise ValueError("仅支持 2、10、16 进制之间的转换")

    cleaned, negative = _validate(value, from_base)

    if "." in cleaned:
        int_str, frac_str = cleaned.split(".")
    else:
        int_str, frac_str = cleaned, ""

    steps: List[Step] = []
    note = ""
    result = ""

    if from_base == 10:
        # Decimal -> base
        int_val = int(int_str) if int_str else 0
        int_result, int_steps = _decimal_integer_to_base(int_val, to_base)
        frac_result, frac_steps, frac_note = _decimal_fraction_to_base(frac_str, to_base, precision)
        steps.extend(int_steps)
        steps.extend(frac_steps)
        if frac_result:
            result = f"{int_result}.{frac_result}"
        else:
            result = int_result
        note = frac_note
    elif to_base == 10:
        # Base -> decimal
        int_val, int_steps = _base_to_decimal_integer(int_str if int_str else "0", from_base)
        steps.extend(int_steps)
        if frac_str:
            frac_val, frac_steps = _base_to_decimal_fraction(frac_str, from_base)
            steps.extend(frac_steps)
            total = int_val + frac_val
            result = str(total)
        else:
            result = str(int_val)
    else:
        # Binary <-> Hex: convert via decimal internally? For steps we can show direct grouping
        result, steps = _binary_hex_convert(cleaned, from_base, to_base)

    if negative and result != "0":
        result = "-" + result

    return BaseConversionResult(
        source_value=value,
        source_base=from_base,
        target_base=to_base,
        result=result,
        steps=steps,
        note=note or None,
    )
