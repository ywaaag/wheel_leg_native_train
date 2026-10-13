"""Run only explicitly PORTABLE CPU tests; never launch Isaac or read run history."""
import argparse
import ast
from pathlib import Path
import subprocess
import sys


def select(root):
    result=[]
    for path in sorted((Path(root)/'tests').glob('test_*.py')):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FROZEN_TEST_SCOPE' for t in node.targets):
                if ast.literal_eval(node.value)=='PORTABLE':result.append(str(path.relative_to(root)))
                break
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true',help='List selected files without running tests')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];tests=select(root)
    if not tests:raise ValueError('No explicitly PORTABLE tests found')
    if args.list:
        print('\n'.join(tests));return 0
    return subprocess.run([sys.executable,'-m','pytest','-q',*tests],cwd=root).returncode


if __name__=='__main__':raise SystemExit(main())
