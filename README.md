# learn-skill

> 一组通用的 **Agent Skill**：把学习与读论文的对话沉淀成可复练、可核查的结构化笔记。
> 同一份 `SKILL.md` 在 **DSH / OpenAI Codex / Claude Code** 三个 harness 通用（它们共享目录 bundle 格式）。

| Skill | 一句话 | 触发 |
|-------|--------|------|
| [`learning-wiki/`](./learning-wiki) | 把 AI 问答学习对话沉淀为结构化学习 Wiki | "总结这次学习，做成 wiki" |
| [`paper-reading/`](./paper-reading) | 把论文加工成可核查的中文精读笔记（讲解 / 填表 / 思维导图 + 可渲染导图 / 难点与解答 / 综述） | "讲一下这篇论文" / "这篇论文有什么难点" / "写文献综述" |

## learning-wiki：对话 → 学习 Wiki

### 它解决什么问题

频繁开对话学习一个主题时，知识散落在几十个会话窗口里，回头找不到"当时是怎么想通的"。
安装本 skill 后，任何时候说一句 **"总结这次学习，做成 wiki"**，它就会：

- 按**因果链**组织章节（每个机制由上一个机制的局限逼出来），而不是百科式词条
- 还原你的**真实提问**作小节标题，保留你**踩过的误解**（❌ 直觉版 → ✅ 修正版）
- 术语首现必释 + 全表速查、每篇 Mermaid 流程图、自测题配**推演式参考答案**
- 支持**增量续写**：下次学到新内容，它会找到已有 wiki 继续生长，不推倒重来

### 产出长什么样

```
learning-<主题>/
├── README.md          # 因果链一图流 + 目录 + 术语速查 + 复习建议
├── 01-....md          # 一章 = 一个"局限 → 机制 → 代价"循环
├── 02-....md
└── ...                # 每篇：真实问题标题、Mermaid 流程图、一句话总结、自测题+参考答案
```

## paper-reading：论文 → 可核查笔记

### 它解决什么问题

读论文时最贵的不是翻译，而是**分不清哪句话有据、哪句话是二手转述**。AI 总结里的数字、动机、消融常常是二手甚至编的，直接当结论用会带偏整个判断。本 skill 把"读论文"固化成六种可校验的产出：

| 模式 | 触发说法 | 产物 | 关键约束 |
|------|---------|------|---------|
| A 精读讲解 | "讲一下这篇论文" | `深读-<短名>.md` | 开头一段话总结核心；公式用 Markdown 数学（行间 `$$` 独占一行）；符号表；局限单列 |
| B 逐篇填表 | "按模板整理" | `表格-<短名>.md` | 只有一张 9 维表，表外无任何文字，每格 1–3 句 |
| C 思维导图（大纲） | "生成思维导图" | `思维导图-<短名>.md` | 固定四分支、层级 ≤4、无代码围栏 |
| E 可渲染导图 | 与 C 成套产出 | `导图-<短名>.md` | Mermaid mindmap：唯一 `root((短名))`、四分支顺序固定、层级 ≤4、节点文本禁用 ASCII `( ) [ ] { } , ; : %` |
| F 难点与解答 | "这篇论文有什么难点" | `难点-<短名>.md` | ≥3 条难点，每条含 `**难点**` / `**解答**`，解答必须带来源标记 |
| D 汇总综述 | "写文献综述" | `综述-<主题>.md` | 五节固定结构、`[num]` 标注、不给文献列表 |

输入支持 **PDF**（工作区路径或上传件，转成带页锚点的 `_source/` 文本，引用可标到页如 `[原文 p.12]`）、DOI/arXiv、官方摘要、他人总结、官方代码仓库。它的核心机制是**证据分层**：每条断言都要归到 `[原文]` / `[代码]` / `[摘要]` / `[二手]` / `[推断]`，二手数字必须与原文并列或标"待核对"，两个来源冲突时**两个都写、不许调和**。此外强制"读者假设"：有领域通用基础、无本小方向基础，术语首现必须给出大白话解释与相邻概念的分界。导图另出 Mermaid 形态，**并如实说明渲染能力**：Obsidian / GitHub 能出图，DSH Web GUI 只做语法高亮、不出图（要出图就打开 `导图-<短名>.md`）。

### 产出长什么样

```
paper-notes/<论文短名>/
├── README.md              # 索引 + 一句话结论 + 证据强度提示
├── _source/<论文名>.md     # PDF 导入产物，含 <!-- page:N --> 页锚点
├── 深读-<短名>.md          # 背景与动机 → 符号表 → 方法 → 实验 → 贡献 → 局限 → 证据与出处
├── 表格-<短名>.md
├── 思维导图-<短名>.md      # 四分支大纲（主形态，跨 harness 可读）
├── 导图-<短名>.md          # 同一导图的 Mermaid 可渲染形态
├── 难点-<短名>.md          # 难点与解答，每条带来源标记
└── 综述-<主题>.md          # 多篇时
```

参考实例：`paper-notes/MFAA/`（对一篇 TIFS 2025 对抗攻击论文的真实产出，五件套同时作为 `paper-reading/sample/` 的回归正样本）。

## 安装

三个平台都遵循 `<skill名>/SKILL.md` 目录 bundle 格式，把目标 skill 文件夹整个放进对应扫描目录即可，无需编译安装：

### DSH

```bash
# 用户级（所有项目可用；热发现，无需重启）
cp -r learning-wiki ~/.dsh/skills/        # 或 ~/.agents/skills/
cp -r paper-reading ~/.dsh/skills/
# 项目级
cp -r learning-wiki <项目>/.dsh/skills/   # 或 <项目>/.agents/skills/
cp -r paper-reading <项目>/.dsh/skills/
```

### Claude Code

```bash
# 个人级（所有项目可用）
cp -r learning-wiki ~/.claude/skills/
cp -r paper-reading ~/.claude/skills/
# 项目级（可提交进仓库共享给团队）
cp -r learning-wiki <项目>/.claude/skills/
```

### Codex

```bash
# 全局
cp -r learning-wiki ~/.codex/skills/
cp -r paper-reading ~/.codex/skills/
# 项目级见官方文档：https://learn.chatgpt.com/docs/build-skills
```

## 使用

在任意学习或读论文的对话里（哪怕对话已经进行了很久）：

```
/learning-wiki     # 总结这次学习，做成学习 wiki
/paper-reading     # 讲一下这篇论文 / 导入这个 PDF 并精读 / 按模板填表 / 生成思维导图（含可渲染 Mermaid）/ 这篇论文有什么难点 / 写文献综述
```

可选指定：输出路径（默认 `./learning-<主题>/` 与 `./paper-notes/<短名>/`）、只要某一模式、增量更新已有目录。

## 仓库结构

```
.
├── README.md
├── LICENSE                     # MIT
├── learning-wiki/                 # ← 把这一层作为 skill 目录安装
│   ├── SKILL.md                # 主指令：Step 1–5 生成流程 + Step 6 触发式自迭代
│   ├── CHANGELOG.md            # 版本变更账（每次 bump 须过门禁 + 人工确认）
│   ├── scripts/
│   │   └── check_wiki.py       # 机械校验 E1–E5 / W1–W3：链接/围栏/编号/必备小节/悬空引用
│   ├── evals/
│   │   ├── run_evals.py        # 回归门禁：正样本 0 错 + 负样本 8 类埋错逐类被抓
│   │   └── bad-wiki/           # 负样本 fixture（故意不合格的 wiki，勿修）
│   ├── feedback/
│   │   └── ledger.example.jsonl # 证据账本格式：失败信号先记账，攒够证据才迭代
│   ├── sample-wiki/            # 示例产出 = 回归正样本（3 章，真实通过校验器）
│   └── references/
│       ├── chapter-template.md # 章节模板 + Mermaid 骨架 + 风格示例
│       ├── readme-template.md  # 总览模板 + 因果链图画法
│       ├── quality-rubric.md   # 人工质检清单（只留机器查不了的）
│       └── self-iteration.md   # RSI 协议：触发条件/最小 diff/宪法区/防膨胀
└── paper-reading/                 # ← 把这一层作为 skill 目录安装
    ├── SKILL.md                # 主指令：六种产出 + 证据分层纪律 + 可渲染优先 + Step 1–6
    ├── CHANGELOG.md
    ├── scripts/
    │   ├── check_paper_note.py # 机械校验：结构/公式定界符与独占行/表格/引用范围/模式混装/导图渲染/难点字段，六模式各一套
    │   └── pdf_extract.py      # PDF 导入：逐页提取 + `<!-- page:N -->` 页锚点 + 扫描页标记
    ├── evals/
    │   ├── run_evals.py        # 回归门禁：good/warn/bad 样本 + sample/ 真实产出
    │   ├── good-sample/        # 正样本 fixture（六种模式各一）
    │   ├── warn-sample/        # WARN 类 fixture（应退出 0 但命中指定 WARN）
    │   └── bad-sample/         # 负样本 fixture（故意违规，勿修）
    ├── feedback/
    │   └── ledger.example.jsonl
    ├── sample/                 # 真实产出（MFAA 论文笔记五件套）= 端到端正样本
    └── references/
        ├── deep-read-template.md  # 模式 A：精读讲解结构（含模式分离与公式块要求）
        ├── table-template.md      # 模式 B：填表纪律 + 独立交付纪律
        ├── mindmap-template.md    # 模式 C/E：四分支思维导图 + one-shot + Mermaid 形态与渲染能力对照
        ├── faq-template.md        # 模式 F：难点与解答（五字段结构 + 难点五类来源 + 反编造约束）
        ├── review-template.md     # 模式 D：汇总综述骨架 + [num] 规则
        ├── formula-style.md       # 公式：Markdown 数学定界符 / 记法约定 / 渲染自检
        ├── input-intake.md        # 输入接入：PDF/摘要/DOI/二手 的可讲深度与页锚点规范
        ├── grounding-rules.md     # 证据五级标记 / 冲突处理 / 可讲深度判定
        ├── quality-rubric.md      # 人工质检清单（忠实性、论证链、讲解密度、可渲染性）
        └── self-iteration.md      # RSI 协议
```

## 设计说明（为什么这样有效）

- **忠实性优先**：skill 明令禁止编造对话或论文之外的内容。learning-wiki 不许把误解"顺滑"成"一开始就正确"；paper-reading 不许把二手转述当原文结论，冲突数字必须并列
- **渐进披露**：SKILL.md 只留工作流骨架，模板与质检清单放 `references/`，按需加载省上下文
- **零工具依赖**：只读写 Markdown，校验器只用标准库；唯一可选依赖是 PDF 回退通道的 `pypdf`（缺失时脚本明确报错并退出码 3，不静默失败）
- **只承诺渲染器做得到的**：公式用 Markdown 数学、导图另出 Mermaid，但会明确告知目标渲染器能不能出图（DSH Web GUI 只做语法高亮），不把"代码块"说成"已渲染的脑图"
- **验证 + 自迭代闭环**：校验器输出错误码 → 错误码与返工记入 ledger → 攒够证据才触发复盘 → 改动过 `evals/run_evals.py` 回归门禁才准升版本。skill 只在有证据时改规则，且改完能证明没把好的改坏
- **可机械化的就不靠自觉**：结构、公式定界符、表格列数、引用编号这类能查的都交给脚本；rubric 只留"忠实性""论证链""讲解密度"这些机器判不了的

## 贡献 / 反馈

Issue & PR 欢迎。改完先跑回归门禁（必须全绿）：

```bash
python learning-wiki/evals/run_evals.py
python paper-reading/evals/run_evals.py
```

再在三个平台里至少一个实测一次（对话/论文 → 产出 → 对照对应 `quality-rubric.md` 自检）。改规则的完整流程见各 skill 的 `references/self-iteration.md`。
