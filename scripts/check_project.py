#!/usr/bin/env python3
from pathlib import Path
import sys

REQUIRED_DIRS = [
    'docs/bootstrap','docs/architecture','docs/control','docs/handoff',
    'contracts','schemas','scripts','examples','templates','.github'
]

def main():
    root = Path.cwd()
    missing = [d for d in REQUIRED_DIRS if not (root/d).is_dir()]
    if missing:
        for d in missing: print(f'Missing directory: {d}')
        return 1
    print('Project scaffold check passed.')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
