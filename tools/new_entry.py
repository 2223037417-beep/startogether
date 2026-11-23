"""Create one Markdown entry for the current Beijing day."""
import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEIJING = timezone(timedelta(hours=8), "Asia/Shanghai")
LOGIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII | re.IGNORECASE)


def username(value):
    if len(value) > 39 or not LOGIN.fullmatch(value):
        raise ValueError("请输入 GitHub 个人用户名（1–39 个英文字母、数字或单连字符）。")
    return value.lower()


def create_entry(login, root=ROOT, now=None):
    login = username(login)
    if os.name == "nt" and re.fullmatch(r"con|prn|aux|nul|(?:com|lpt)[1-9]", login):
        raise ValueError("此用户名是 Windows 设备名，请在 WSL 的 Linux 目录中创建或在 GitHub 网页编辑。")
    day = (now or datetime.now(BEIJING)).astimezone(BEIJING).date()
    directory = root
    for part in ("journal", *day.strftime("%y/%m/%d").split("/")):
        directory = directory / part
        if directory.resolve() != directory:
            raise ValueError("日记目录包含链接，请检查本地仓库。")
        directory.mkdir(exist_ok=True)
    path = directory / (login + ".md")
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("目标路径必须是普通文件。")
    template = (ROOT / "templates/entry.md").read_text(encoding="utf-8")
    content = template.replace("{date}", day.isoformat()).replace("{username}", login)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as entry:
            entry.write(content)
    except FileExistsError:
        return path, False
    return path, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", help="GitHub 个人用户名")
    args = parser.parse_args()
    try:
        path, created = create_entry(args.username)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"无法生成日记：{exc}\n")
    print("已创建：" if created else "日记已经存在，保留原文：", path)


if __name__ == "__main__":
    main()
