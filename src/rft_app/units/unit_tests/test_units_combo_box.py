"""Guards for UnitsComboBox UnitSystem-only API."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from project.manager import ProjectDataManager  # noqa: E402
from units.units_combo_box import UnitsComboBox  # noqa: E402
from units.units_manager import FIELD_UNITS, UnitSystem  # noqa: E402

SRC_ROOT = APP_ROOT


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _expr_source(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def _units_combo_call_violations(path: Path) -> list[str]:
    """Return messages for UnitsComboBox / set_default_unit args that look like a Project."""
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(path))
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name == "UnitsComboBox":
            if len(node.args) < 2:
                continue
            arg_src = _expr_source(source, node.args[1]).strip()
            # Allowed: …current_unit_system, a UnitSystem name, etc.
            # Forbidden: bare project / self.project / project= without .current_unit_system
            if arg_src in {"project", "self.project"} or (
                arg_src.endswith(".project") and "current_unit_system" not in arg_src
            ):
                violations.append(
                    f"{path.relative_to(SRC_ROOT)}:{node.lineno}: "
                    f"UnitsComboBox(..., {arg_src}) — pass a UnitSystem "
                    f"(e.g. project.current_unit_system)"
                )

        elif func_name == "set_default_unit" and node.args:
            arg_src = _expr_source(source, node.args[0]).strip()
            if arg_src in {"project", "self.project"} or (
                arg_src.endswith(".project") and "current_unit_system" not in arg_src
            ):
                violations.append(
                    f"{path.relative_to(SRC_ROOT)}:{node.lineno}: "
                    f"set_default_unit({arg_src}) — pass a UnitSystem "
                    f"(e.g. project.current_unit_system)"
                )

    return violations


def test_units_combo_box_rejects_project_data_manager(qapp: QApplication) -> None:
    project = ProjectDataManager()
    with pytest.raises(TypeError, match="UnitSystem"):
        UnitsComboBox("length", project)  # type: ignore[arg-type]


def test_units_combo_box_accepts_unit_system(qapp: QApplication) -> None:
    combo = UnitsComboBox("length", FIELD_UNITS)
    assert isinstance(combo.unit_system, UnitSystem)
    assert combo.currentText() == FIELD_UNITS.units_by_quantity["length"]


def test_all_units_combo_box_call_sites_pass_unit_system() -> None:
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        if "unit_tests" in path.parts and path.name == "test_units_combo_box.py":
            # This file intentionally constructs with a Project for the TypeError test
            continue
        violations.extend(_units_combo_call_violations(path))

    assert not violations, "UnitsComboBox must receive a UnitSystem:\n" + "\n".join(
        violations
    )
