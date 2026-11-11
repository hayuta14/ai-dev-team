"""Regression tests for type-safety-check rules (one finding per construct,
non-null assertion). Rules are matched against single source lines — the
framework scans line by line — so no filesystem is involved.
"""
import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scan-typescript-files-for-weak-types-and-assertions.py"
)
_spec = importlib.util.spec_from_file_location("type_safety_scanner_under_test", SCRIPT_PATH)
scanner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanner)


def labels_for(line):
    """Label of every match of every rule on `line` (duplicates kept)."""
    return [rule[2] for rule in scanner.PATTERNS for _ in rule[0].finditer(line)]


def test_type_safety_double_cast_reported_once_as_double_cast():
    # Arrange
    line = "const bar = foo as unknown as Bar;"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["double cast (as unknown as)"]


def test_type_safety_double_cast_to_any_reported_once_as_double_cast():
    # Arrange
    line = "const bar = foo as unknown as any;"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["double cast (as unknown as)"]


def test_type_safety_any_array_annotation_reported_once_as_any_array():
    # Arrange
    line = "const list: any[] = [];"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["any array"]


def test_type_safety_plain_any_annotation_still_reported():
    # Arrange
    line = "function handle(event: any) {}"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["any type annotation"]


def test_type_safety_single_as_cast_still_reported_low():
    # Arrange
    line = "const cfg = raw as Config;"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["as cast"]


def test_type_safety_non_null_assertion_reported_low():
    # Arrange
    lines = [
        'const el = document.getElementById("x")!;',
        "const n = foo!.bar;",
        "use(items[0]!);",
        'const el = document.getElementById("x")!',
    ]
    # Act
    results = [labels_for(line) for line in lines]
    # Assert
    assert results == [["non-null assertion (!)"]] * 4


def test_type_safety_inequality_and_logical_not_not_reported():
    # Arrange
    line = 'if (a != b && a !== c && !flag && x!==y) { alert("Saved! ok"); }'
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == []
