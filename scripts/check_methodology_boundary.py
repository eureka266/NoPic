"""Check that the tracked methodology tree carries no production media or asset library."""
from pathlib import Path
import subprocess

from methodology_policy import violation


def violations(root):
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, text=True, check=True)
    errors = []
    for relative in result.stdout.split('\0'):
        if not relative:
            continue
        path = root / relative
        if not path.is_file():
            continue
        problem = violation(relative, root)
        if problem:
            errors.append(relative + ': ' + problem)
    return errors


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    errors = violations(root)
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print('Methodology boundary check passed: no tracked production media or asset library.')
