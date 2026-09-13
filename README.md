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

三个平台都遵循 `<skill名>/SKILL.md` 目录 bundle 格式，把 `learning-wiki/` 整个文件夹放进对应扫描目录即可，无需编译安装：

### DSH

```bash
# 用户级（所有项目可用；热发现，无需重启）
cp -r learning-wiki ~/.dsh/skills/        # 或 ~/.agents/skills/
# 项目级
cp -r learning-wiki <项目>/.dsh/skills/   # 或 <项目>/.agents/skills/
```

### Claude Code

```bash
# 个人级（所有项目可用）
cp -r learning-wiki ~/.claude/skills/
# 项目级（可提交进仓库共享给团队）
cp -r learning-wiki <项目>/.claude/skills/
```

### Codex

```bash
# 全局
cp -r learning-wiki ~/.codex/skills/
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
└── learning-wiki/                 # ← 把这一层作为 skill 目录安装
    ├── SKILL.md                # 主指令：Step 1–5 生成流程 + Step 6 触发式自迭代
    ├── CHANGELOG.md            # 版本变更账（每次 bump 须过门禁 + 人工确认）
    ├── scripts/
    │   └── check_wiki.py       # 机械校验 E1–E5 / W1–W3：链接/围栏/编号/必备小节/悬空引用
    ├── evals/
    │   ├── run_evals.py        # 回归门禁：正样本 0 错 + 负样本 8 类埋错逐类被抓
    │   └── bad-wiki/           # 负样本 fixture（故意不合格的 wiki，勿修）
    ├── feedback/
    │   └── ledger.example.jsonl # 证据账本格式：失败信号先记账，攒够证据才迭代
    ├── sample-wiki/            # 示例产出 = 回归正样本（3 章，真实通过校验器）
    └── references/
        ├── chapter-template.md # 章节模板 + Mermaid 骨架 + 风格示例
        ├── readme-template.md  # 总览模板 + 因果链图画法
        ├── quality-rubric.md   # 人工质检清单（只留机器查不了的）
        └── self-iteration.md   # RSI 协议：触发条件/最小 diff/宪法区/防膨胀
```

## 设计说明（为什么这样有效）

- **忠实性优先**：skill 明令禁止编造对话之外的内容，误解轨迹不许被"顺滑"——复练价值恰恰在记录"错路"
- **渐进披露**：SKILL.md 只留工作流骨架，模板与质检清单放 `references/`，按需加载省上下文
- **零工具依赖**：只读写 Markdown，任何有文件读写能力的 agent harness 理论上都能跑
- **验证 + 自迭代闭环**：校验器输出错误码 → 错误码与返工记入 ledger → 攒够证据才触发复盘 → 改动过 `evals/run_evals.py` 回归门禁才准升版本。skill 只在有证据时改规则，且改完能证明没把好的改坏

## 贡献 / 反馈

Issue & PR 欢迎。改完先跑回归门禁 `python learning-wiki/evals/run_evals.py`（必须全绿），再在三个平台里至少一个实测一次（对话→产出→对照 `quality-rubric.md` 自检）。改规则的完整流程见 `learning-wiki/references/self-iteration.md`。
