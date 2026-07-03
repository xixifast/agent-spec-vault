from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_HOME = Path("~/.agents/spec-vault").expanduser()
SPEC_TEMPLATE = """# {title}

## Background

## Goals

## Non-Goals

## Repositories

## Contract

## Verification

## Decisions
"""
DECISION_TEMPLATE = """# {title}

## Context

## Decision

## Consequences

## Related Specs
"""


@dataclass(frozen=True)
class VaultDoc:
    path: Path
    metadata: dict[str, object]
    body: str

    @property
    def id(self) -> str:
        return str(self.metadata.get("id", self.path.stem))

    @property
    def kind(self) -> str:
        return str(self.metadata.get("kind", "spec"))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.path.stem))

    @property
    def updated(self) -> str:
        return str(self.metadata.get("updated", ""))

    @property
    def repos(self) -> list[str]:
        value = self.metadata.get("repos", [])
        return value if isinstance(value, list) else []

    @property
    def tags(self) -> list[str]:
        value = self.metadata.get("tags", [])
        return value if isinstance(value, list) else []

    @property
    def codex_sessions(self) -> list[str]:
        value = self.metadata.get("codex_sessions", [])
        return value if isinstance(value, list) else []


def vault_home(value: str | None = None) -> Path:
    if value:
        return normalize_home(Path(value))
    if os.environ.get("SPECV_HOME"):
        return normalize_home(Path(os.environ["SPECV_HOME"]))
    return normalize_home(DEFAULT_HOME)


def normalize_home(home: Path) -> Path:
    return home.expanduser().resolve()


def ensure_vault(home: Path) -> None:
    home = normalize_home(home)
    for dirname in ("specs", "decisions", "templates"):
        (home / dirname).mkdir(parents=True, exist_ok=True)
    write_if_missing(home / "templates" / "spec.md", SPEC_TEMPLATE)
    write_if_missing(home / "templates" / "decision.md", DECISION_TEMPLATE)
    write_if_missing(
        home / "README.md",
        "# Agent Spec Vault\n\n"
        "Global Markdown specs and decisions for AI coding agents.\n\n"
        "- `specs/`: durable specifications and cross-repo contracts\n"
        "- `decisions/`: ADR-style decisions and rationale\n"
        "- `index.jsonl`: generated search/index surface\n",
    )


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def split_values(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for raw in values:
        for part in raw.split(","):
            value = part.strip()
            if value and value not in result:
                result.append(value)
    return result


def slugify(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
    if slug:
        return slug[:72].strip("-")
    return hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]


def today() -> str:
    return dt.date.today().isoformat()


def compact_date(value: str) -> str:
    return value.replace("-", "")


def create_doc(
    home: Path,
    *,
    kind: str,
    title: str,
    repos: list[str],
    tags: list[str],
    codex_sessions: list[str],
    status: str,
) -> Path:
    home = normalize_home(home)
    ensure_vault(home)
    created = today()
    slug = slugify(title)
    prefix = "decision" if kind == "decision" else "spec"
    doc_id = unique_id(home, prefix, compact_date(created), slug)
    directory = home / ("decisions" if kind == "decision" else "specs")
    path = unique_path(directory / f"{created}-{slug}.md")
    metadata = {
        "id": doc_id,
        "kind": kind,
        "title": clean_scalar(title),
        "status": status,
        "created": created,
        "updated": created,
        "repos": repos,
        "tags": tags,
        "codex_sessions": codex_sessions,
    }
    template = DECISION_TEMPLATE if kind == "decision" else SPEC_TEMPLATE
    content = render_frontmatter(metadata) + "\n" + template.format(title=title)
    path.write_text(content, encoding="utf-8")
    return path.resolve()


def clean_scalar(value: str) -> str:
    return " ".join(value.split())


def unique_id(home: Path, prefix: str, date_part: str, slug: str) -> str:
    base = f"{prefix}-{date_part}-{slug}"
    existing = {doc.id for doc in iter_docs(home)}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def render_frontmatter(metadata: dict[str, object]) -> str:
    scalar_keys = ("id", "kind", "title", "status", "created", "updated")
    list_keys = ("repos", "tags", "codex_sessions")
    known = set(scalar_keys) | set(list_keys)
    lines = ["---"]
    for key in scalar_keys:
        lines.append(f"{key}: {metadata.get(key, '')}")
    for key in list_keys:
        values = metadata.get(key, [])
        lines.append(f"{key}:")
        if isinstance(values, list):
            for value in values:
                lines.append(f"  - {value}")
    for key in sorted(metadata):
        if key in known:
            continue
        value = metadata[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def iter_docs(home: Path) -> list[VaultDoc]:
    home = normalize_home(home)
    docs: list[VaultDoc] = []
    for dirname in ("specs", "decisions"):
        root = home / dirname
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            try:
                docs.append(read_doc(path))
            except ValueError:
                continue
    return docs


def read_doc(path: Path) -> VaultDoc:
    path = path.expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return VaultDoc(path=path, metadata={}, body=text)
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"unterminated frontmatter: {path}")
    raw_meta = text[4:end]
    body = text[end + 5 :]
    return VaultDoc(path=path, metadata=parse_frontmatter(raw_meta), body=body)


def parse_frontmatter(raw: str) -> dict[str, object]:
    metadata: dict[str, object] = {}
    current_list: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list:
            value = line[4:].strip()
            current = metadata.setdefault(current_list, [])
            if isinstance(current, list):
                current.append(value)
            continue
        current_list = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            metadata[key] = value
        else:
            metadata[key] = []
            current_list = key
    return metadata


def filter_docs(
    docs: Iterable[VaultDoc],
    *,
    kind: str | None = None,
    repo: str | None = None,
    tag: str | None = None,
    codex_session: str | None = None,
    status: str | None = None,
) -> list[VaultDoc]:
    filtered: list[VaultDoc] = []
    for doc in docs:
        if kind and kind != "all" and doc.kind != kind:
            continue
        if repo and repo not in doc.repos:
            continue
        if tag and tag not in doc.tags:
            continue
        if codex_session and codex_session not in doc.codex_sessions:
            continue
        if status and doc.metadata.get("status") != status:
            continue
        filtered.append(doc)
    return sorted(filtered, key=lambda item: (item.updated, item.id), reverse=True)


def find_doc(home: Path, ref: str) -> VaultDoc:
    home = normalize_home(home)
    candidate = Path(ref).expanduser()
    if candidate.exists():
        return read_doc(candidate)
    for doc in iter_docs(home):
        if ref in {doc.id, doc.path.stem, doc.path.name}:
            return doc
    raise LookupError(f"no spec or decision found for {ref!r}")


def append_codex_sessions(home: Path, ref: str, sessions: list[str]) -> VaultDoc:
    if not sessions:
        raise ValueError("at least one Codex session id is required")
    doc = find_doc(home, ref)
    metadata = dict(doc.metadata)
    existing = doc.codex_sessions
    metadata["codex_sessions"] = merge_unique(existing, sessions)
    metadata["updated"] = today()
    write_doc(doc.path, metadata, doc.body)
    return read_doc(doc.path)


def merge_unique(existing: Iterable[str], additions: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in [*existing, *additions]:
        item = str(value).strip()
        if item and item not in result:
            result.append(item)
    return result


def write_doc(path: Path, metadata: dict[str, object], body: str) -> None:
    path.write_text(render_frontmatter(metadata) + "\n" + body, encoding="utf-8")


def write_index(home: Path) -> Path:
    home = normalize_home(home)
    ensure_vault(home)
    index_path = home / "index.jsonl"
    with index_path.open("w", encoding="utf-8") as stream:
        for doc in iter_docs(home):
            stream.write(json.dumps(index_record(home, doc), ensure_ascii=False) + "\n")
    return index_path


def index_record(home: Path, doc: VaultDoc) -> dict[str, object]:
    home = normalize_home(home)
    return {
        "id": doc.id,
        "kind": doc.kind,
        "title": doc.title,
        "status": doc.metadata.get("status", ""),
        "created": doc.metadata.get("created", ""),
        "updated": doc.updated,
        "repos": doc.repos,
        "tags": doc.tags,
        "codex_sessions": doc.codex_sessions,
        "path": str(doc.path.relative_to(home)),
        "summary": first_content_line(doc.body),
    }


def first_content_line(body: str) -> str:
    for line in body.splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            return text
    return ""


def search_docs(docs: Iterable[VaultDoc], query: str) -> list[tuple[VaultDoc, int, str]]:
    needle = query.lower()
    matches: list[tuple[VaultDoc, int, str]] = []
    for doc in docs:
        haystack = json.dumps(doc.metadata, ensure_ascii=False).lower()
        if needle in haystack:
            matches.append((doc, 0, doc.title))
            continue
        for line_number, line in enumerate(doc.body.splitlines(), start=1):
            if needle in line.lower():
                matches.append((doc, line_number, line.strip()))
                break
    return matches
