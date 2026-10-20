"""Check the integrity of the files in a downloaded public release."""
import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath


def main():
    parser = argparse.ArgumentParser(description="Verify public release file hashes")
    parser.add_argument("--strict", action="store_true", help="Also reject unlisted files outside .git, outputs, and caches")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "PUBLIC_MANIFEST.json").read_text(encoding="utf-8"))
    failures = []
    seen = set()
    for entry in manifest["files"]:
        name = entry["path"]
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            failures.append("unsafe manifest path")
            continue
        if name in seen:
            failures.append(f"duplicate manifest entry: {name}")
            continue
        seen.add(name)
        filename = (root / name).resolve()
        try:
            filename.relative_to(root)
            content = filename.read_bytes()
        except (OSError, ValueError):
            failures.append(f"missing or unsafe file: {name}")
            continue
        digest = hashlib.sha256(content).hexdigest()
        if len(content) != entry["bytes"] or digest != entry["sha256"]:
            failures.append(f"modified file: {name}")
    if args.strict:
        allowed = seen | {"PUBLIC_MANIFEST.json"}
        for filename in root.rglob("*"):
            relative = filename.relative_to(root)
            if any(part in (".git", "outputs", "__pycache__") for part in relative.parts):
                continue
            if filename.is_file() and relative.as_posix() not in allowed:
                failures.append(f"unlisted file: {relative.as_posix()}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Verified {len(manifest['files'])} listed public files. "
          "This checks integrity, not model correctness or authorship.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
