import pathlib
import re
import sys

PATTERNS = (
    re.compile(r"^\s*from\s+src(\.|\s|$)"),
    re.compile(r"^\s*import\s+src(\.|\s|$)"),
)

errors = []

repo_root = pathlib.Path(__file__).parent.parent.resolve()
src_dir = repo_root / "src"

if not src_dir.is_dir():
    print(f"Error: 'src' directory not found at {src_dir}")
    sys.exit(1)

for path in src_dir.rglob("*.py"):
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(p.match(line) for p in PATTERNS):
            errors.append(f"{path}:{lineno}: {line.strip()}")

if errors:
    print("Imports from 'src' are forbidden:")
    print(*errors, sep="\n")
    sys.exit(1)
