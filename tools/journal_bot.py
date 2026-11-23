"""Run only from trusted main, in a public clone with no PR working tree."""
import json
import os
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError

from validate_pr import changes, git, validate_journal

CONTEXT = "Startogether / PR policy"
DELAYS = (0, 2, 4, 8, 15, 30, 30)


class Waiting(RuntimeError):
    """GitHub has not finished computing or enforcing the merge conditions."""


def gh(*args, expect_json=True):
    # gh reads its installation token from GH_TOKEN. Never log API response bodies
    # containing contributor-controlled text as Actions workflow commands.
    result = subprocess.run(["gh", *args], capture_output=True, timeout=45)
    if result.returncode:
        if result.returncode == 8 or any(
            marker in result.stderr for marker in (b"HTTP 429", b"HTTP 502", b"HTTP 503", b"HTTP 504", b"no required checks reported")
        ):
            raise Waiting("GitHub 状态尚未就绪或暂时不可用。")
        if b"HTTP 405" in result.stderr or b"HTTP 409" in result.stderr:
            raise ValueError("GitHub 拒绝合并；请检查最新 head、分支同步和保护规则。")
        raise RuntimeError("GitHub API 调用未成功，请核对 App 权限、分支规则和服务状态。")
    return json.loads(result.stdout) if expect_json and result.stdout.strip() else None


def retry(read):
    for delay in DELAYS:
        if delay:
            time.sleep(delay)
        try:
            return read()
        except Waiting as exc:
            reason = str(exc)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            reason = "GitHub 历史归属查询暂时不可用。"
        except (URLError, TimeoutError, subprocess.TimeoutExpired):
            reason = "读取 GitHub 数据超时或连接中断。"
    raise ValueError(reason + " 本次没有合并；状态恢复后可重跑。")


def classify(pr, raw, api_files):
    # --no-renames produces NUL-delimited (header, path) pairs. This also
    # catches moves out of journal even when the files API collapses a rename.
    fields = raw.split(b"\0")
    if len(fields) < 3 or len(fields) % 2 != 1 or fields[-1]:
        raise ValueError("变更列表为空或不完整。")
    paths = fields[1::2]
    if not api_files or len(api_files) != min(2, pr["changed_files"]):
        raise Waiting("PR 文件列表尚未与文件数一致。")
    if any(f["filename"].encode() not in paths for f in api_files):
        raise Waiting("文件 API 与 Git 的快照尚未一致。")
    if not any(p == b"journal" or p.startswith(b"journal/") for p in paths):
        return "manual"
    if pr["user"].get("type") != "User" or not isinstance(pr["user"].get("id"), int):
        raise ValueError("无法确认个人账户身份。")
    validate_journal(pr, raw)
    if pr["changed_files"] != 1 or len(api_files) != 1:
        raise ValueError("API 与 Git 文件数不一致，请等待最新检查。")
    item = api_files[0]
    status = fields[0].split()[-1]
    if (item["filename"].encode() != paths[0] or "previous_filename" in item
            or item["status"] != {b"A": "added", b"M": "modified"}[status]):
        raise ValueError("API 与固定提交的文件路径或操作不一致。")
    return "journal"


class Bot:
    def __init__(self, repo, number, head, app_id, run_url):
        self.repo = repo
        self.number = number
        self.head = head
        self.app_id = app_id
        self.run_url = run_url
        self.pull = f"pulls/{number}"

    def api(self, endpoint, *args):
        return gh("api", f"repos/{self.repo}/{endpoint}", *args)

    def status(self, state, message):
        self.api(f"statuses/{self.head}", "-X", "POST", "-f", f"context={CONTEXT}",
                 "-f", f"state={state}", "-f", f"description={message[:140]}",
                 "-f", f"target_url={self.run_url}")

    def snapshot(self):
        pr = self.api(self.pull)
        if (pr["number"] != self.number or pr["base"]["repo"]["full_name"] != self.repo
                or pr["head"]["sha"] != self.head):
            raise ValueError("PR 已更新或仓库不符，请查看新提交的检查。")
        return pr

    def inspect(self, pr):
        if pr["state"] != "open" or pr["draft"] is not False or pr["base"]["ref"] != "main":
            raise ValueError("自动合并仅处理目标为 main 的开放、非草稿 PR。")
        if pr["base"]["sha"] != git("rev-parse", "origin/main").decode().strip():
            raise ValueError("main 已更新，请同步日记分支并重新检查。")
        # Only a one-file PR can be automated. Two API records suffice to reject it.
        files = self.api(self.pull + "/files?per_page=2")
        return classify(pr, changes(pr, self.number), files)

    def protection(self):
        pages = self.api("rules/branches/main?per_page=100", "--paginate", "--slurp")
        rules = [rule for page in pages for rule in page]
        required = [r["parameters"] for r in rules if r["type"] == "required_status_checks"]
        if not any(p["strict_required_status_checks_policy"] is True and any(
            c["context"] == CONTEXT and c.get("integration_id") == self.app_id
            for c in p["required_status_checks"]) for p in required):
            raise ValueError("main 缺少绑定此 App 的严格必需检查，请按 SETUP 配置。")
        if not any(r["type"] == "pull_request" and r["parameters"]["require_code_owner_review"]
                   for r in rules):
            raise ValueError("main 缺少强制 Code Owner 审核规则。")

        return {c["context"] for p in required for c in p["required_status_checks"]}

    def code_owners(self):
        # A missing owner line is silently ignored by GitHub. Verify the
        # deployment's catch-all and its sole exception before passing code.
        lines = [s.split("#", 1)[0].split() for s in
                 git("show", "origin/main:.github/CODEOWNERS").decode().splitlines()]
        lines = [line for line in lines if line]
        if (len(lines) != 2 or len(lines[0]) < 2 or lines[0][0] != "*"
                or lines[1] != ["/journal/"] or self.api("codeowners/errors?ref=main")["errors"] != []):
            raise ValueError("请在 main 配置有效的 CODEOWNERS 和日记例外。")

    def ready(self, required):
        pr = self.snapshot()
        if pr["merged"] is True:
            return None
        if pr["state"] != "open" or pr["draft"] is not False or pr["base"]["ref"] != "main":
            raise ValueError("PR 状态或目标分支已改变。")
        if pr["base"]["sha"] != git("rev-parse", "origin/main").decode().strip():
            raise ValueError("main 已更新，请同步分支。")
        if pr["auto_merge"] is not None:
            raise ValueError("PR 已被另外安排自动合并，请重新运行检查。")
        if pr["mergeable"] is False or pr["mergeable_state"] in ("dirty", "behind"):
            raise ValueError("请同步最新 main 或人工解决冲突。")
        if pr["mergeable"] is not True or pr["mergeable_state"] not in ("clean", "unstable"):
            raise Waiting("GitHub 正在计算状态，或合并仍受规则限制。")
        checks = gh("pr", "checks", str(self.number), "--repo", self.repo, "--required",
                    "--json", "name,state,link")
        if not any(c["name"] == CONTEXT and c["link"] == self.run_url for c in checks):
            raise Waiting("正在等待本次 PR 校验结果传播。")
        if not required.issubset({c["name"] for c in checks}):
            raise Waiting("部分必需检查尚未报告。")
        if any(c["state"].upper() != "SUCCESS" for c in checks):
            raise Waiting("最新提交的必需检查尚未全部成功。")
        return pr

    def run(self):
        pr = retry(self.snapshot)
        if pr["state"] == "closed":
            print("PR 已关闭，本次无需操作。")
            return
        if pr["auto_merge"] is not None:
            # Cancel before publishing green, including on draft/retarget events.
            gh("pr", "merge", str(self.number), "--repo", self.repo, "--disable-auto", expect_json=False)
        self.status("pending", "正在核对当前 PR 和 Git 文件")
        try:
            kind = retry(lambda: self.inspect(self.snapshot()))
            retry(self.code_owners)
            if kind == "manual":
                retry(self.protection)
        except Exception as exc:
            message = str(exc) if isinstance(exc, ValueError) else "日记策略未通过，详见本次检查"
            self.status("failure", message)
            raise
        if kind == "manual":
            self.status("success", "项目代码变更，请 Code Owner 人工审核和合并")
            print("纯项目变更；交给维护者审核。")
            return
        self.status("success", "日记归属与日期通过")
        required = retry(self.protection)
        latest = retry(lambda: self.ready(required))
        if latest is None:
            return
        # Independent live decision after the status was published.
        try:
            if retry(lambda: self.inspect(self.snapshot())) != "journal":
                raise ValueError("当前 PR 已不符合日记自动合并条件。")
        except Exception:
            self.status("failure", "合并前复验未通过，请查看最新检查")
            raise
        latest = retry(lambda: self.ready(required))
        if latest is None:
            return
        result = self.api(self.pull + "/merge", "-X", "PUT", "-f", "merge_method=squash",
                          "-f", f"sha={self.head}", "-f",
                          f"commit_title=Journal entry (#{self.number})", "-f",
                          "commit_message=Validated Startogether journal.")
        if result.get("merged") is not True:
            raise ValueError("GitHub 未确认合并，请检查分支限制并重跑。")
        print("日记已 squash 合并；请查看该提交的 Pages 部署。")


if __name__ == "__main__":
    try:
        Bot(os.environ["GITHUB_REPOSITORY"], int(os.environ["PR_NUMBER"]),
            os.environ["HEAD_SHA"], int(os.environ["APP_ID"]), os.environ["RUN_URL"]).run()
    except (KeyError, ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        sys.exit(f"日记机器人停止：{exc}")
