# 开始记录

给今天留几分钟。你可以写下一件做成的小事，或者勾选一个坚持下来的目标。

## 准备工具

注册并登录 GitHub，安装 [Git](https://git-scm.com/downloads) 和 [Python 3](https://www.python.org/downloads/)。Windows 可以用 Git Bash 或 PowerShell，macOS 和 Linux 打开终端。

## 复制仓库

在项目的 GitHub 首页点击 **Fork → Create fork**，你会得到一份属于自己的副本。在副本点击 **Code → HTTPS** 复制地址。将下例中的地址替换为你的地址，再依次运行：

```sh
git clone https://github.com/alice/startogether.git startogether
cd startogether
git config user.name "你的公开昵称"
git config user.email "你的 GitHub 提交邮箱"
git switch -c diary-first
```

Clone 将仓库下载到电脑。可以在 GitHub 的 Settings → Emails 中找到自己的 noreply 邮箱。

## 选择今天的记录方式

将 `alice` 换成自己的 GitHub 用户名。Windows 可将 `python3` 换为 `py -3`。

### 私密日记，只公开打卡

```sh
python3 tools/new_entry.py alice --private
```

终端会给出两个路径。打开第一个，在电脑主目录的 `.startogether-private` 文件夹里写日记。第二个是 `journal/` 下的空文件，保持空白，按[提交与合并](./submit)的步骤只提交它。合并并更新网站后，大家能看到你的用户名和打卡日期，热力图会亮起，正文只有你自己保管。

以后想分享这一天，可以把愿意公开的段落写进原来的空文件，再提交一次。同一天仍只算一次打卡。

### 公开分享日记

```sh
python3 tools/new_entry.py alice --public
```

打开终端显示的 Markdown 文件，写下今天的收获。任务可以这样写：

```md
- [x] 午休时出门散步
- [ ] 睡前读几页书
```

文件按北京时间归档。重复运行会保留原文。保存后，继续[提交与合并](./submit)。
