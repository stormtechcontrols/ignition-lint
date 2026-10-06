"""Tests for component type checking against the generated component list."""

import json
import os
import re
import tempfile

import pytest

from ignition_lint.perspective.linter import IgnitionPerspectiveLinter
from ignition_lint.reporting import LintSeverity
from ignition_lint.schemas import schema_path_for

COMPONENT_PROPS = schema_path_for("robust").parent / "component-props.json"


def _lint_root(root):
    """Lint a view whose root component is ``root``; return (linter, issues)."""
    linter = IgnitionPerspectiveLinter()
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "view.json")
    with open(path, "w") as f:
        json.dump({"custom": {}, "params": {}, "props": {}, "root": root}, f)
    try:
        linter.lint_file(path)
    finally:
        os.unlink(path)
        os.rmdir(tmpdir)
    return linter, linter.issues


def _with_code(issues, code):
    return [i for i in issues if i.code == code]


# Components that Ignition 8.3 ships but the hand-written list did not have.
IGNITION_83_TYPES = [
    "ia.display.cylindrical-tank",
    "ia.display.map",
    "ia.display.pdf-viewer",
    "ia.display.sparkline",
    "ia.container.split",
    "ia.input.slider",
    "ia.navigation.link",
    "ia.shapes.circle",
    "ia.symbol.valve",
    "ia.symbol.motor",
    "ia.reporting.report-viewer",
]


class TestKnownComponentTypes:
    @pytest.mark.parametrize("comp_type", IGNITION_83_TYPES)
    def test_ignition_83_component_passes(self, comp_type):
        linter, issues = _lint_root(
            {"type": comp_type, "meta": {"name": "Thing"}, "props": {}}
        )
        assert _with_code(issues, "SCHEMA_VALIDATION") == []
        assert _with_code(issues, "UNKNOWN_COMPONENT_TYPE") == []
        assert linter.component_stats["invalid_components"] == 0

    def test_known_component_with_bad_structure_is_still_an_error(self):
        _, issues = _lint_root(
            {
                "type": "ia.display.label",
                "meta": {"name": "StatusLabel"},
                "props": {"text": "ok"},
                "position": {"grow": -1},
            }
        )
        errors = _with_code(issues, "SCHEMA_VALIDATION")
        assert len(errors) == 1
        assert errors[0].severity == LintSeverity.ERROR
        assert _with_code(issues, "UNKNOWN_COMPONENT_TYPE") == []

    def test_ignition_83_props_are_known(self):
        _, issues = _lint_root(
            {
                "type": "ia.symbol.valve",
                "meta": {"name": "InletValve"},
                "props": {"state": "open", "appearance": "auto"},
            }
        )
        assert _with_code(issues, "UNKNOWN_PROP") == []


@pytest.fixture(scope="module")
def type_schema():
    with open(schema_path_for("robust"), encoding="utf-8") as f:
        return json.load(f)["properties"]["type"]


class TestSchemaConsistency:
    def test_every_listed_type_matches_the_pattern(self, type_schema):
        pattern = re.compile(type_schema["pattern"])
        mismatched = [t for t in type_schema["enum"] if not pattern.match(t)]
        assert mismatched == []

    def test_type_list_is_sorted_and_unique(self, type_schema):
        assert type_schema["enum"] == sorted(set(type_schema["enum"]))

    def test_every_listed_type_has_a_props_entry(self, type_schema):
        with open(COMPONENT_PROPS, encoding="utf-8") as f:
            props = json.load(f)
        missing = [t for t in type_schema["enum"] if t not in props]
        # ia.display.barcode was listed by hand and is not in Ignition 8.3.
        assert missing == ["ia.display.barcode"]
