# 文件合并、内容统计、正则分析相关代码将在此实现

import os
import re
from datetime import datetime

def merge_files_by_types(source_dir, output_path, file_types, joke_state=None):
    """支持多类型文件合并，.cs 文件统计 C# 结构，其余类型只统计文件数和行数"""
    exclude_dirs = {'.git', 'bin', 'obj', 'node_modules', '.vs', 'packages', 'Debug', 'Release'}
    file_count = 0
    error_count = 0
    total_lines = 0
    class_count = 0
    struct_count = 0
    enum_count = 0
    interface_count = 0
    variable_count = 0
    method_count = 0
    type_file_count = {ext: 0 for ext in file_types}

    re_class = re.compile(r'\bclass\s+\w+')
    re_struct = re.compile(r'\bstruct\s+\w+')
    re_enum = re.compile(r'\benum\s+\w+')
    re_interface = re.compile(r'\binterface\s+\w+')
    re_variable = re.compile(r'\b(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>\[\],]+\s+\w+\s*(=|;|\{)')
    re_method = re.compile(r'\b(public|private|protected|internal)\s+((static|virtual|override|async|sealed|new|partial)\s+)*[\w<>\[\],]+\s+\w+\s*\([^;]*\)\s*(\{|where|$)')

    print(f"🔍 正在扫描目录: {source_dir}")

    cs_class_infos = []
    enum_member_counts = []
    struct_field_counts = []
    interface_method_counts = []

    def analyze_cs_classes(content):
        nonlocal class_count, struct_count, enum_count, interface_count, variable_count, method_count
        class_count += len(re_class.findall(content))
        struct_count += len(re_struct.findall(content))
        enum_count += len(re_enum.findall(content))
        interface_count += len(re_interface.findall(content))
        variable_count += len(re_variable.findall(content))
        method_count += len(re_method.findall(content))
        class_pattern = re.compile(r'(public|private|protected|internal)?\s*(abstract)?\s*class\s+(\w+)')
        for m in class_pattern.finditer(content):
            is_abstract = m.group(2) is not None
            class_name = m.group(3)
            class_body = extract_type_body(content, m.start())
            methods = re.findall(r'(public|private|protected|internal)?\s*(abstract)?\s*([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*(;|\{)', class_body)
            method_count = len(methods)
            fields = re.findall(r'(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>,\[\]]+\s+\w+\s*(=|;|\{)', class_body)
            field_count = len(fields)
            abstract_methods = [m for m in methods if m[1] == 'abstract']
            abstract_method_count = len(abstract_methods)
            cs_class_infos.append((is_abstract, False, class_name, class_body.count('\n'), method_count, field_count, abstract_method_count))
        interface_pattern = re.compile(r'(public|private|protected|internal)?\s*interface\s+(\w+)')
        for m in interface_pattern.finditer(content):
            interface_name = m.group(2)
            interface_body = extract_type_body(content, m.start())
            methods = re.findall(r'([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*;', interface_body)
            method_count = len(methods)
            cs_class_infos.append((False, True, interface_name, interface_body.count('\n'), method_count, 0, 0))
            interface_method_counts.append(method_count)
        struct_pattern = re.compile(r'(public|private|protected|internal)?\s*struct\s+(\w+)')
        for m in struct_pattern.finditer(content):
            struct_body = extract_type_body(content, m.start())
            fields = re.findall(r'(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>,\[\]]+\s+\w+\s*(=|;|\{)', struct_body)
            struct_field_counts.append(len(fields))
        enum_pattern = re.compile(r'(public|private|protected|internal)?\s*enum\s+(\w+)')
        for m in enum_pattern.finditer(content):
            enum_body = extract_type_body(content, m.start())
            members = [x for x in enum_body.split(',') if x.strip() and not x.strip().startswith('//')]
            enum_member_counts.append(len(members))

    def extract_type_body(content, start_idx):
        brace = 0
        in_body = False
        body = []
        for i in range(start_idx, len(content)):
            c = content[i]
            if c == '{':
                brace += 1
                in_body = True
            if in_body:
                body.append(c)
            if c == '}':
                brace -= 1
                if brace == 0 and in_body:
                    break
        return ''.join(body)

    merged_contents = []
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            for ext in file_types:
                if file.endswith(ext):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    merged_contents.append(f"\n\n// ==================== 文件: {relative_path} ====================\n\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        type_file_count[ext] += 1
                        if ext == '.cs':
                            analyze_cs_classes(content)
                        merged_contents.append(content)
                        file_count += 1
                    except Exception as e:
                        merged_contents.append(f"// [错误] 无法读取文件: {e}\n")
                        error_count += 1
                    break

    merge_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stat_lines = []
    stat_lines.append(f"// 合并时间: {merge_time}")
    stat_lines.append(f"// 来源目录: {source_dir}")
    main_stat = "// 合并统计：共 {} 个文件，总行数 {}，".format(file_count, total_lines)
    main_stat += ", ".join(["{} 文件 {} 个".format(ext, type_file_count[ext]) for ext in file_types])
    if '.cs' in file_types:
        main_stat += "，类 {} 个，结构体 {} 个，枚举 {} 个，接口 {} 个，变量/字段/属性 {} 个，方法 {} 个".format(
            class_count, struct_count, enum_count, interface_count, variable_count, method_count)
    main_stat += "，读取失败 {} 个文件".format(error_count)
    stat_lines.append(main_stat)
    detail_lines = []
    if '.cs' in file_types:
        real_classes = [c for c in cs_class_infos if not c[0] and not c[1]]
        abstract_classes = [c for c in cs_class_infos if c[0] and not c[1]]
        interfaces = [c for c in cs_class_infos if c[1]]
        avg_real_class_len = round(sum(c[3] for c in real_classes)/len(real_classes), 2) if real_classes else 0
        avg_abstract_methods = round(sum(c[6] for c in abstract_classes)/len(abstract_classes), 2) if abstract_classes else 0
        max_class_len = max((c[3] for c in cs_class_infos), default=0)
        min_class_len = min((c[3] for c in cs_class_infos), default=0)
        avg_methods_per_class = round(sum(c[4] for c in cs_class_infos)/len(cs_class_infos), 2) if cs_class_infos else 0
        avg_fields_per_class = round(sum(c[5] for c in cs_class_infos)/len(cs_class_infos), 2) if cs_class_infos else 0
        avg_enum_members = round(sum(enum_member_counts)/len(enum_member_counts), 2) if enum_member_counts else 0
        avg_struct_fields = round(sum(struct_field_counts)/len(struct_field_counts), 2) if struct_field_counts else 0
        avg_iface_methods = round(sum(c[4] for c in interfaces)/len(interfaces), 2) if interfaces else 0
        stat_lines.append("// 实际类平均长度: {} 行，抽象类平均抽象方法数: {}，最大类长度: {}，最小类长度: {}".format(
            avg_real_class_len, avg_abstract_methods, max_class_len, min_class_len))
        stat_lines.append("// 平均每类方法数: {}，平均每类字段数: {}".format(
            avg_methods_per_class, avg_fields_per_class))
        stat_lines.append("// 枚举平均成员数: {}，结构体平均字段数: {}，接口平均方法数: {}".format(
            avg_enum_members, avg_struct_fields, avg_iface_methods))
        detail_lines.append("实际类平均长度: {} 行，抽象类平均抽象方法数: {}，最大类长度: {}，最小类长度: {}".format(
            avg_real_class_len, avg_abstract_methods, max_class_len, min_class_len))
        detail_lines.append("平均每类方法数: {}，平均每类字段数: {}".format(
            avg_methods_per_class, avg_fields_per_class))
        detail_lines.append("枚举平均成员数: {}，结构体平均字段数: {}，接口平均方法数: {}".format(
            avg_enum_members, avg_struct_fields, avg_iface_methods))
    stat_lines.append("// ==========================================")
    stat_str = "\n".join(stat_lines) + "\n"
    print("-" * 30)
    print(f"✅ 成功! 共处理了 {file_count} 个文件，总行数 {total_lines}。")
    for ext in file_types:
        print(f"{ext} 文件: {type_file_count[ext]} 个")
    if '.cs' in file_types:
        print(f"类: {class_count}，结构体: {struct_count}，枚举: {enum_count}，接口: {interface_count}")
        print(f"变量/字段/属性: {variable_count}，方法: {method_count}")
        print("")
        for line in detail_lines:
            print(line)
        print("")
    if joke_state is not None:
        if file_count >= 50 and not joke_state.get('file50'):
            print("哇哦，50个以上文件？你是要挑战我的极限吗？美少女架构师可不会轻易认输哦！")
            joke_state['file50'] = True
        elif file_count >= 30 and not joke_state.get('file30'):
            print("30+文件合并，今天也是元气满满地搬砖呢！不过你可别偷懒让我全干了呀~")
            joke_state['file30'] = True
        elif file_count >= 20 and not joke_state.get('file20'):
            print("20个文件，批量操作才是大佬的日常，继续加油哦！")
            joke_state['file20'] = True
        elif file_count >= 10 and not joke_state.get('file10'):
            print("文件数量上双，手速跟得上我可爱的嘴炮吗？")
            joke_state['file10'] = True
        if total_lines >= 5000 and not joke_state.get('line5000'):
            print("5000+行代码，眼睛要保护好哦，不然我可要心疼你啦！")
            joke_state['line5000'] = True
        elif total_lines >= 2000 and not joke_state.get('line2000'):
            print("合并内容超过2000行，代码海洋都快淹没我这小小美少女了！")
            joke_state['line2000'] = True
        if '.cs' in file_types:
            real_classes = [c for c in cs_class_infos if not c[0] and not c[1]]
            avg_real_class_len = round(sum(c[3] for c in real_classes)/len(real_classes), 2) if real_classes else 0
            if avg_real_class_len > 200 and not joke_state.get('avg_class_len200'):
                print("欸？你这要成为屎山了吧？美少女架构师在线劝退大类，快拆分一下啦！")
                joke_state['avg_class_len200'] = True
        if error_count > 0 and not joke_state.get('error'):
            print("有文件读取失败啦，别怕，有我罩着你，快检查下路径或权限吧~")
            joke_state['error'] = True
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(stat_str)
            for content in merged_contents:
                outfile.write(content)
        print(f"\n🎉 合并完成，文件已生成：{output_path}")
    except Exception as e:
        print(f"❌ 写入合并文件失败: {e}")
        raise
