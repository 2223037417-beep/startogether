# Startogether

## 写给每一个来记录的你

<!-- #region letter -->

你好呀，

你看过《小狗钱钱》吗？那是我的财商启蒙书。书中“成功日记”的概念吸引了我，也让我很快明白了信念的重要性。

**注意力是即时性的，坚持是阶段性的，而信念是持久性的。**

这就是我做 Startogether 的初衷。我希望你能在这里养成写日记的习惯，把自己的目标写下来，再回头看看自己坚持了多久。日复一日，那些记下来的小成功，也会让你更相信自己。

如果你还没用过 GitHub，也可以从第一篇日记开始。写下它，你会学着编辑 Markdown 文件；把它提交到这里，你也就慢慢熟悉了 GitHub 和 Git 的基本操作。

进步永无止境，永远相信自己可以做到。微不足道的一颗种子，也可以长成参天大树！

—— Samoye

<!-- #endregion letter -->

## 写下第一篇

每人每天有一份 Markdown 日记，可以写收获、勾选目标，也可以留一句明天想尝试的事。

**提交前请确认愿意公开。** 任何人都能阅读、克隆仓库。不要写密码、密钥、住址、联系方式或他人的隐私。Git 历史、Fork 和本地副本可能长期保留，后来删除文件也无法保证所有副本消失。

1. 注册并登录 GitHub，安装 [Git](https://git-scm.com/downloads) 和 [Python 3](https://www.python.org/downloads/)（3.8 或以上）。Windows 安装 Python 时可勾选加入 PATH，随后打开 Git Bash 或 PowerShell；macOS、Linux 打开终端。以下示例用 `python3`，Windows 可换成 `py -3`，若 `python --version` 显示 3.8 或以上也可用 `python`。
2. 在项目首页点 **Fork → Create fork**。Fork 会在你的 GitHub 账户下建立项目副本。在自己的副本点 **Code → HTTPS**，复制地址。Clone 会把这个副本下载到电脑。把下面示例地址换成刚复制的地址，小写文件名示例中的 `alice` 也要换成你自己的账号。

   ```sh
   git clone https://github.com/alice/startogether.git startogether
   cd startogether
   git config user.name "你的公开昵称"
   git config user.email "你的 GitHub 提交邮箱"
   git switch -c diary-first
   ```

   邮箱可从 GitHub **Settings → Emails** 复制自己的 noreply 地址。分支让这一篇日记可以单独提交。
3. 在仓库目录运行：

   ```sh
   python3 tools/new_entry.py alice
   ```

   用文本编辑器打开终端输出的文件。路径按北京时间生成，例如 `journal/26/11/23/alice.md`。写几句话，用 `- [ ] 散步` 表示待办，完成后改成 `- [x] 散步`。可以增删标题、贴链接、引用公开图片。保存为 UTF-8。再次运行会保留原文。
4. Commit 是把本次修改保存为一条本地记录，Push 是把记录上传到自己的 Fork。将示例路径替换成你的文件路径。

   ```sh
   git add -- journal/26/11/23/alice.md
   git status
   git commit -m "记录今天的小成功"
   git push -u origin diary-first
   ```

   检查 `git status` 的待提交区域，应只有自己的一个文件。首次推送按凭据管理器提示登录 GitHub；HTTPS 身份验证也可使用有权写入自己 Fork 的个人访问令牌。
5. 打开自己的 Fork，点 **Compare & pull request**（或 **Contribute → Open pull request**）。Pull Request，简称 PR，是请原项目合并这次修改的请求。确认目标是**原仓库的 main**，来源是自己的 `diary-first`，在 **Files changed** 核对文件后提交。仓库启用日记机器人后，合法日记通过必需检查即可自动合并。草稿请先点 **Ready for review**；同一分支后续 Commit 和 Push 会更新这一个 PR。

## 明天再写，或修改旧日记

在 GitHub 的 Fork 首页选择 **Sync fork → Update branch**，然后在本地执行：

```sh
git switch main
git pull --ff-only origin main
git switch -c diary-1124
```

每篇换一个未用过的分支名，再重复生成、编辑、提交步骤。修改历史日记时直接打开原文件。若待合并分支落后，在 GitHub 的 PR 页点 **Update branch**；也可先同步 Fork，再在当前日记分支运行 `git fetch origin`、`git merge origin/main`、`git push`。

## 阅读与常见问题

- **去哪儿看大家的记录？** 在仓库首页按 `journal → 年 → 月 → 日` 浏览，点文件即可阅读。文件页的 **History** 能看到历次修改。首次有人提交日记后目录才会出现。
- **可以补昨天的记录吗？** 新文件的目录日期取 PR 首次打开时的北京时间；已经打开的 PR 可以隔天合并。若在午夜前写完、午夜后才开 PR，请保留旧分支正文，从同步后的 main 新建分支，重新运行脚本，将正文复制到今天的文件，并在今天新开 PR，随后关闭过期 PR。
- **为何校验失败？** 点状态检查的 **Details** 看原因。一次只能新增或编辑本人一份日记，文件名统一小写。删除、移动、可执行文件和其他路径都会被拒绝。GitHub 账号改名后，请联系维护者处理旧文件。
- **谁可以使用这些内容？** 代码、文档和公共模板使用 [MIT 许可](LICENSE)。`journal/` 中每篇日记的版权归相应作者，作者可另行授权。公开可读不代表可以任意转载或商用。

维护者请参阅 [部署、合并规则与验收步骤](SETUP.md)。

## 在网站上阅读

维护者启用 GitHub Pages 后，可从仓库的 **Deployments → github-pages** 打开阅读站。成长日历按北京时间展示已合并的日记，点击有记录的日期即可阅读；输入 GitHub 用户名可查看个人记录。写作和投稿仍使用上面的 Markdown 与 PR 流程。
