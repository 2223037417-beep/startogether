"""Validate immutable Git trees without checking out the contributor's branch."""
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from new_entry import BEIJING, username


def git(*args):
    return subprocess.check_output(["git", *args])


def historical_owner(base, path, repo):
    # main uses squash merges. Locate the PR which introduced this exact path.
    sha = git("log", "-1", "--format=%H", "--diff-filter=A", "--no-renames",
              base, "--", path).decode().strip()
    if not re.fullmatch("[0-9a-f]{40}", sha):
        raise ValueError("找不到文件的创建记录，请联系维护者核对。")
    request = Request(f"https://api.github.com/repos/{repo}/commits/{sha}/pulls",
                      headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                               "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=20) as response:
        pulls = json.load(response)
        if response.headers.get("Link"):
            raise ValueError("创建记录存在歧义，请联系维护者。")
    owners = [p["user"]["id"] for p in pulls if p["merged_at"]
              and p["base"]["repo"]["full_name"] == repo and p["base"]["ref"] == "main"
              and p["merge_commit_sha"] == sha]
    if len(owners) != 1:
        raise ValueError("无法唯一确认创建者，请维护者核对原 PR。")
    return owners[0]


def entries_on_day(base, directory):
    paths = git("ls-tree", "-r", "-z", "--name-only", base, "--", directory + "/")
    return [name.decode("utf-8") for name in paths.split(b"\0") if name]


def validate(pr, raw, owner_lookup, list_day):
    login = username(pr["user"]["login"])
    if pr["base"]["ref"] != "main":
        raise ValueError("请将 PR 目标分支设为 main。")
    fields = raw.split(b"\0")
    if len(fields) != 3 or fields[-1]:
        raise ValueError("每个 PR 只能提交一份日记；移动、删除或混合提交均无法合并。")
    header, filename, _ = fields
    old, new, _, _, status = header.split()
    if (old, new, status) not in ((b":000000", b"100644", b"A"),
                                  (b":100644", b"100644", b"M")):
        raise ValueError("只允许新建或编辑普通 Markdown 文件，请检查删除、链接或权限变更。")
    path = filename.decode("utf-8")
    match = re.fullmatch(r"journal/([0-9]{2})/([0-9]{2})/([0-9]{2})/" + login + r"\.md", path)
    if not match:
        raise ValueError(f"只可提交 journal/YY/MM/DD/{login}.md，用户名须小写。")
    yy, mm, dd = map(int, match.groups())
    try:
        day = date(2000 + yy, mm, dd)
    except ValueError:
        raise ValueError("路径中的日期无效。") from None
    if status == b"A":
        opened = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        expected = opened.astimezone(BEIJING).date()
        if day != expected:
            raise ValueError(f"此 PR 首次创建时的北京日期为 {expected}。若已跨午夜，请按 README "
                             "在新分支重新生成今天的文件、复制正文并于当天新开 PR。")
        for existing in list_day(path.rsplit("/", 1)[0]):
            if owner_lookup(existing) == pr["user"]["id"]:
                raise ValueError("此账户当天已有日记；如已更改用户名，请联系维护者迁移。")
    elif owner_lookup(path) != pr["user"]["id"]:
        raise ValueError("当前账户 ID 与文件创建者不符；如已改名，请联系维护者。")


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pr = event["pull_request"]
    base, head = pr["base"]["sha"], pr["head"]["sha"]
    if not all(re.fullmatch("[0-9a-f]{40}", s) for s in (base, head)):
        raise ValueError("无效的提交标识。")
    number = int(event["number"])
    git("fetch", "--no-tags", "--filter=blob:none", "origin", f"refs/pull/{number}/head")
    if git("rev-parse", "FETCH_HEAD").decode().strip() != head:
        raise ValueError("PR 已更新，请查看最新一次检查。")
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, head]).returncode:
        raise ValueError("请先同步上游 main 至当前分支，再重新检查。")
    raw = git("diff", "--raw", "-z", "--no-renames", "--no-ext-diff", "--ignore-submodules=none", base, head, "--")
    validate(pr, raw, lambda p: historical_owner(base, p, os.environ["GITHUB_REPOSITORY"]),
             lambda directory: entries_on_day(base, directory))
    print("通过：本次提交符合日记归属和日期规则。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"日记校验失败：{exc}")
