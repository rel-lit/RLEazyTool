"""控制台输出与合并结果写盘（与引擎分离）。"""

from __future__ import annotations

from file_analysis import build_console_file_hints, build_neutral_notices
from merge_engine import MergeRunResult


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
