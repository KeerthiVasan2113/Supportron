#!/usr/bin/env python3
"""Validate repository files for non-PowerShell-friendly shell constructs.

This quick script scans common text/code files and reports occurrences of
`&&` or explicit `bash`/`sh` mentions which are often not PowerShell-friendly.

Exit codes:
 - 0 : no issues found
 - 2 : issues found (printed to stdout)

Run from repository root (PowerShell):
  python .\scripts\validate_powershell_commands.py
"""
import os
import re
import sys

SKIP_DIRS = {".git", "redhat", "node_modules", "venv", "logs", "__pycache__", "dist", "build", "vector_db"}
FILE_EXT_WHITELIST = {".md", ".py", ".sh", ".ps1", ".txt", ".yaml", ".yml", ".json", ".ts", ".tsx", ".js", ".jsx"}
PATTERNS = [re.compile(r"&&"), re.compile(r"\bbash\b"), re.compile(r"\bsh\b")]


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def should_check_file(fname):
    _, ext = os.path.splitext(fname)
    return ext in FILE_EXT_WHITELIST


def main():
    root = repo_root()
    issues = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip known large or irrelevant folders
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not should_check_file(fname):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for n, line in enumerate(fh, start=1):
                        for pat in PATTERNS:
                            if pat.search(line):
                                issues.append((path, n, line.rstrip()))
                                break
            except Exception:
                # ignore unreadable files
                continue

    if issues:
        print("Found potential non-PowerShell constructs:")
        for p, ln, txt in issues:
            print(f"{p}:{ln}: {txt}")
        sys.exit(2)

    print("No obvious non-PowerShell constructs found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
