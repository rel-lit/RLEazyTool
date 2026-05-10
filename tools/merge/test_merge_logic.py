from merge_engine import MergeRunOptions, run_merge
from merge_report import write_merged_output


def test_merge_files_by_types(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    f1 = d / "a.cs"
    f2 = d / "b.txt"
    f1.write_text("public class A {\npublic void Foo(){}\n}")
    f2.write_text("hello\nworld")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(d),
        output_path=str(output),
        file_types=(".cs", ".txt"),
        recursive=True,
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    content = output.read_text(encoding="utf-8")
    assert "class" in content
    assert "hello" in content
    assert "world" in content
    assert "合并统计" in content


def test_merge_non_recursive_skips_subfolders(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "root.cs").write_text("// root")
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.cs").write_text("// nested")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(root),
        output_path=str(output),
        file_types=(".cs",),
        recursive=False,
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "root.cs" in text
    assert "// root" in text
    assert "nested.cs" not in text
    assert "// nested" not in text


def run():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_files_by_types(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_non_recursive_skips_subfolders(Path(tmp))
    print("merge_engine 单元测试通过")


if __name__ == "__main__":
    run()
