# 提交与合并

## 保存并推送

用自己的实际日记路径替换下例。Commit 将本次修改保存为一条本地记录，Push 将它上传到你的 Fork。

```sh
git add -- journal/26/11/23/alice.md
git status
git commit -m "记录今天的小成功"
git push -u origin diary-first
```

确认待提交区只有自己的一个文件。首次 Push 时根据凭据管理器提示登录 GitHub。

## 创建 Pull Request

在 Fork 页面点 **Compare & pull request**，目标选原仓库的 **main**，来源选自己的日记分支。在 **Files changed** 核对内容后提交。Pull Request 是请维护者合并修改的请求。检查通过并合并后，日记会在网站下次部署时出现。

## 下一次记录

先在 Fork 首页点 **Sync fork → Update branch**，然后从更新后的 main 新建分支。每篇使用一个未用过的分支名。

```sh
git switch main
git pull --ff-only origin main
git switch -c diary-next
```

修改旧日记时直接编辑自己的原文件，然后重新提交 PR。
