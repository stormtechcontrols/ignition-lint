"""Tests for the project-library script linter (code.py files)."""

from ignition_lint.scripts.linter import IgnitionScriptLinter


def _codes_for(tmp_path, source):
    lib = tmp_path / "script-python" / "lib"
    lib.mkdir(parents=True)
    (lib / "code.py").write_text(source, encoding="utf-8")
    linter = IgnitionScriptLinter()
    linter.lint_directory(str(tmp_path))
    return {issue.code for issue in linter.issues}


def test_except_comma_is_valid_jython(tmp_path):
    """``except Exception, e:`` is Jython 2.7 syntax (storm-tooling#38)."""
    source = (
        "def run(log):\n"
        "    try:\n"
        "        pass\n"
        "    except Exception, e:\n"
        "        log.warn(\"%s\" % e)\n"
    )
    assert "SYNTAX_ERROR" not in _codes_for(tmp_path, source)


def test_genuine_syntax_error_still_reported(tmp_path):
    assert "SYNTAX_ERROR" in _codes_for(tmp_path, "def run(:\n    pass\n")
