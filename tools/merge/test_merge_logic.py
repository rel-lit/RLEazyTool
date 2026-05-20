from actions import Action
from input_parser import parse_input
from exclude_rules import FileExcludeRule, filename_excluded, walk_skip_dir_names
from merge_engine import MergeRunOptions, collect_candidate_paths, run_merge
from merge_report import write_merged_output
from scope_rules import ScopeContext, file_in_merge_scope


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
        merge_max_depth=None,
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


def test_merge_max_depth_zero_skips_subfolders(tmp_path):
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
        merge_max_depth=0,
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "root.cs" in text
    assert "// root" in text
    assert "nested.cs" not in text
    assert "// nested" not in text


def test_merge_max_depth_one(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "root.cs").write_text("// root")
    core = root / "Core"
    core.mkdir()
    (core / "in.cs").write_text("// in")
    deep = core / "Sub"
    deep.mkdir()
    (deep / "deep.cs").write_text("// deep")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(root),
        output_path=str(output),
        file_types=(".cs",),
        merge_max_depth=1,
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "root.cs" in text
    assert "in.cs" in text or "Core\\in.cs" in text
    assert "deep.cs" not in text


def test_collect_candidate_paths_sorted(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "z.cs").write_text("// z")
    (d / "a.cs").write_text("// a")
    paths, err = collect_candidate_paths(str(d), (".cs",), (), (), None, (), ())
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
        merge_max_depth=None,
        only_relative_paths=("pick.cs",),
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "pick.cs" in text
    assert "picked" in text
    assert "skip.cs" not in text


def test_scope_exclude_subfolder(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "keep.cs").write_text("// keep")
    core = root / "Core"
    core.mkdir()
    (core / "in.cs").write_text("// in")
    skip = root / "Skip"
    skip.mkdir()
    (skip / "out.cs").write_text("// out")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(root),
        output_path=str(output),
        file_types=(".cs",),
        merge_max_depth=None,
        merge_scope_exclude=("Skip",),
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "keep.cs" in text
    assert "Core/in.cs" in text or "Core\\in.cs" in text
    assert "out.cs" not in text


def test_file_in_merge_scope_rules(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "Sub").mkdir()
    src = str(root)

    def ctx(depth, exc=(), inc=()):
        return ScopeContext.create(src, depth, exc, inc)

    assert file_in_merge_scope("a.cs", ctx(None)) is True
    assert file_in_merge_scope("Sub/a.cs", ctx(None, ("Sub",), ())) is False
    assert file_in_merge_scope("Sub/a.cs", ctx(None, ("Sub",), ("Sub",))) is True
    assert file_in_merge_scope("only.cs", ctx(0)) is True
    assert file_in_merge_scope("Sub/x.cs", ctx(0)) is False
    assert file_in_merge_scope("Sub/x.cs", ctx(1)) is True
    assert file_in_merge_scope("A/B/x.cs", ctx(1)) is False


def test_exc_filename_rules():
    rules = (
        FileExcludeRule("contains", "Generated"),
        FileExcludeRule("suffix", ".Designer.cs"),
        FileExcludeRule("glob", "*.g.cs"),
    )
    assert filename_excluded("Foo.Generated.cs", rules)
    assert filename_excluded("X.Designer.cs", rules)
    assert filename_excluded("a.g.cs", rules)
    assert not filename_excluded("Plain.cs", rules)


def test_exc_skip_dirs_merge_builtin():
    merged = walk_skip_dir_names(("CustomDir",))
    assert "bin" in merged
    assert "CustomDir" in merged


def test_merge_exc_skip_dir(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "keep.cs").write_text("// k")
    custom = root / "CustomDir"
    custom.mkdir()
    (custom / "skip.cs").write_text("// s")
    output = tmp_path / "out.txt"
    opts = MergeRunOptions(
        source_dir=str(root),
        output_path=str(output),
        file_types=(".cs",),
        exc_skip_dirs=("CustomDir",),
    )
    result = run_merge(opts)
    write_merged_output(str(output), result)
    text = output.read_text(encoding="utf-8")
    assert "keep.cs" in text
    assert "skip.cs" not in text


def test_parse_exc_commands():
    assert parse_input("exc", 0) == (Action.EXC, ("last", None))
    assert parse_input("exc off", 0) == (Action.EXC, ("off", None))
    assert parse_input("exc u dev", 0) == (Action.EXC, ("use", "dev"))
    assert parse_input("exc a dev", 0) == (Action.EXC, ("group_add", "dev"))
    assert parse_input("exc dir a dev bin obj", 0) == (
        Action.EXC,
        ("dir_add", ("dev", ["bin", "obj"])),
    )
    assert parse_input("exc f a dev suffix .Designer.cs", 0) == (
        Action.EXC,
        ("f_add", ("dev", "suffix", ".Designer.cs")),
    )


def test_parse_this_commands():
    assert parse_input("this", 0) == (Action.THIS, ("toggle", None))
    assert parse_input("this 0", 0) == (Action.THIS, ("set_depth", 0))
    assert parse_input("this 2", 0) == (Action.THIS, ("set_depth", 2))
    assert parse_input("this max", 0) == (Action.THIS, ("set_depth", None))
    assert parse_input("this ll", 0) == (Action.THIS, ("list", 0))
    assert parse_input("this ll 0", 0) == (Action.THIS, ("list", 0))
    assert parse_input("this ll 2", 0) == (Action.THIS, ("list", 2))
    assert parse_input("this ll all", 0) == (Action.THIS, ("list_all", None))
    assert parse_input("this s Core", 0) == (Action.THIS, ("exclude", ["Core"]))


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
        test_merge_max_depth_zero_skips_subfolders(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_max_depth_one(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_collect_candidate_paths_sorted(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_only_relative_paths(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_scope_exclude_subfolder(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_file_in_merge_scope_rules(Path(tmp))
    test_exc_filename_rules()
    test_exc_skip_dirs_merge_builtin()
    with tempfile.TemporaryDirectory() as tmp:
        test_merge_exc_skip_dir(Path(tmp))
    test_parse_exc_commands()
    test_parse_this_commands()
    test_parse_c_commands()
    print("merge_engine 单元测试通过")


if __name__ == "__main__":
    run()
