from ignition_lint.cli import determine_checks
from ignition_lint.json_linter import JsonLinter


def test_determine_checks_profile_defaults():
    assert determine_checks("default", None, False) == {
        "perspective",
        "naming",
        "scripts",
    }


def test_determine_checks_naming_only():
    assert determine_checks("default", None, True) == {"naming"}


def test_determine_checks_explicit():
    assert determine_checks("default", "perspective,scripts", False) == {
        "perspective",
        "scripts",
    }


class TestRootComponentNaming:
    """The 'root' component name is Ignition-assigned and should not be flagged."""

    def test_root_name_not_flagged(self):
        linter = JsonLinter(component_style="PascalCase")
        data = {
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "root"},
                "children": [],
            }
        }
        linter._check_json_structure(data, "test.json")
        component_errors = [e for e in linter.errors if e.error_type == "component"]
        flagged_names = {e.name for e in component_errors}
        assert "root" not in flagged_names

    def test_non_pascalcase_name_still_flagged(self):
        linter = JsonLinter(component_style="PascalCase")
        data = {
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "bad_name"},
                "children": [],
            }
        }
        linter._check_json_structure(data, "test.json")
        component_errors = [e for e in linter.errors if e.error_type == "component"]
        flagged_names = {e.name for e in component_errors}
        assert "bad_name" in flagged_names

    def test_pascalcase_name_passes(self):
        linter = JsonLinter(component_style="PascalCase")
        data = {
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "MyContainer"},
                "children": [],
            }
        }
        linter._check_json_structure(data, "test.json")
        component_errors = [e for e in linter.errors if e.error_type == "component"]
        assert len(component_errors) == 0


def test_version_flag_prints_installed_version(capsys, monkeypatch):
    """Scripts compare it with the build they pin (storm-tooling#38)."""
    import pytest

    from ignition_lint import __version__
    from ignition_lint.cli import parse_args

    monkeypatch.setattr("sys.argv", ["ignition-lint", "--version"])
    with pytest.raises(SystemExit) as exc:
        parse_args()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"ignition-lint {__version__}"
