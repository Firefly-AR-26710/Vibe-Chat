# 问题追踪：GitHub

本项目的所有需求 (Issues) 和产品需求文档 (PRDs) 都作为 GitHub Issues 进行管理。请使用 `gh` 命令行工具进行所有操作。

## 操作规范

- **创建 Issue**：`gh issue create --title "..." --body "..."`。如果是多行内容，请使用 heredoc 格式。
- **读取 Issue**：`gh issue view <number> --comments`，可以通过 `jq` 过滤评论并获取标签信息。
- **列出 Issues**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，结合适当的 `--label` 和 `--state` 过滤参数。
- **添加评论**：`gh issue comment <number> --body "..."`
- **添加/移除标签**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **关闭 Issue**：`gh issue close <number> --comment "..."`

从 `git remote -v` 中推断所属的代码仓库——当在 clone 的仓库内部运行时，`gh` 会自动完成此推断。

## 当技能提示“发布到问题追踪系统 (publish to the issue tracker)”时
请创建一个 GitHub Issue。

## 当技能提示“获取相关工单 (fetch the relevant ticket)”时
请运行 `gh issue view <number> --comments`。
