"""Thin compatibility entry: all Motion defaults and parsing belong to tools.play."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from native_stand.command_v6.tools.play import main

if __name__=='__main__':
    sys.argv[1:1]=['--preview','--keyboard']
    main()
