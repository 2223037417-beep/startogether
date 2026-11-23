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


def entry_path(login, root, now, folder):
    login = username(login)
    if os.name == "nt" and re.fullmatch(r"con|prn|aux|nul|(?:com|lpt)[1-9]", login):
        raise ValueError("此用户名是 Windows 设备名，请在 WSL 的 Linux 目录中创建或在 GitHub 网页编辑。")
    day = (now or datetime.now(BEIJING)).astimezone(BEIJING).date()
    directory = root
    for part in (folder, *day.strftime("%y/%m/%d").split("/")):
        directory = directory / part
        if directory.resolve() != directory:
            raise ValueError("日记目录包含链接，请检查本地仓库。")
        directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / (login + ".md")
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("目标路径必须是普通文件。")
    return path, day


def write_template(path, day):
    template = (ROOT / "templates/entry.md").read_text(encoding="utf-8")
    content = template.replace("{date}", day.isoformat()).replace("{username}", path.stem)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as entry:
            entry.write(content)
    except FileExistsError:
        return path, False
    return path, True


def create_entry(login, root=ROOT, now=None):
    path, day = entry_path(login, root, now, "journal")
    return write_template(path, day)


def create_private_entry(login, root=ROOT, now=None):
    now = now or datetime.now(BEIJING)
    marker, _ = entry_path(login, root, now, "journal")
    note_root = Path.home().resolve()
    local_folder = note_root / ".startogether-private"
    if local_folder == root or root in local_folder.parents:
        raise ValueError("私密目录必须位于项目仓库之外。")
    if marker.exists() and marker.stat().st_size:
        raise ValueError("当天的投稿文件已有正文。请先核对它的内容和提交历史，再选择只打卡。")
    note, day = entry_path(login, note_root, now, local_folder.name)
    write_template(note, day)
    try:
        marker.touch(exist_ok=False)
    except FileExistsError:
        if marker.stat().st_size:
            raise ValueError("当天的投稿文件已有正文，无法作为空白打卡文件。")
    return note, marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", help="GitHub 个人用户名")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--private", action="store_true", help="正文保存在本地，仅提交空白打卡文件")
    mode.add_argument("--public", action="store_true", help="在仓库内撰写可公开的日记（默认）")
    args = parser.parse_args()
    try:
        if args.private:
            note, marker = create_private_entry(args.username)
            print("只在这里写私密正文：", note)
            print("只提交这个空文件：", marker.relative_to(ROOT))
            return
        path, created = create_entry(args.username)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"无法生成日记：{exc}\n")
    print("公开分享模式。提交后正文将公开。")
    print("已创建：" if created else "日记已经存在，保留原文：", path)


if __name__ == "__main__":
    main()
