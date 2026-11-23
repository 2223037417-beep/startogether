import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import new_entry
import validate_pr as gate


def instant(value):
    return datetime.fromisoformat(value + "+00:00")


class Entries(unittest.TestCase):
    def test_beijing_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for utc, expected in [
                ("2026-11-23T15:59:59", "26/11/23"),
                ("2026-11-23T16:00:00", "26/11/24"),
                ("2026-01-31T16:00:00", "26/02/01"),
                ("2026-12-31T16:00:00", "27/01/01"),
                ("2024-02-28T16:00:00", "24/02/29"),
            ]:
                path, created = new_entry.create_entry("Alice", root, instant(utc))
                self.assertTrue(created)
                self.assertEqual(path, root / "journal" / expected / "alice.md")
                self.assertIn("- [ ]", path.read_text(encoding="utf-8"))

    def test_concurrent_creations_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            def create(login):
                return new_entry.create_entry(login, root, instant("2026-11-23T00:00"))
            with ThreadPoolExecutor(3) as pool:
                results = list(pool.map(create, ["Alice", "alice", "bob"]))
            self.assertEqual(sum(created for _, created in results), 2)
            path = results[0][0]
            path.write_text("我的正文", encoding="utf-8")
            self.assertEqual(create("ALICE"), (path, False))
            self.assertEqual(path.read_text(encoding="utf-8"), "我的正文")

    def test_private_note_stays_outside_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            repo = home / "checkout"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            now = instant("2026-11-23T16:00:00")
            with patch.object(Path, "home", return_value=home):
                note, marker = new_entry.create_private_entry("Alice", repo, now)
                note.write_text("private draft", encoding="utf-8")
                self.assertEqual(new_entry.create_private_entry("alice", repo, now), (note, marker))
                self.assertEqual(note.read_text(encoding="utf-8"), "private draft")
                self.assertEqual(marker.read_bytes(), b"")
                subprocess.run(["git", "add", "."], cwd=repo, check=True)
                staged = subprocess.check_output(["git", "ls-files"], cwd=repo).decode().strip()
                self.assertEqual(staged, "journal/26/11/24/alice.md")
                marker.write_text("shared excerpt", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "已有正文"):
                    new_entry.create_private_entry("alice", repo, now)
                self.assertEqual(marker.read_text(encoding="utf-8"), "shared excerpt")

    def test_invalid_names(self):
        for name in ["../bob", "-a", "a--b", "a/b", "a\\b", "a" * 40, "ａ", "a\n"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                new_entry.username(name)


def pr(login="Alice"):
    return {"base": {"ref": "main"}, "user": {"login": login, "id": 17},
            "created_at": "2026-11-22T16:00:00Z"}


def record(path="journal/26/11/23/alice.md", status="A", old="000000", new="100644"):
    return f":{old} {new} 0000000 aaaaaaa {status}\0{path}\0".encode()


class Policy(unittest.TestCase):
    def test_independent_prs(self):
        def check(login):
            gate.validate(pr(login), record(f"journal/26/11/23/{login}.md"), None, lambda _: [])
        with ThreadPoolExecutor(3) as pool:
            list(pool.map(check, ["alice", "bob", "cathy"]))

    def test_same_day_after_rename(self):
        with self.assertRaisesRegex(ValueError, "当天已有"):
            gate.validate(pr(), record(), lambda _: 17, lambda _: ["journal/26/11/23/old.md"])
        gate.validate(pr(), record(), lambda _: 42, lambda _: ["journal/26/11/23/bob.md"])

    def test_historical_owner(self):
        raw = record("journal/22/09/10/alice.md", "M", "100644")
        gate.validate(pr(), raw, lambda path: 17, None)
        with self.assertRaisesRegex(ValueError, "ID"):
            gate.validate(pr(), raw, lambda path: 33, None)

    def test_rejected_changes(self):
        for raw in [
            b"", record() * 2, record("README.md"), record(".github/workflows/journal.yml"),
            record("tools/validate_pr.py"), record("journal/26/11/23/bob.md"),
            record("journal/26/11/23/../alice.md"), record("journal/26/11/23/Alice.md"),
            record("journal/26/2/03/alice.md"), record("journal/26/02/29/alice.md"),
            record("journal/26/11/23/alice.md\n"), record("journal/26/11/24/alice.md"),
            record(status="D", old="100644", new="000000"), record(status="R100"),
            record(status="D") + record(), record(new="120000"), record(new="100755"),
            record(new="160000"),
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                gate.validate(pr(), raw, lambda path: 17, None)

    def test_actual_pr_git_objects(self):
        # Exercise the production command against a local origin and PR ref.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "upstream"
            origin.mkdir()
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=origin).decode().strip()
            git("init", "-q", "-b", "main")
            git("config", "user.name", "Bob")
            git("config", "user.email", "bob@example.invalid")
            git("config", "commit.gpgsign", "false")
            git("commit", "-q", "--allow-empty", "-m", "base")
            base = git("rev-parse", "HEAD")
            path = origin / "journal/26/11/23/bob.md"
            path.parent.mkdir(parents=True)
            path.write_text("progress")
            git("add", "journal")
            git("commit", "-qm", "entry")
            head = git("rev-parse", "HEAD")
            git("update-ref", "refs/pull/1/head", head)
            clone = root / "validator"
            git("clone", "-q", "--no-checkout", str(origin), str(clone))
            event = root / "event.json"
            def run(login):
                metadata = pr(login)
                metadata["base"]["sha"] = base
                metadata["head"] = {"sha": head}
                event.write_text(json.dumps({"number": 1, "pull_request": metadata}))
                return subprocess.run([sys.executable, str(TOOLS / "validate_pr.py")],
                                      cwd=clone, capture_output=True, text=True,
                                      env=dict(os.environ, GITHUB_EVENT_PATH=str(event)))
            self.assertEqual(run("Bob").returncode, 0)
            self.assertIn("alice.md", run("Alice").stderr)

    def test_creation_pr_resolution(self):
        sha = "f" * 40
        original = {"merged_at": "2026-11-24", "merge_commit_sha": sha,
                    "user": {"id": 17}, "base": {"repo": {"full_name": "a/b"}, "ref": "main"}}
        for records in [[original], [], [original, original]]:
            reply = BytesIO(json.dumps(records).encode())
            reply.headers = {}
            with patch.object(gate, "git", return_value=sha.encode()), patch.object(
                gate, "urlopen", return_value=reply
            ), patch.dict(os.environ, GH_TOKEN="test"):
                if len(records) == 1:
                    self.assertEqual(gate.historical_owner(sha, "entry", "a/b"), 17)
                else:
                    with self.assertRaises(ValueError):
                        gate.historical_owner(sha, "entry", "a/b")
