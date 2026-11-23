# Startogether 维护指南

## 发布与权限

1. 获所有者授权后，在 GitHub 建立空的 Public 仓库，上传本项目的初始提交到 `main`，将其设为默认分支。先完成下面的保护和验收，再开放投稿。本地可运行 `python3 -m unittest discover -s tests -v` 复查。
2. **Settings → General → Pull Requests** 只启用 **Allow squash merging**。每篇日记的创建 PR 及其合并 SHA 用于日后核对作者。保持线性历史，关闭自动合并和合并队列。
3. 只给维护者写权限。**Settings → Actions → General** 启用 Actions，默认令牌选只读，关闭 Actions 创建或批准 PR 的权限。**Fork pull request workflows from outside collaborators** 选择 **Require approval for all outside collaborators**。维护者不要批准 Fork 提供的工作流运行。内置的 `pull_request_target` 从受信任的默认分支触发，日记投稿无需批准任何由 Fork 定义的任务。组织仓库还需注意，组织成员可能不受外部贡献者审批策略约束。[GitHub 的 Fork 工作流审批说明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)
4. 在开放投稿前，用外部账号从 Fork 提交一篇自己的日记，让检查成功运行一次，先保留 PR。这样状态会出现在最近运行过的检查候选列表中。

## 强制合并条件

在仓库 **Settings → Rules → Rulesets → New ruleset → New branch ruleset** 创建保护规则。Enforcement 选 **Active**，目标分支选 **Include default branch**（确认默认分支为 main），日常 bypass 列表留空。

- 开启 **Require a pull request before merging**，要求至少一位有写权限的维护者批准，勾选新提交后撤销旧批准。
- 开启 **Require status checks to pass**，添加精确名称 `Startogether / journal ownership`，预期来源选 **GitHub Actions**。开启 **Require branches to be up to date before merging**。这个名称是工作流明确写到 PR head SHA 的 commit status；在状态的 Details 可打开生成它的运行。若候选为空，请先检查试投 PR 的发布状态作业日志。
- 开启 **Block force pushes**、**Restrict deletions**、**Require linear history**，保存。使用经典 Branch Protection 的仓库可在 **Settings → Branches** 为 `main` 配置相同的必需 PR、审批、严格状态检查和线性历史，并启用 **Do not allow bypassing the above settings**，保持禁止强推和删除。
- 支持组织级必需工作流的部署，在 **Organization Settings → Repository → Rulesets** 为本仓库的 main 加上 **Require workflows to pass before merging**。来源选本仓库受保护的 main 和 `.github/workflows/journal.yml`。此规则绑定可信工作流本身；普通状态名称及 GitHub Actions 来源只能辨认报告应用。若普通参与者是组织成员，应采用这条来源绑定规则，并确保组织成员提交的 Fork 工作流不会被当作可信任务执行。[组织工作流规则](https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-workflows-to-pass-before-merging)
- 每次批准前点必需状态的 **Details**，确认这一运行属于**当前 PR 编号和最新 head**，且 ownership 作业实际成功。GitHub 的普通状态附在提交 SHA 上，另一份 PR 可以指向同一 SHA；尤其在个人仓库，维护者审批是核对这层对应关系的必要环节。只由维护者点击 **Squash and merge**。[必需状态检查与提交 SHA](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

## 上线验收

从两个外部账号各发一篇自己的日记。检查 Details 与 PR 对应，批准并 squash 合并第一篇；第二个分支更新到最新 main 后也应通过。用第一个账号新开 PR 编辑已经合并的日记，确认能解析到创建者。在另一份测试 PR 中改动别人的日记、再追加系统文件，分别确认新 head 上结果为失败且合并被锁定。改回合法的一份文件后应重新通过。另用无写权限账号验证不能直推 main，核对规则没有管理员日常绕过项。遇到 Expected、Pending、权限错误或来源不明的绿灯，保留阻塞并核对状态名称、来源、事件及最新提交。

## 校验依据

工作流只从公开上游读取 Git 对象，从已验证属于 main 的固定 base SHA 提取两个 Python 文件。PR head 只作为 Git 数据读取，并与事件 SHA 核对；不会检出 Fork 的工作树、安装其依赖或执行其文件。以固定 base/head 的完整 NUL 分隔 raw diff 核对全部文件与 Git 模式，避免实时文件列表分页、截断和更新竞态。关闭重命名检测使移动表现为删除与新增，两项都会导致拒绝。严格更新规则保证 main 前进后要重新检查。[GitHub 的 pull_request_target 安全说明](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)

身份取 GitHub 事件的 PR 作者，日期取 PR 首次创建时间换算成 UTC+8（当前北京时间）。路径采用 2000–2099 年、小写用户名和真实日历日期。更新时，用受保护历史找到创建提交，再通过 GitHub API 找到同一仓库 main 上与之精确对应的已合并 PR，比较账户数字 ID。新增时也核对当日已有条目的创建者，避免同一账户改名后重复投稿。查询失败、限流和归属歧义均阻止合并；网络恢复后可重新运行。验证作业仅用 `pull-requests: read`，独立的报告作业仅用 `statuses: write`；两者均无仓库内容写权限。[提交关联 PR 的 API](https://docs.github.com/en/rest/commits/commits#list-pull-requests-associated-with-a-commit)

## 改名与系统维护

账户改名后旧文件保留历史。若需迁移，让**原作者用新用户名亲自发起迁移 PR**。维护者对照各文件原创建 PR 的数字 ID 和迁移 PR 的作者 ID，核实目标路径空闲、日期及正文未变。只有仓库所有者授权的维护例外才能让该 PR 通过；使用 squash 合并，确保新路径的创建提交仍归属于原作者发起的 PR。找不到原始记录或无法核实身份时保留原文。

脚本、模板和规则变更同样走专门的维护 PR。所有者可将日记检查放入独立规则集，仅在获授权的维护窗口为指定维护者配置 **For pull requests only** 的临时 bypass；审批、禁止直接推送和禁止强推保留在无 bypass 的规则集中。审核完整差异，合并后立即移除临时权限，并重跑上线验收。经典保护需由管理员调整对应的日记检查并记录恢复过程。维护窗口暂停其他合并。

## GitHub Pages 阅读站

在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**，并将 `github-pages` 环境的部署来源限定为 main。提交合并到 main 后，`Publish growth journal` 构建并部署静态站，也可在 Actions 页选择 main 手动运行。访问地址以 deploy 作业的 environment 链接为准。仓库 URL 取自 GitHub 工作流上下文，资源前缀取自 Pages 配置，支持仓库子路径、自定义域和根路径。

本地使用最新的 Node.js 22 LTS。项目锁定 VitePress 2.0.0-alpha.21 和对应依赖，升级后请重新检查默认主题及静态构建。依次运行：

```sh
npm ci
npm run build
npm run preview
```

打开终端给出的地址并进入仓库子路径（无远程时默认 `/startogether/`）。开发时可用 `npm run dev`。更改日记后重新构建或重启开发服务。`SITE_BASE` 可指定带首尾斜杠的路径；有 GitHub origin 或设置 `GITHUB_REPOSITORY=所有者/仓库名` 时生成指向该仓库的链接。

构建只扫描 `journal/YY/MM/DD/用户名.md`。每篇正文单独使用禁用原始 HTML 的 Markdown 渲染器处理，Vue 模板、脚本及 frontmatter 均作为参与者内容处理。站点没有日记写入接口。主分支保护与日记所有权检查仍需按上文配置。
