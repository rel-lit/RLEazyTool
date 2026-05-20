"""控制台输出与合并结果写盘（与引擎分离）。"""

from __future__ import annotations

from datetime import datetime

from file_analysis import (
    build_console_file_hints,
    build_file_analysis_header_lines,
    build_neutral_notices,
)
from models import MergeRunOptions, MergeRunResult
from scope_rules import format_scope_for_header


def build_report_lines(
    options: MergeRunOptions, result: MergeRunResult
) -> tuple[list[str], list[str]]:
    merge_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stat_lines: list[str] = [
        f"// 合并时间: {merge_time}",
        f"// 来源目录: {options.source_dir}",
        "// 扫描范围: "
        + format_scope_for_header(
            options.source_dir,
            options.merge_max_depth,
            options.merge_scope_exclude,
            options.merge_scope_include,
        ),
    ]
    if options.use_gitignore:
        if options.git_repo_root:
            stat_lines.append(f"// .gitignore: 已启用 (仓库根: {options.git_repo_root})")
        else:
            stat_lines.append("// .gitignore: 已启用 (未检测到 Git 仓库)")
    if options.only_relative_paths is not None:
        stat_lines.append(
            f"// 合并模式: c 点名 ({len(options.only_relative_paths)} 个文件)"
        )
    if result.scan_error:
        stat_lines.append(f"// 扫描错误: {result.scan_error}")
    parts = [
        "// 合并统计：共 {} 个文件，总行数 {}".format(
            result.file_count, result.total_lines
        ),
    ]
    ext_bits = [
        "{} 文件 {} 个".format(ext, result.type_file_count.get(ext, 0))
        for ext in options.file_types
    ]
    parts[0] += "，" + "，".join(ext_bits)
    cs = result.cs_stats
    if ".cs" in options.file_types and cs is not None:
        parts[0] += (
            "，类 {} 个，结构体 {} 个，枚举 {} 个，接口 {} 个，"
            "变量/字段/属性 {} 个，方法 {} 个".format(
                cs.class_count,
                cs.struct_count,
                cs.enum_count,
                cs.interface_count,
                cs.variable_count,
                cs.method_count,
            )
        )
    parts[0] += "，读取失败 {} 个文件".format(result.error_count)
    stat_lines.append(parts[0])

    detail_lines: list[str] = []
    if ".cs" in options.file_types and cs is not None and cs.cs_class_infos:
        infos = cs.cs_class_infos
        real_classes = [c for c in infos if not c[0] and not c[1]]
        abstract_classes = [c for c in infos if c[0] and not c[1]]
        interfaces = [c for c in infos if c[1]]
        avg_real = (
            round(sum(c[3] for c in real_classes) / len(real_classes), 2)
            if real_classes
            else 0
        )
        avg_abs_m = (
            round(sum(c[6] for c in abstract_classes) / len(abstract_classes), 2)
            if abstract_classes
            else 0
        )
        max_len = max((c[3] for c in infos), default=0)
        min_len = min((c[3] for c in infos), default=0)
        avg_m = round(sum(c[4] for c in infos) / len(infos), 2) if infos else 0
        avg_f = round(sum(c[5] for c in infos) / len(infos), 2) if infos else 0
        avg_enum = (
            round(
                sum(cs.enum_member_counts) / len(cs.enum_member_counts),
                2,
            )
            if cs.enum_member_counts
            else 0
        )
        avg_struct_f = (
            round(
                sum(cs.struct_field_counts) / len(cs.struct_field_counts),
                2,
            )
            if cs.struct_field_counts
            else 0
        )
        avg_iface_m = (
            round(sum(c[4] for c in interfaces) / len(interfaces), 2)
            if interfaces
            else 0
        )
        line_a = (
            "// 实际类平均长度: {} 行，抽象类平均抽象方法数: {}，"
            "最大类长度: {}，最小类长度: {}".format(
                avg_real, avg_abs_m, max_len, min_len
            )
        )
        line_b = "// 平均每类方法数: {}，平均每类字段数: {}".format(avg_m, avg_f)
        line_c = (
            "// 枚举平均成员数: {}，结构体平均字段数: {}，接口平均方法数: {}".format(
                avg_enum, avg_struct_f, avg_iface_m
            )
        )
        stat_lines.extend([line_a, line_b, line_c])
        detail_lines = [
            line_a.replace("// ", ""),
            line_b.replace("// ", ""),
            line_c.replace("// ", ""),
        ]
    if result.file_entries:
        stat_lines.extend(
            build_file_analysis_header_lines(
                result.file_entries,
                options.file_types,
                cs.cs_class_infos if cs is not None else None,
            )
        )
    stat_lines.append("// ==========================================")
    return stat_lines, detail_lines


def print_scan_banner(source_dir: str, scope_text: str) -> None:
    print(f"🔍 正在扫描目录: {source_dir}")
    print(f"📂 扫描范围: {scope_text}")


def print_merge_summary(result: MergeRunResult, file_types: tuple[str, ...]) -> None:
    print("-" * 30)
    if result.scan_error:
        print(f"⚠️ 扫描目录时出错: {result.scan_error}")
    print(f"✅ 成功! 共处理了 {result.file_count} 个文件，总行数 {result.total_lines}。")
    for ext in file_types:
        print(f"{ext} 文件: {result.type_file_count.get(ext, 0)} 个")
    cs = result.cs_stats
    if ".cs" in file_types and cs is not None:
        print(
            f"类: {cs.class_count}，结构体: {cs.struct_count}，"
            f"枚举: {cs.enum_count}，接口: {cs.interface_count}"
        )
        print(f"变量/字段/属性: {cs.variable_count}，方法: {cs.method_count}")
        for line in result.console_detail_lines:
            print(line)
    for line in build_console_file_hints(result.file_entries):
        print(line)
    for line in build_neutral_notices(result):
        print(line)
    print("")


def write_merged_output(output_path: str, result: MergeRunResult) -> None:
    stat_str = "\n".join(result.stat_header_lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(stat_str)
        for chunk in result.merged_chunks:
            outfile.write(chunk)
    print(f"\n🎉 合并完成，文件已生成：{output_path}")
