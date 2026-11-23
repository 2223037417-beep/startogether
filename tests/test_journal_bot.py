"""Drive the production decision with GitHub responses and immutable diff fixtures."""
import copy
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import journal_bot as bot
import validate_pr

gh_adapter = bot.gh


class Platform:
    def __init__(self, number=1, login="alice"):
        self.head = f"{number:040x}"
        self.base = "a" * 40
        self.run_url = f"https://github.com/org/repo/actions/runs/{number}/attempts/1"
        self.bot = bot.Bot("org/repo", number, self.head, 22, self.run_url)
        self.pr = {"number": number, "base": {"repo": {"full_name": "org/repo"},
                   "ref": "main", "sha": self.base}, "head": {"sha": self.head},
                   "merged": False, "state": "open", "draft": False, "auto_merge": None,
                   "mergeable": True, "mergeable_state": "clean", "changed_files": 1,
                   "created_at": "2026-11-22T16:00:00Z", "user": {"login": login, "id": 8, "type": "User"}}
        self.path = f"journal/26/11/23/{login}.md"
        self.set_files([self.path])
        self.calls = []
        self.checks = [{"name": bot.CONTEXT, "link": self.run_url, "state": "SUCCESS"}]
        self.rules = [{"type": "required_status_checks", "parameters": {
            "strict_required_status_checks_policy": True,
            "required_status_checks": [{"context": bot.CONTEXT, "integration_id": 22}]}},
            {"type": "pull_request", "parameters": {"require_code_owner_review": True}}]
        self.after_success = lambda: None
        self.error = None

    def set_files(self, paths, modify=False):
        header = b":100644 100644 abc def M" if modify else b":000000 100644 000 def A"
        self.raw = b"".join(header + b"\0" + p.encode() + b"\0" for p in paths)
        self.pr["changed_files"] = len(paths)
        self.files = [{"filename": p, "status": "modified" if modify else "added"} for p in paths]

    def gh(self, command, *args, **kwargs):
        self.calls.append((command, *args))
        if command == "pr":
            if "--disable-auto" in args:
                self.pr["auto_merge"] = None
                return
            return copy.deepcopy(self.checks)
        endpoint = args[0].removeprefix("repos/org/repo/")
        if self.error == endpoint:
            raise RuntimeError("API denied")
        if endpoint == self.bot.pull:
            return copy.deepcopy(self.pr)
        if endpoint.endswith("files?per_page=2"):
            return self.files[:2]
        if endpoint.startswith("statuses/"):
            if "state=success" in args:
                self.after_success()
            return {}
        if endpoint.startswith("rules/branches/"):
            return [self.rules]
        if endpoint.startswith("codeowners/errors"):
            return {"errors": []}
        if endpoint.endswith("/merge"):
            self.pr.update(state="closed", merged=True)
            return {"merged": True}
        raise AssertionError(endpoint)

    def merges(self):
        return [call for call in self.calls if call[1].endswith("/merge")]


class BotTests(unittest.TestCase):
    def setUp(self):
        self.p = Platform()
        self.use("DELAY", patch.object(bot, "DELAYS", (0, 0)))
        self.use("env", patch.dict(os.environ, GITHUB_REPOSITORY="org/repo"))
        self.use("owner", patch.object(validate_pr, "historical_owner", return_value=8))
        self.use("days", patch.object(validate_pr, "entries_on_day", return_value=[]))
        self.use("changes", patch.object(bot, "changes", side_effect=lambda *_: self.p.raw))
        self.use("git", patch.object(bot, "git", side_effect=lambda *a:
                 b"* @maintainer\n/journal/\n" if a[0] == "show" else self.p.base.encode()))
        self.use("api", patch.object(bot, "gh", side_effect=self.p.gh))

    def use(self, name, patcher):
        setattr(self, name, patcher.start())
        self.addCleanup(patcher.stop)

    def assert_stopped(self):
        with self.assertRaises((ValueError, RuntimeError)):
            self.p.bot.run()
        self.assertFalse(self.p.merges())

    def test_added_idempotent_sha_bound_squash(self):
        self.p.bot.run()
        self.p.bot.run()
        merge, = self.p.merges()
        self.assertIn("sha=" + self.p.head, merge)
        self.assertIn("merge_method=squash", merge)
        self.assertEqual(self.changes.call_count, 2)

    def test_history_checked_twice(self):
        self.p.set_files(["journal/25/11/23/alice.md"], modify=True)
        self.p.bot.run()
        self.assertEqual(self.owner.call_count, 2)
        self.assertEqual(len(self.p.merges()), 1)

    def test_wrong_owner_multiple_mixed(self):
        for paths in [["journal/26/11/23/bob.md"], [self.p.path, "journal/26/11/22/alice.md"],
                      [self.p.path, "site/index.md"]]:
            with self.subTest(paths=paths):
                self.p.set_files(paths)
                self.assert_stopped()

    def test_system_files_require_human(self):
        for path in ["tools/validate_pr.py", "README.md", ".github/workflows/journal.yml"]:
            self.p.set_files([path])
            self.p.bot.run()
            self.assertFalse(self.p.merges())
            self.assertFalse(any(call[0] == "pr" for call in self.p.calls))

    def test_draft_non_main_and_conflict(self):
        self.p.pr["draft"] = True
        self.assert_stopped()
        self.p.pr.update(draft=False, mergeable=False)
        self.assert_stopped()
        self.p.pr["base"]["ref"] = "dev"
        self.assert_stopped()

    def test_head_updated_after_check(self):
        self.p.after_success = lambda: self.p.pr["head"].update(sha="b" * 40)
        self.assert_stopped()

    def test_new_illegal_revision_cancels_deferred_merge_first(self):
        self.p.pr["auto_merge"] = {"merge_method": "squash"}
        self.p.set_files([self.p.path, "tools/validate_pr.py"])
        self.assert_stopped()
        self.assertIsNone(self.p.pr["auto_merge"])
        self.assertIn("--disable-auto", self.p.calls[1])
        self.assertIn("state=failure", self.p.calls[-1])

    def test_file_api_disagrees_with_git(self):
        self.p.files[0]["status"] = "renamed"
        self.assert_stopped()

    def test_required_checks_not_affirmative(self):
        for state in ("FAILURE", "PENDING", "SKIPPED", "NEUTRAL", "CANCELLED", "UNKNOWN"):
            self.p.checks[0]["state"] = state
            self.assert_stopped()
        self.p.checks.clear()
        self.assert_stopped()

    def test_shared_head_other_pr_success(self):
        self.p.checks[0]["link"] = self.p.run_url.replace("runs/1", "runs/2")
        self.assert_stopped()

    def test_missing_required_check_or_wrong_source(self):
        checks = self.p.rules[0]["parameters"]["required_status_checks"]
        checks.append({"context": "other"})
        self.assert_stopped()
        checks[0]["integration_id"] = 23
        self.assert_stopped()

    def test_api_errors_no_merge(self):
        for endpoint in ["pulls/1", "pulls/1/files?per_page=2", "rules/branches/main?per_page=100"]:
            self.p.error = endpoint
            self.assert_stopped()

    def test_independent_validation_can_revoke_green(self):
        self.owner.side_effect = [8, 99]
        self.p.set_files(["journal/25/11/23/alice.md"], modify=True)
        self.assert_stopped()
        self.assertIn("state=failure", self.p.calls[-1])

    def test_main_advanced_during_validation(self):
        self.p.after_success = lambda: self.p.pr["base"].update(sha="c" * 40)
        self.assert_stopped()

    def test_code_without_owners_must_not_receive_success(self):
        self.p.set_files(["README.md"])
        self.git.side_effect = lambda *args: b"/journal/" if args[0] == "show" else self.p.base.encode()
        self.assert_stopped()
        self.assertIn("state=failure", self.p.calls[-1])

    def test_transient_status_recovers(self):
        original = self.p.gh
        def eventually(command, *args, **kwargs):
            if command == "pr" and not any(c[0] == "pr" for c in self.p.calls):
                self.p.calls.append(("pr", "checks"))
                raise bot.Waiting("稍后重试")
            return original(command, *args, **kwargs)
        self.api.side_effect = eventually
        self.p.bot.run()
        self.assertEqual(len(self.p.merges()), 1)

    def test_independent_prs_in_parallel(self):
        platforms = [self.p, Platform(2, "bob")]
        def run(p):
            # Keep each installation's mocked API local to its simulated runner.
            p.bot.api = lambda endpoint, *args: p.gh("api", "repos/org/repo/" + endpoint, *args)
            p.bot.run()
        self.api.side_effect = lambda command, operation, number, *args: platforms[int(number)-1].gh(
            command, operation, number, *args)
        self.changes.side_effect = lambda pr, number: platforms[number-1].raw
        with ThreadPoolExecutor(2) as pool:
            list(pool.map(run, platforms))
        self.assertEqual([len(p.merges()) for p in platforms], [1, 1])

    def test_unusable_credentials_and_transient_transport(self):
        # Exercise the CLI adapter, including failure when stdout isn't JSON.
        for stderr, error in [(b"HTTP 403", RuntimeError), (b"HTTP 503", bot.Waiting)]:
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 1, b"", stderr)), self.assertRaises(error):
                gh_adapter("api", "repos/org/repo/pulls/1")

    def test_app_merge_feeds_existing_pages_push_workflow(self):
        self.p.bot.run()
        merge, = self.p.merges()
        self.assertIn("commit_message=Validated Startogether journal.", merge)
        workflow = (ROOT/".github/workflows/journal.yml").read_text()
        self.assertIn("GH_TOKEN: ${{ steps.app.outputs.token }}", workflow)
        pages = (ROOT/".github/workflows/pages.yml").read_text()
        self.assertIn("push:\n    branches: [main]", pages)
        self.assertIn("npm run build", pages)
        self.assertIn("actions/deploy-pages@", pages)
