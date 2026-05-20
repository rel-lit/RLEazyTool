from input_parser import parse_input
from merge_engine import MergeRunOptions, collect_candidate_paths, run_merge
from merge_report import write_merged_output
from actions import Action


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
    assert "文件分析" in content
    assert "a.cs" in content


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


def test_collect_candidate_paths_sorted(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "z.cs").write_text("// z")
    (d / "a.cs").write_text("// a")
    paths, err = collect_candidate_paths(str(d), (".cs",), (), True, False)
    assert err is None
    assert paths == ["a.cs", "z.cs"]


def test_merge_only_relative_paths(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "pick.cs").write_text("picked")
    (d / "skip.cs").write_text("skipped")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(d),
        output_path=str(output),
        file_types=(".cs",),
        recursive=True,
        only_relative_paths=("pick.cs",),
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "pick.cs" in text
    assert "picked" in text
    assert "skip.cs" not in text


def test_parse_c_commands():
    assert parse_input("c", 0) == (Action.CHOOSE, ("toggle", None))
    assert parse_input("c ll", 0) == (Action.CHOOSE, ("list", None))
    assert parse_input("c 3 5", 0) == (Action.CHOOSE, ("select", ["3", "5"]))
    assert parse_input("c s 2", 0) == (Action.CHOOSE, ("deselect", ["2"]))
    assert parse_input("c all", 0) == (Action.CHOOSE, ("select_all", None))
    assert parse_input("c limit 80", 0) == (Action.CHOOSE, ("limit_set", "80"))


def run():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_files_by_types(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_non_recursive_skips_subfolders(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_collect_candidate_paths_sorted(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_only_relative_paths(Path(tmp))
    test_parse_c_commands()
    print("merge_engine 单元测试通过")


if __name__ == "__main__":
    run()
