"""控制台输出与合并结果写盘（与引擎分离）。"""

from __future__ import annotations

from merge_engine import MergeRunResult


def print_scan_banner(source_dir: str, recursive: bool) -> None:
    print(f"🔍 正在扫描目录: {source_dir}")
    print(
        "📂 扫描范围: "
        + ("含子文件夹" if recursive else "仅当前文件夹（不含子目录）")
    )


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
        print("")
        for line in result.console_detail_lines:
            print(line)
        print("")


def apply_merge_jokes(joke_state: dict, result: MergeRunResult) -> None:
    if joke_state is None:
        return
    if result.scan_error and not joke_state.get("scan_error"):
        print("目录我读不动啦，检查一下路径或权限再试试吧~")
        joke_state["scan_error"] = True
    fc = result.file_count
    if fc >= 50 and not joke_state.get("file50"):
        print("哇哦，50个以上文件？你是要挑战我的极限吗？美少女架构师可不会轻易认输哦！")
        joke_state["file50"] = True
    elif fc >= 30 and not joke_state.get("file30"):
        print("30+文件合并，今天也是元气满满地搬砖呢！不过你可别偷懒让我全干了呀~")
        joke_state["file30"] = True
    elif fc >= 20 and not joke_state.get("file20"):
        print("20个文件，批量操作才是大佬的日常，继续加油哦！")
        joke_state["file20"] = True
    elif fc >= 10 and not joke_state.get("file10"):
        print("文件数量上双，手速跟得上我可爱的嘴炮吗？")
        joke_state["file10"] = True
    tl = result.total_lines
    if tl >= 5000 and not joke_state.get("line5000"):
        print("5000+行代码，眼睛要保护好哦，不然我可要心疼你啦！")
        joke_state["line5000"] = True
    elif tl >= 2000 and not joke_state.get("line2000"):
        print("合并内容超过2000行，代码海洋都快淹没我这小小美少女了！")
        joke_state["line2000"] = True
    cs = result.cs_stats
    if cs is not None and cs.cs_class_infos:
        real_classes = [c for c in cs.cs_class_infos if not c[0] and not c[1]]
        avg_real = (
            round(sum(c[3] for c in real_classes) / len(real_classes), 2)
            if real_classes
            else 0
        )
        if avg_real > 200 and not joke_state.get("avg_class_len200"):
            print("欸？你这要成为屎山了吧？美少女架构师在线劝退大类，快拆分一下啦！")
            joke_state["avg_class_len200"] = True
    if result.error_count > 0 and not joke_state.get("error"):
        print("有文件读取失败啦，别怕，有我罩着你，快检查下路径或权限吧~")
        joke_state["error"] = True


def write_merged_output(output_path: str, result: MergeRunResult) -> None:
    stat_str = "\n".join(result.stat_header_lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(stat_str)
        for chunk in result.merged_chunks:
            outfile.write(chunk)
    print(f"\n🎉 合并完成，文件已生成：{output_path}")
