from path_utils import levenshtein_distance, split_camel_case, find_best_match
import os

def test_levenshtein_distance():
    assert levenshtein_distance("abc", "abc") == 0
    assert levenshtein_distance("abc", "ab") == 1
    assert levenshtein_distance("kitten", "sitting") == 3

def test_split_camel_case():
    assert split_camel_case("CamelCaseTest") == ["camel", "case", "test"]
    assert split_camel_case("snake_case_test") == ["snake", "case", "test"]
    assert split_camel_case("Test123") == ["test", "123"]

def test_find_best_match(tmp_path):
    d = tmp_path / "testdir"
    d.mkdir()
    (d / "fooBar").mkdir()
    (d / "baz_qux").mkdir()
    assert find_best_match(str(d), "foobar") == "fooBar"
    assert find_best_match(str(d), "bazqux") == "baz_qux"
    assert find_best_match(str(d), "notfound") is None

def run():
    import tempfile
    from pathlib import Path
    test_levenshtein_distance()
    test_split_camel_case()
    with tempfile.TemporaryDirectory() as tmp:
        test_find_best_match(Path(tmp))
    print("path_utils 单元测试通过")

if __name__ == "__main__":
    run()

