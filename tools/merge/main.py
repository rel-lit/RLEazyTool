"""入口：保持 `py main.py` / merge.bat 可用。"""

from venv_bootstrap import ensure_pathspec

from repl import main

if __name__ == "__main__":
    ensure_pathspec(quiet=True)
    main()
