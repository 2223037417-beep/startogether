# Startogether v2.1 维护指南

## 所有者首次发布

1. 在自己的 GitHub 账户或组织名下创建空的 Public 仓库。将默认分支设为 `main`。只向维护者授予写权限。
2. 将 [.github/CODEOWNERS.example](.github/CODEOWNERS.example) 复制为 `.github/CODEOWNERS`，把占位符替换为实际有写权限的维护者或可见团队。第一行规则 `* @维护者` 负责所有项目文件（含工作流与 CODEOWNERS 本身）；下一行 `/journal/` 留空，明确豁免日记目录。可以在第一行指定多位维护者。机器人会核对这两条规则以及 GitHub 报告的文件错误。把实际配置随项目提交到 main。没有远程时，由所有者执行 `git remote add origin 仓库地址` 和 `git push -u origin main`。
3. **Settings → General → Pull Requests** 勾选 **Allow squash merging** 和 **Allow auto-merge**，关闭 merge commit、rebase、自动修复和 Merge Queue。机器人在所有条件已经满足时执行一次原生 Squash 合并。GitHub 的排队 Auto-merge 适用于尚有条件未满足的 PR；本项目会取消受管 PR 上已有的排队请求，以免对后续版本留下合并授权。[GitHub Auto-merge 的条件](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request) · [带 head SHA 的合并 API](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request)
4. 在 **Settings → Actions → General** 启用 Actions，默认工作流权限选只读，关闭 Actions 创建或批准 PR。Fork 工作流选择 **Require approval for all outside collaborators**。日记机器人由可信 `pull_request_target` 自动运行。不要批准 Fork 提供的陌生工作流。组织应限制能修改上游分支和工作流的成员。

## 安装专用 GitHub App

由所有者在账户或组织的 **Settings → Developer settings → GitHub Apps → New GitHub App** 创建私有 App。主页可用仓库地址，取消 Active webhook，安装范围选 Only on this account。不需要回调地址、事件订阅或独立服务。

| Repository permissions | 用途 |
| --- | --- |
| Metadata · Read | 读取仓库及对 main 生效的规则 |
| Pull requests · Read and write | 读取 PR、变更列表与历史归属，撤销已有的 Auto-merge |
| Commit statuses · Read and write | 写入绑定到本次提交的策略结果 |
| Checks · Read | 读取最新提交的必需检查 |
| Contents · Read and write | GitHub 原生 Squash 合并 |

在 **Install App → Only select repositories** 只选择本仓库。记录数字 **App ID**，生成并保管 PEM 私钥。在仓库 **Settings → Environments** 创建 `journal-bot`，仅允许分支 `main`，无需环境审批。在该环境添加变量 `JOURNAL_APP_ID` 和 secret `JOURNAL_APP_PRIVATE_KEY`（完整多行 PEM）。给 App 的 bypass 列表留空，不给 Administration、Workflows 或 Pages 写权限。私钥轮换时，先更新环境 secret、完成一次验收，再撤销旧密钥。

工作流的默认 `GITHUB_TOKEN` 权限为空。固定版本的官方 Action 为本仓库签发短期 installation token，任务结束时撤销。由 App 发起合并，现有 Pages 工作流可接收 main 的 push。默认 `GITHUB_TOKEN` 触发的 push 通常不会再创建这个工作流运行。[安装令牌 Action](https://github.com/actions/create-github-app-token) · [GitHub 工作流触发规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)

## main 的强制规则

在 **Settings → Rules → Rulesets → New branch ruleset** 创建 Active 规则，目标仅为 main，不设 bypass。此实现通过 GitHub 的分支有效规则 API 检查 Rulesets；仅配置经典 Branch Protection 时，机器人会停在合并前。

- 开启 **Require a pull request before merging**，全局 **Required approvals = 0**，开启 **Require review from Code Owners** 和 **Dismiss stale pull request approvals when new commits are pushed**。关闭普遍要求他人批准最近一次推送的选项。代码文件由 catch-all Code Owner 审核；日记目录的例外由必需的归属检查覆盖。机器人不会提交 APPROVE review。[GitHub 对 CODEOWNERS 顺序、空所有者和强制审核的说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- 开启 **Require status checks to pass**，添加精确名称 `Startogether / PR policy`，预期来源选择**刚安装的专用 App**，启用 **Require branches to be up to date before merging**。同时开启 **Block force pushes**、**Restrict deletions** 和 **Require linear history**。机器人的执行作业要等待必需检查完成，因此不要把整个合并作业设为必需检查。
- 首次配置时，用外部账号打开一篇合法日记 PR 以登记状态名称。它可以先发布日记策略绿灯，但在读不到上述严格规则时会停止。设置来源、保存规则后，重新运行该 PR 的全部作业。核对规则和 Code Owner 生效后再开放投稿。
- 从 v2.0 升级时，先保留旧保护并暂停其他合并，完成新 App、CODEOWNERS 和新必需状态的配置，再移除旧的 `Startogether / journal ownership` 和全局 1 人审批。检查叠加的经典保护、组织规则和旧版 required workflow，避免继续等待已退休的检查。保留其他有意配置的安全检查。

**限制 App 修改其他基分支。** GitHub 的合并接口能原子校验 head SHA，接口参数没有 expected base branch。在上游另建分支规则集：目标为所有分支并排除 main，开启 **Restrict updates**。如需在这些分支上开发，仅将可信维护者或必要的内部写入身份加入该规则集允许列表，排除日记 App。这样即便在最后一次读取 PR 和 GitHub 执行合并之间改了目标，平台也会拒绝 App 更新其他基分支。参与者的 Fork 分支不受上游仓库分支规则影响。

## 机器人如何判定

每次开 PR、更新提交、重新打开、修改目标、切换草稿状态或启用排队合并时，机器人读取 GitHub API 的 PR 编号、作者、状态、base 和 head。工作目录只加载公开上游 main 上的三个脚本；Fork 引用仅作为 Git 对象获取。校验对照固定 Git 树和 API 文件列表，沿用北京时间、真实日期、单文件、普通文件模式以及历史创建者数字 ID 等规则。禁用重命名检测后，跨目录移动会在 Git 差异中保留源路径。

纯项目 PR 在分支审核规则与 CODEOWNERS 有效时得到“需人工审核”的策略结果，机器人随即退出。日记与代码混合提交、触碰他人文件或不符合日记规则都会失败。需要系统维护时，单独开纯代码 PR，由 Code Owner 批准后人工 Squash 合并。

日记绿灯发布后，机器人核对 main 生效的严格规则、当前 PR 的全部必需检查和指向本次运行的状态链接，再读取文件及归属复验。最终合并请求固定 head SHA，GitHub 在执行时再次实施分支保护。合并消息由机器人生成，避免 PR 标题或提交正文中的跳过 CI 标记影响 Pages。GitHub 的 commit status 属于提交 SHA；不同 PR 可指向同一 SHA，因此维护者应让机器人完成普通日记的最终合并。[必需检查与 SHA](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

同一 PR 的作业串行，不同 PR 可并行校验。GitHub 状态传播延迟时会限时重读；超时、权限不足或未知状态会停止。待暂时性问题消失后可 **Re-run all jobs**。两个 PR 基于同一 main 时，第一篇合并后，严格保护可能要求第二个分支 **Update branch** 或手动同步；随后对新 SHA 重新校验。机器人不会修改参与者的 Fork。若合并请求已发送但响应丢失，先查看 PR 的 merged 状态，重跑已合并的 PR 不会再次合并。

## 真实仓库验收

| 操作 | 应核实的 GitHub 证据 |
| --- | --- |
| 两个外部账户各发当天一篇日记 | PR 的状态来源是专用 App，Details 指向本 PR 的运行；没有人工批准即可由 App squash。若第二个 PR 落后，同步后自动重验 |
| 修改自己已合并的旧日记 | 创建提交归属查询通过，历史更新被合并 |
| 提交草稿，再转 ready | 草稿保持打开；转 ready 后新运行才可合并 |
| 将一个仍在等待其他必需检查的合法 PR 改为混合或越权提交 | 新 head 的策略检查失败；旧 SHA 的绿灯不能让机器人合并。已有排队请求被平台或机器人清除 |
| 修改他人日记、同时提交两篇、删除或移动日记 | 对应 head 上出现失败状态，合并被阻止 |
| 只修改 README 或校验脚本 | 原 main 上的规则仍在执行；Code Owner 批准前被拦截，批准后由维护者人工合并 |
| 暂时撤销 App 授权或令另一个必需检查 pending | PR 保持未合并。恢复授权或检查后，重新运行并查看最新结果 |
| 检查分支保护 | 普通账户不能直推 main，App 没有 bypass，规则来源固定。若启用其他必需检查，逐一测试失败和挂起状态 |

Pages 需要单独验收。在一篇实际自动合并的 PR 页面记下 **squash commit SHA**。在 **Actions → Publish growth journal** 确认事件为 `push`、分支为 main、运行对应这个 SHA，并检查 build 与 deploy 均成功。也可执行：

```sh
gh pr view PR编号 --json mergeCommit,mergedBy
gh run list --workflow pages.yml --event push --commit 合并提交SHA
gh run watch 运行编号 --exit-status
```

打开部署 URL，在该作者个人主页核对日期格、日记列表及正文。若连续发布合并为较新的 Pages 部署，核对最终部署提交包含该篇日记。没有 push 运行时，检查 mergedBy、Actions 开关和工作流；有运行但部署失败时，检查 Pages Source、环境和作业日志。手动触发可恢复站点，但不能作为自动触发成功的证据。

## 账户改名

由本人使用新账户名发起迁移 PR。维护者逐项核对原创建 PR 的数字 ID、目标路径、日期和正文。迁移是受控维护例外，日记机器人会拒绝移动操作。获所有者授权后可在暂停其他合并的维护窗口处理，并保留原作者发起的 squash PR 作为新路径的归属记录；恢复并验收强制规则后再开放投稿。不要向机器人授予绕过权限。

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
