#!/usr/bin/env python3
from pathlib import Path
from collections import Counter, defaultdict

SKIP_DIRS = {
    ".git", ".github", "__pycache__", ".pytest_cache",
    "node_modules", ".venv", "venv", "dist", "build"
}

EXT_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".sh": "Shell",
    ".rb": "Ruby",
    ".pl": "Perl",
    ".r": "R",
    ".java": "Java",
    ".json": "JSON",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".csv": "CSV",
}

def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)

def main() -> None:
    root = Path(".")
    counts = Counter()
    files_by_lang = defaultdict(list)

    for path in root.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue

        lang = EXT_TO_LANG.get(path.suffix.lower(), "Other")
        counts[lang] += 1
        files_by_lang[lang].append(path)

    print("\nRepo inventory\n==============")
    for lang, count in counts.most_common():
        print(f"{lang:12} {count}")

    print("\nFiles by language\n=================")
    for lang in sorted(files_by_lang):
        print(f"\n{lang}")
        for path in sorted(files_by_lang[lang]):
            print(f"  - {path}")

if __name__ == "__main__":
    main()
