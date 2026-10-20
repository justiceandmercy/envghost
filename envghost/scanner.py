"""Core scanning logic for envghost."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

DEFAULT_ENV_FILES = (".env", ".env.local", ".env.development", ".env.production", ".env.test")
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}
DEFAULT_SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rb",
    ".sh",
    ".bash",
    ".zsh",
    ".php",
    ".java",
    ".kt",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".swift",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".txt",
}

ENV_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
REFERENCE_PATTERNS = [
    re.compile(r'os\.environ\[(?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")\]'),
    re.compile(r'os\.environ\.get\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'os\.getenv\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'process\.env\.([A-Za-z_][A-Za-z0-9_]*)'),
    re.compile(r'process\.env\[(?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")\]'),
    re.compile(r'import\.meta\.env\.([A-Za-z_][A-Za-z0-9_]*)'),
    re.compile(r'Deno\.env\.get\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'os\.Getenv\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'os\.LookupEnv\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'ENV\[(?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")\]'),
    re.compile(r'ENV\.fetch\((?:\'|")([A-Za-z_][A-Za-z0-9_]*)(?:\'|")'),
    re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}'),
]


def parse_env_file(path: Path | str) -> dict[str, None]:
    """Return mapping of declared keys to None for one env file."""
    result: dict[str, None] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return result
    for line in lines:
        match = ENV_KEY_RE.match(line)
        if match:
            result[match.group(1)] = None
    return result


def _walk(root: Path, excluded_dirs: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in excluded_dirs]
        for filename in filenames:
            yield Path(dirpath) / filename


def find_env_files(root: Path | str, names: Iterable[str], excluded_dirs: set[str] | None = None) -> list[Path]:
    excluded = excluded_dirs or DEFAULT_EXCLUDE_DIRS
    requested = set(names)
    return sorted(
        path for path in _walk(Path(root), excluded) if path.name in requested
    )


def extract_references(text: str) -> set[str]:
    """Extract references using common language-specific patterns."""
    references: set[str] = set()
    for pattern in REFERENCE_PATTERNS:
        references.update(pattern.findall(text))
    return references


def scan_references(
    root: Path | str,
    declared: set[str],
    env_file_paths: Iterable[Path],
    excluded_dirs: set[str] | None = None,
) -> set[str]:
    excluded = excluded_dirs or DEFAULT_EXCLUDE_DIRS
    env_paths = {str(path) for path in env_file_paths}
    references: set[str] = set()

    for path in _walk(Path(root), excluded):
        if str(path) in env_paths:
            continue
        if path.suffix.lower() not in DEFAULT_SOURCE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        references.update(extract_references(text))

        # Generic fallback: a declared key used as an ordinary identifier.
        for key in declared:
            if key not in references and re.search(r"\b" + re.escape(key) + r"\b", text):
                references.add(key)

    return references


def scan(
    root: Path | str,
    env_file_names: Iterable[str],
    excluded_dirs: set[str] | None = None,
) -> dict[str, object]:
    excluded = excluded_dirs if excluded_dirs is not None else DEFAULT_EXCLUDE_DIRS
    env_files = find_env_files(root, env_file_names, excluded)

    declared: dict[str, None] = {}
    for env_file in env_files:
        declared.update(parse_env_file(env_file))

    declared_keys = set(declared)
    references = scan_references(root, declared_keys, env_files, excluded)

    return {
        "root": str(Path(root).resolve()),
        "env_files": [str(path) for path in env_files],
        "declared": sorted(declared_keys),
        "referenced": sorted(references),
        "unused": sorted(declared_keys - references),
        "missing": sorted(references - declared_keys),
    }