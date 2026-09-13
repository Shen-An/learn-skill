# learn-skill

> 一个通用的 **Agent Skill**：把 AI 问答学习对话沉淀为结构化学习 Wiki。
> 同一份 `SKILL.md` 在 **DSH / OpenAI Codex / Claude Code** 三个 harness 通用（它们共享目录 bundle 格式）。

## 它解决什么问题

频繁开对话学习一个主题时，知识散落在几十个会话窗口里，回头找不到"当时是怎么想通的"。
安装本 skill 后，任何时候说一句 **"总结这次学习，做成 wiki"**，它就会：

- 按**因果链**组织章节（每个机制由上一个机制的局限逼出来），而不是百科式词条
- 还原你的**真实提问**作小节标题，保留你**踩过的误解**（❌ 直觉版 → ✅ 修正版）
- 术语首现必释 + 全表速查、每篇 Mermaid 流程图、自测题配**推演式参考答案**
- 支持**增量续写**：下次学到新内容，它会找到已有 wiki 继续生长，不推倒重来

## 产出长什么样

```
learning-<主题>/
├── README.md          # 因果链一图流 + 目录 + 术语速查 + 复习建议
├── 01-....md          # 一章 = 一个"局限 → 机制 → 代价"循环
├── 02-....md
└── ...                # 每篇：真实问题标题、Mermaid 流程图、一句话总结、自测题+参考答案
```

参考实例：本仓库未附带，可在你自己的项目里试跑一次——用对话学完一个主题后调用即可。

## 安装

三个平台都遵循 `<skill名>/SKILL.md` 目录 bundle 格式，把 `learn-wiki/` 整个文件夹放进对应扫描目录即可，无需编译安装：

### DSH

```bash
# 用户级（所有项目可用；热发现，无需重启）
cp -r learn-wiki ~/.dsh/skills/        # 或 ~/.agents/skills/
# 项目级
cp -r learn-wiki <项目>/.dsh/skills/   # 或 <项目>/.agents/skills/
```

### Claude Code

```bash
# 个人级（所有项目可用）
cp -r learn-wiki ~/.claude/skills/
# 项目级（可提交进仓库共享给团队）
cp -r learn-wiki <项目>/.claude/skills/
```

### Codex

```bash
# 全局
cp -r learn-wiki ~/.codex/skills/
# 项目级见官方文档：https://learn.chatgpt.com/docs/build-skills
```

## 使用

在任意学习对话里（哪怕对话已经进行了很久）：

```
/learning-wiki
```

或者直接说：`总结这次学习，做成学习 wiki` / `把这次问答整理成 wiki`。

可选指定：输出路径（默认 `./learning-<主题>/`）、只要某一部分、增量更新已有目录。

## 仓库结构

```
.
├── README.md
├── LICENSE                     # MIT
└── learn-wiki/                 # ← 把这一层作为 skill 目录安装
    ├── SKILL.md                # 主指令（frontmatter: name/description）
    └── references/
        ├── chapter-template.md # 章节模板 + Mermaid 骨架 + 风格示例
        ├── readme-template.md  # 总览模板 + 因果链图画法
        └── quality-rubric.md   # 交付前质量清单（结构/忠实性/术语/图表/自测）
```

## 设计说明（为什么这样有效）

- **忠实性优先**：skill 明令禁止编造对话之外的内容，误解轨迹不许被"顺滑"——复练价值恰恰在记录"错路"
- **渐进披露**：SKILL.md 只留工作流骨架，模板与质检清单放 `references/`，按需加载省上下文
- **零工具依赖**：只读写 Markdown，任何有文件读写能力的 agent harness 理论上都能跑

## 贡献 / 反馈

Issue & PR 欢迎。改完记得在三个平台里至少一个实测一次（对话→产出→对照 `quality-rubric.md` 自检）。
