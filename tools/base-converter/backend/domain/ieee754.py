"""IEEE 754 floating-point conversion: decimal <-> binary/hex representation."""
import math
import struct
from typing import List, Tuple
from .models import Step, HighlightRange


def _get_params(precision: str) -> Tuple[int, int, int]:
    """Return (total_bits, exponent_bits, bias)."""
    if precision == "float32":
        return 32, 8, 127
    if precision == "float64":
        return 64, 11, 1023
    raise ValueError("precision 只能是 float32 或 float64")


def _float_to_bits(value: float, precision: str) -> Tuple[str, str]:
    """Pack a Python float into IEEE 754 bits and hex string."""
    total, exp_bits, bias = _get_params(precision)
    fmt = "!f" if precision == "float32" else "!d"
    packed = struct.pack(fmt, value)
    bits = "".join(f"{b:08b}" for b in packed)
    hex_str = packed.hex().upper()
    return bits, hex_str


def _bits_to_float(bits: str, precision: str) -> float:
    """Unpack IEEE 754 bits to a Python float."""
    total, exp_bits, bias = _get_params(precision)
    if len(bits) != total:
        raise ValueError(f"{precision} 需要 {total} 位二进制")
    byte_vals = [int(bits[i:i+8], 2) for i in range(0, total, 8)]
    packed = bytes(byte_vals)
    fmt = "!f" if precision == "float32" else "!d"
    return struct.unpack(fmt, packed)[0]


def _integer_to_binary(n: int, bits: int) -> str:
    if n < 0 or n >= 2 ** bits:
        raise ValueError(f"数值 {n} 无法用 {bits} 位二进制表示")
    return format(n, f"0{bits}b")


def _decimal_to_binary_parts(value: float) -> Tuple[bool, str, int]:
    """Convert absolute value of a float to normalized binary: 1.xxxx * 2^e.
    Returns (sign_bit, normalized_mantissa_without_leading_one, exponent)."""
    if value == 0.0:
        return False, "", 0

    sign = value < 0
    v = abs(value)

    # Use math.frexp: returns (m, e) such that v = m * 2^e, 0.5 <= abs(m) < 1
    m, e = math.frexp(v)
    # Normalize to 1.xxxx form: m * 2 = 1.xxxx, exponent becomes e - 1
    normalized = m * 2  # now 1 <= normalized < 2
    exp = e - 1

    # Convert fractional part to binary
    frac = normalized - 1.0
    frac_bits = []
    # Generate enough bits for float64 (52 + some extra for rounding visualization)
    for _ in range(64):
        frac *= 2
        bit = int(frac)
        frac_bits.append(str(bit))
        frac -= bit

    return sign, "".join(frac_bits), exp


def convert_decimal_to_ieee(value: float, precision: str = "float32") -> dict:
    total, exp_bits, bias = _get_params(precision)
    frac_bits_count = total - 1 - exp_bits

    if value == 0.0:
        bits = "0" * total
        hex_str = "0" * (total // 4)
        return {
            "input": str(value),
            "precision": precision,
            "bits": bits,
            "hex": "0x" + hex_str,
            "sign": "0",
            "exponent_bits": "0" * exp_bits,
            "fraction_bits": "0" * frac_bits_count,
            "biased_exponent": 0,
            "unbiased_exponent": None,
            "decimal_value": 0.0,
            "note": "零",
            "steps": [Step(title="零的特殊表示", description="IEEE 754 中零的阶码和尾数全为 0")],
        }

    if math.isnan(value) or math.isinf(value):
        bits, hex_str = _float_to_bits(value, precision)
        return {
            "input": str(value),
            "precision": precision,
            "bits": bits,
            "hex": "0x" + hex_str,
            "sign": bits[0],
            "exponent_bits": bits[1:1+exp_bits],
            "fraction_bits": bits[1+exp_bits:],
            "biased_exponent": int(bits[1:1+exp_bits], 2),
            "unbiased_exponent": None,
            "decimal_value": value,
            "note": "NaN 或 Infinity",
            "steps": [],
        }

    sign, frac_bits, exp = _decimal_to_binary_parts(value)
    biased_exp = exp + bias

    # Round fraction to required length
    rounded_frac = frac_bits[:frac_bits_count]

    sign_bit = "1" if sign else "0"
    exp_bits_str = _integer_to_binary(biased_exp, exp_bits)
    frac_bits_str = rounded_frac.ljust(frac_bits_count, "0")
    bits = sign_bit + exp_bits_str + frac_bits_str
    hex_str = "".join(f"{int(bits[i:i+4], 2):X}" for i in range(0, total, 4))

    # Visualization steps
    steps: List[Step] = []
    abs_value = abs(value)

    steps.append(
        Step(
            title="Step 1：确定符号位",
            description=f"输入 {value}，{'负' if sign else '正'}数，符号位为 {sign_bit}",
            bits=sign_bit,
            bit_groups=[HighlightRange(0, 1, label="符号位", color="sign")],
        )
    )

    # Show binary representation of absolute value
    int_part = int(abs_value)
    frac_part = abs_value - int_part
    int_bin = bin(int_part)[2:] if int_part > 0 else "0"
    frac_bin = ""
    f = frac_part
    for _ in range(min(20, frac_bits_count)):
        if f == 0:
            break
        f *= 2
        bit = int(f)
        frac_bin += str(bit)
        f -= bit

    steps.append(
        Step(
            title="Step 2：将绝对值转换为二进制",
            description=f"|{value}| = {int_part} + {frac_part:.10f} = {int_bin}.{frac_bin}",
        )
    )

    steps.append(
        Step(
            title="Step 3：规格化",
            description=f"写成 1.xxxx × 2^n 形式：1.{rounded_frac[:8]}... × 2^{exp}",
        )
    )

    steps.append(
        Step(
            title="Step 4：计算阶码（加偏置值）",
            description=f"阶码真值 {exp} + 偏置值 {bias} = {biased_exp}，二进制为 {exp_bits_str}",
            bits=exp_bits_str,
            bit_groups=[HighlightRange(0, exp_bits, label="阶码", color="exponent")],
        )
    )

    steps.append(
        Step(
            title="Step 5：尾数去掉隐含的最高位 1",
            description=f"规格化后尾数 1.{rounded_frac[:8]}...，去掉前导 1 得到 {rounded_frac[:8]}...，保留 {frac_bits_count} 位",
            bits=frac_bits_str,
            bit_groups=[HighlightRange(0, frac_bits_count, label="尾数", color="mantissa")],
        )
    )

    steps.append(
        Step(
            title="Step 6：组合成 IEEE 754 格式",
            description=f"符号位 + 阶码 + 尾数 = {bits}",
            bits=bits,
            bit_groups=[
                HighlightRange(0, 1, label="符号", color="sign"),
                HighlightRange(1, 1 + exp_bits, label="阶码", color="exponent"),
                HighlightRange(1 + exp_bits, total, label="尾数", color="mantissa"),
            ],
        )
    )

    return {
        "input": str(value),
        "precision": precision,
        "bits": bits,
        "hex": "0x" + hex_str,
        "sign": sign_bit,
        "exponent_bits": exp_bits_str,
        "fraction_bits": frac_bits_str,
        "biased_exponent": biased_exp,
        "unbiased_exponent": exp,
        "decimal_value": value,
        "note": None,
        "steps": steps,
    }


def convert_ieee_to_decimal(bits: str, precision: str = "float32") -> dict:
    total, exp_bits, bias = _get_params(precision)
    frac_bits_count = total - 1 - exp_bits

    if len(bits) != total:
        raise ValueError(f"{precision} 需要 {total} 位二进制")

    sign_bit = bits[0]
    exp_bits_str = bits[1:1+exp_bits]
    frac_bits_str = bits[1+exp_bits:]

    biased_exp = int(exp_bits_str, 2)
    sign = -1 if sign_bit == "1" else 1

    steps: List[Step] = []
    steps.append(
        Step(
            title="Step 1：拆分字段",
            description=f"符号位 {sign_bit}，阶码 {exp_bits_str}，尾数 {frac_bits_str}",
            bits=bits,
            bit_groups=[
                HighlightRange(0, 1, label="符号", color="sign"),
                HighlightRange(1, 1 + exp_bits, label="阶码", color="exponent"),
                HighlightRange(1 + exp_bits, total, label="尾数", color="mantissa"),
            ],
        )
    )

    note = None
    value = None

    if biased_exp == 0:
        # Denormalized
        exp = 1 - bias
        mantissa = int(frac_bits_str, 2) / (2 ** frac_bits_count)
        value = sign * mantissa * (2 ** exp)
        note = "非规格化数"
        steps.append(Step(title="Step 2：非规格化数", description=f"阶码全 0，真值 = (-1)^{sign_bit} × 0.{frac_bits_str} × 2^{exp}"))
    elif biased_exp == (2 ** exp_bits - 1):
        # Infinity or NaN
        if int(frac_bits_str, 2) == 0:
            value = float('inf') if sign == 1 else float('-inf')
            note = "Infinity"
        else:
            value = float('nan')
            note = "NaN"
        steps.append(Step(title="Step 2：特殊值", description=note))
    else:
        exp = biased_exp - bias
        mantissa = 1 + int(frac_bits_str, 2) / (2 ** frac_bits_count)
        value = sign * mantissa * (2 ** exp)
        steps.append(
            Step(
                title="Step 2：计算真值",
                description=f"阶码真值 = {biased_exp} - {bias} = {exp}\n" +
                            f"尾数 = 1.{frac_bits_str} = {mantissa}\n" +
                            f"真值 = (-1)^{sign_bit} × {mantissa} × 2^{exp} = {value}",
            )
        )

    hex_str = "".join(f"{int(bits[i:i+4], 2):X}" for i in range(0, total, 4))

    return {
        "input": bits,
        "precision": precision,
        "bits": bits,
        "hex": "0x" + hex_str,
        "sign": sign_bit,
        "exponent_bits": exp_bits_str,
        "fraction_bits": frac_bits_str,
        "biased_exponent": biased_exp,
        "unbiased_exponent": exp if value is not None and not math.isnan(value) and not math.isinf(value) else None,
        "decimal_value": value,
        "note": note,
        "steps": steps,
    }


def convert(value: str, precision: str = "float32", direction: str = "to_ieee") -> dict:
    """Main entry point."""
    if direction == "to_ieee":
        try:
            num = float(value)
        except ValueError:
            raise ValueError("请输入合法的十进制数")
        return convert_decimal_to_ieee(num, precision)
    elif direction == "to_decimal":
        bits = value.strip().replace(" ", "").replace("0x", "").replace("0X", "")
        if any(c not in "01" for c in bits):
            raise ValueError("反转换请输入二进制串（仅含 0/1）")
        return convert_ieee_to_decimal(bits, precision)
    else:
        raise ValueError("direction 只能是 to_ieee 或 to_decimal")
