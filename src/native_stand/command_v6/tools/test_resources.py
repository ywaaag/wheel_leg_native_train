"""Test resource locators follow imported code; project history is explicit optional IO."""
import ast
from pathlib import Path
import native_stand


def source_file(relative):
    root=Path(native_stand.__file__).resolve().parent
    path=(root/relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():raise ValueError('Imported source resource missing: '+relative)
    return path


def project_file(relative):
    """Returns None in a standalone frozen validation tree: callers skip history tests."""
    for root in Path(native_stand.__file__).resolve().parents:
        if (root/'AGENTS.md').is_file() and (root/'README.md').is_file():
            path=(root/relative).resolve()
            if not path.is_relative_to(root):raise ValueError('Project resource escapes root')
            return path if path.is_file() else None
    return None


def scope(path):
    tree=ast.parse(Path(path).read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='FROZEN_TEST_SCOPE' for n in node.targets):
            value=ast.literal_eval(node.value)
            if value not in ('PORTABLE','PROJECT_DATA'):raise ValueError('Invalid frozen test scope')
            return value
    return 'UNCLASSIFIED'
