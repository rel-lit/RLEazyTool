import os
from merge_logic import merge_files_by_types

def test_merge_files_by_types(tmp_path):
    # 创建测试文件夹和文件
    d = tmp_path / "src"
    d.mkdir()
    f1 = d / "a.cs"
    f2 = d / "b.txt"
    f1.write_text("public class A {\npublic void Foo(){}\n}")
    f2.write_text("hello\nworld")
    output = tmp_path / "out.txt"
    merge_files_by_types(str(d), str(output), [".cs", ".txt"])
    content = output.read_text(encoding="utf-8")
    assert "class" in content
    assert "hello" in content
    assert "world" in content
    assert "合并统计" in content

def run():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        test_merge_files_by_types(Path(tmp))
        print("merge_logic 单元测试通过")

if __name__ == "__main__":
    run()

