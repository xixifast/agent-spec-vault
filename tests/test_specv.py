from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from specv.cli import main
from specv.vault import find_doc, iter_docs, read_doc


class SpecvCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_cli(self, *args: str) -> str:
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(["--home", str(self.home), *args])
        self.assertEqual(code, 0)
        return stream.getvalue()

    def test_init_creates_vault_shape(self) -> None:
        self.run_cli("init")

        self.assertTrue((self.home / "specs").is_dir())
        self.assertTrue((self.home / "decisions").is_dir())
        self.assertTrue((self.home / "templates" / "spec.md").is_file())
        self.assertTrue((self.home / "templates" / "decision.md").is_file())

    def test_create_spec_with_repos_tags_and_index(self) -> None:
        output = self.run_cli(
            "new",
            "质量分析展示契约",
            "--repos",
            "lippi-smart-customer,aics-web-repos",
            "--tags",
            "quality-analysis,contract",
        )
        path = Path(output.strip())
        doc = read_doc(path)

        self.assertEqual(doc.kind, "spec")
        self.assertEqual(doc.title, "质量分析展示契约")
        self.assertEqual(doc.repos, ["lippi-smart-customer", "aics-web-repos"])
        self.assertEqual(doc.tags, ["quality-analysis", "contract"])
        self.assertTrue(doc.id.startswith("spec-"))

        self.run_cli("index")
        records = [
            json.loads(line)
            for line in (self.home / "index.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "质量分析展示契约")

    def test_decision_search_show_and_prime(self) -> None:
        self.run_cli(
            "decision",
            "不用 Beads 管历史 spec",
            "--tags",
            "tooling,specs",
            "--status",
            "accepted",
        )
        docs = iter_docs(self.home)
        self.assertEqual(len(docs), 1)

        search = self.run_cli("search", "Beads")
        self.assertIn("decision", search)
        self.assertIn("不用 Beads 管历史 spec", search)

        shown = self.run_cli("show", docs[0].id)
        self.assertIn("kind: decision", shown)
        self.assertIn("# 不用 Beads 管历史 spec", shown)

        prime = self.run_cli("prime", "--tag", "tooling")
        self.assertIn("# Agent Spec Vault", prime)
        self.assertIn(docs[0].id, prime)

    def test_find_doc_accepts_stem(self) -> None:
        output = self.run_cli("new", "Cross repo contract")
        path = Path(output.strip())
        found = find_doc(self.home, path.stem)

        self.assertEqual(found.path, path)


if __name__ == "__main__":
    unittest.main()
