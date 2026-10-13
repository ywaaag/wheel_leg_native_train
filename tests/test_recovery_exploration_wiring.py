"""Shared actual trainer call-site test; run in original project tree."""

def test_std_intervention_training_branch_after_adam_before_sampling():
    import ast
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'src/native_stand/command_v6/train.py';tree=ast.parse(path.read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    line=next(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=='initialize_exploration')
    restore=next(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=='initialize_adam')
    act=next(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='act')
    assert restore<line<act
    assert len([n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='initialize_exploration'])==1
    # The intervention is inside training else, not deterministic source_eval.
    branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.phase == 'source_eval'")
    assert any(getattr(n,'lineno',None)==line for x in branch.orelse for n in ast.walk(x))
    assert not any(getattr(n,'lineno',None)==line for x in branch.body for n in ast.walk(x))
