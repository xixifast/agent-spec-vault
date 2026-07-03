from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .vault import (
    append_codex_sessions,
    create_doc,
    ensure_vault,
    filter_docs,
    find_doc,
    index_record,
    iter_docs,
    search_docs,
    split_values,
    vault_home,
    write_index,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specv",
        description="Manage a global Markdown spec and decision vault for AI agents.",
    )
    parser.add_argument("--home", help="Vault directory. Defaults to SPECV_HOME or ~/.agents/spec-vault.")
    parser.add_argument("--version", action="version", version=f"specv {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create the vault directory structure.")

    new_parser = subparsers.add_parser("new", help="Create a new spec.")
    add_doc_args(new_parser)

    decision_parser = subparsers.add_parser("decision", help="Create a new decision note.")
    add_doc_args(decision_parser)

    list_parser = subparsers.add_parser("list", help="List specs and decisions.")
    add_filter_args(list_parser)
    list_parser.add_argument("--limit", type=int, default=50)
    list_parser.add_argument("--json", action="store_true", help="Emit JSONL records.")

    search_parser = subparsers.add_parser("search", help="Search specs and decisions.")
    search_parser.add_argument("query")
    add_filter_args(search_parser)

    show_parser = subparsers.add_parser("show", help="Print one spec or decision.")
    show_parser.add_argument("ref", help="Document id, file name, or path.")

    link_session_parser = subparsers.add_parser("link-session", help="Attach Codex session ids to one document.")
    link_session_parser.add_argument("ref", help="Document id, file name, or path.")
    add_session_args(link_session_parser)

    index_parser = subparsers.add_parser("index", help="Regenerate index.jsonl.")
    index_parser.add_argument("--print", action="store_true", help="Print index path after writing.")

    prime_parser = subparsers.add_parser("prime", help="Print an agent-friendly vault summary.")
    add_filter_args(prime_parser)
    prime_parser.add_argument("--limit", type=int, default=12)

    subparsers.add_parser("path", help="Print the resolved vault directory.")
    return parser


def add_doc_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title")
    parser.add_argument("--repo", "--repos", action="append", dest="repos", help="Repo name(s), comma-separated or repeated.")
    parser.add_argument("--tag", "--tags", action="append", dest="tags", help="Tag(s), comma-separated or repeated.")
    add_session_args(parser)
    parser.add_argument("--status", default="active")


def add_session_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--codex-session", action="append", dest="codex_sessions", help="Codex thread/session id(s), comma-separated or repeated.")
    parser.add_argument("--current-codex-session", action="store_true", help="Attach CODEX_THREAD_ID from the current Codex run.")


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kind", choices=("all", "spec", "decision"), default="all")
    parser.add_argument("--repo")
    parser.add_argument("--tag")
    parser.add_argument("--codex-session")
    parser.add_argument("--status")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    home = vault_home(args.home)

    try:
        if args.command == "init":
            ensure_vault(home)
            print(home)
            return 0
        if args.command == "new":
            path = create_doc(
                home,
                kind="spec",
                title=args.title,
                repos=split_values(args.repos),
                tags=split_values(args.tags),
                codex_sessions=session_values(args),
                status=args.status,
            )
            print(path)
            return 0
        if args.command == "decision":
            path = create_doc(
                home,
                kind="decision",
                title=args.title,
                repos=split_values(args.repos),
                tags=split_values(args.tags),
                codex_sessions=session_values(args),
                status=args.status,
            )
            print(path)
            return 0
        if args.command == "list":
            docs = filtered_docs(home, args)
            docs = docs[: max(args.limit, 0)]
            if args.json:
                for doc in docs:
                    print(json.dumps(index_record(home, doc), ensure_ascii=False))
            else:
                print_list(home, docs)
            return 0
        if args.command == "search":
            docs = filtered_docs(home, args)
            for doc, line_number, snippet in search_docs(docs, args.query):
                location = doc.path.relative_to(home)
                suffix = f":{line_number}" if line_number else ""
                print(f"{doc.id}\t{doc.kind}\t{location}{suffix}\t{snippet}")
            return 0
        if args.command == "show":
            doc = find_doc(home, args.ref)
            print(doc.path.read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "link-session":
            doc = append_codex_sessions(home, args.ref, session_values(args))
            print(doc.path)
            return 0
        if args.command == "index":
            path = write_index(home)
            if args.print:
                print(path)
            return 0
        if args.command == "prime":
            docs = filtered_docs(home, args)[: max(args.limit, 0)]
            print_prime(home, docs)
            return 0
        if args.command == "path":
            print(home)
            return 0
    except (LookupError, ValueError, OSError) as exc:
        print(f"specv: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 2


def filtered_docs(home, args):
    return filter_docs(
        iter_docs(home),
        kind=getattr(args, "kind", "all"),
        repo=getattr(args, "repo", None),
        tag=getattr(args, "tag", None),
        codex_session=getattr(args, "codex_session", None),
        status=getattr(args, "status", None),
    )


def session_values(args) -> list[str]:
    sessions = split_values(getattr(args, "codex_sessions", None))
    if getattr(args, "current_codex_session", False):
        current = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
        if not current:
            raise ValueError("CODEX_THREAD_ID is not set")
        sessions = split_values([*sessions, current])
    return sessions


def print_list(home, docs) -> None:
    if not docs:
        print("No specs or decisions found.")
        return
    for doc in docs:
        path = doc.path.relative_to(home)
        repos = ",".join(doc.repos) or "-"
        tags = ",".join(doc.tags) or "-"
        sessions = ",".join(doc.codex_sessions) or "-"
        status = doc.metadata.get("status", "-")
        print(f"{doc.id}\t{doc.kind}\t{status}\t{doc.updated}\t{repos}\t{tags}\t{sessions}\t{path}\t{doc.title}")


def print_prime(home, docs) -> None:
    print("# Agent Spec Vault")
    print()
    print(f"Vault: `{home}`")
    print()
    if not docs:
        print("No matching specs or decisions found.")
        return
    print("## Relevant Specs And Decisions")
    print()
    for doc in docs:
        repos = ", ".join(doc.repos) or "global"
        tags = ", ".join(doc.tags) or "-"
        sessions = ", ".join(doc.codex_sessions) or "-"
        path = doc.path.relative_to(home)
        print(f"- `{doc.id}` ({doc.kind}, {doc.metadata.get('status', '-')}) {doc.title}")
        print(f"  Path: `{path}`")
        print(f"  Repos: {repos}")
        print(f"  Tags: {tags}")
        print(f"  Codex sessions: {sessions}")
