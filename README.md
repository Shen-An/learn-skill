# learn-skill

> 一组通用的 **Agent Skill**：把学习与读论文的对话沉淀成可复练、可核查的结构化笔记。
> 同一份 `SKILL.md` 在 **DSH / OpenAI Codex / Claude Code** 三个 harness 通用（它们共享目录 bundle 格式）。

| Skill | 一句话 | 触发 |
|-------|--------|------|
| [`learning-wiki/`](./learning-wiki) | 把 AI 问答学习对话沉淀为结构化学习 Wiki | "总结这次学习，做成 wiki" |
| [`paper-reading/`](./paper-reading) | 把论文加工成可核查的中文精读笔记（讲解 / 填表 / 思维导图 + 可渲染导图 / 难点与解答 / 综述），并把整个笔记库管成 wiki（主题清单 / 术语速查 / 跨论文对比 / 证据强度总览） | "讲一下这篇论文" / "这篇论文有什么难点" / "整理我的论文笔记库" |

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

读论文时最贵的不是翻译，而是**分不清哪句话有据、哪句话是二手转述**。AI 总结里的数字、动机、消融常常是二手甚至编的，直接当结论用会带偏整个判断。本 skill 把"读论文"固化成七种可校验的产出：

| 模式 | 触发说法 | 产物 | 关键约束 |
|------|---------|------|---------|
| A 精读讲解 | "讲一下这篇论文" | `深读-<短名>.md` | 开头一段话总结核心；公式用 Markdown 数学（行间 `$$` 独占一行）；符号表；局限单列 |
| B 逐篇填表 | "按模板整理" | `表格-<短名>.md` | 只有一张 9 维表，表外无任何文字，每格 1–3 句 |
| C 思维导图（大纲） | "生成思维导图" | `思维导图-<短名>.md` | 固定四分支、层级 ≤4、无代码围栏 |
| E 可渲染导图 | 与 C 成套产出 | `导图-<短名>.md` | Mermaid mindmap：唯一 `root((短名))`、四分支顺序固定、层级 ≤4、节点文本禁用 ASCII `( ) [ ] { } , ; : %` |
| F 难点与解答 | "这篇论文有什么难点" | `难点-<短名>.md` | ≥3 条难点，每条含 `**难点**` / `**解答**`，解答必须带来源标记 |
| D 汇总综述 | "写文献综述" | `综述-<主题>.md` | 五节固定结构、`[num]` 标注、不给文献列表 |
| G 笔记库索引 | "整理我的论文笔记库"；每次交付后自动维护 | `paper-notes/README.md` | 固定五节 + 条目形状（链接 + 一句话结论 + 证据/代码括注）；增量只追加、不重排；跨论文冲突数字必须并列；死链与漏登记由校验器拦 |

输入支持 **PDF**（工作区路径或上传件，转成带页锚点的 `_source/` 文本，引用可标到页如 `[原文 p.12]`）、DOI/arXiv、官方摘要、他人总结、官方代码仓库。它的核心机制是**证据分层**：每条断言都要归到 `[原文]` / `[代码]` / `[摘要]` / `[二手]` / `[推断]`，二手数字必须与原文并列或标"待核对"，两个来源冲突时**两个都写、不许调和**。此外强制"读者假设"：有领域通用基础、无本小方向基础，术语首现必须给出大白话解释与相邻概念的分界。导图另出 Mermaid 形态，**并如实说明渲染能力**：Obsidian / GitHub 能出图，DSH Web GUI 只做语法高亮、不出图（要出图就打开 `导图-<短名>.md`）。

笔记多起来之后，`paper-notes/README.md` 作为**合集层**回答另一个问题："我读过哪些论文、它们彼此在哪里冲突、我的证据只到哪一层"。它按主题分组登记（条目 = 链接 + 一句话结论 + 证据类型/有无代码）、给术语速查、跨论文对比、未解决问题与证据强度总览，**只追加、不重排**，冲突数字在对比表里同样并列——像 wiki 一样长期维护，而不是一次性的目录清单。

### 产出长什么样

```
paper-notes/
├── README.md               # 库索引（合集层）：主题清单 + 术语速查 + 跨论文对比 + 未解决问题 + 证据强度总览
└── <论文短名>/
    ├── README.md           # 单篇索引 + 一句话结论 + 证据强度提示
    ├── _source/<论文名>.md  # PDF 导入产物，含 <!-- page:N --> 页锚点
    ├── 深读-<短名>.md       # 背景与动机 → 符号表 → 方法 → 实验 → 贡献 → 局限 → 证据与出处
    ├── 表格-<短名>.md
    ├── 思维导图-<短名>.md   # 四分支大纲（主形态，跨 harness 可读）
    ├── 导图-<短名>.md       # 同一导图的 Mermaid 可渲染形态
    ├── 难点-<短名>.md       # 难点与解答，每条带来源标记
    └── 综述-<主题>.md       # 多篇时
```

参考实例：`paper-notes/MFAA/`（对一篇 TIFS 2025 对抗攻击论文的真实产出，五件套同时作为 `paper-reading/sample/` 的回归正样本），以及 `paper-notes/README.md`（同一篇论文的库索引，可直接 `python paper-reading/scripts/check_paper_note.py paper-notes/README.md --mode index` 校验）。

## 安装

三个平台都遵循 `<skill名>/SKILL.md` 目录 bundle 格式，把目标 skill 文件夹整个放进对应扫描目录即可，无需编译安装。

### 一条命令同步：`install.ps1`

```powershell
pwsh install.ps1                    # 两个 skill 同步到三个平台根目录
pwsh install.ps1 -DryRun            # 只看会做什么，不写盘
pwsh install.ps1 -Only paper-reading
pwsh install.ps1 -Roots "$HOME\.agents\skills"
```

脚本自动发现仓库里所有含 `SKILL.md` 的子目录，对每个 (skill × 根目录) 执行：**已是同版本则跳过**（顺手清掉副本里的 `__pycache__` 残留）；否则 **旧版改名保全 → 拷新版 → 逐文件 SHA-256 比对 → 跑该 skill 的回归门禁 → 通过才删旧版，不通过自动回滚**。退出码 0（全成功）/ 1（有失败）。安装副本一律不含本地证据账本 `feedback/ledger.jsonl`（该文件由运行时自建）。默认根目录为 `~/.agents/skills`、`~/.claude/skills`、`~/.codex/skills`，可用 `-Roots` 覆盖；`-SkipGate` 跳过门禁（不推荐）、`-KeepBackup` 保留被替换的旧版目录。

### 手动安装

#### DSH

```bash
# 用户级（所有项目可用；热发现，无需重启）
cp -r learning-wiki ~/.dsh/skills/        # 或 ~/.agents/skills/
cp -r paper-reading ~/.dsh/skills/
# 项目级
cp -r learning-wiki <项目>/.dsh/skills/   # 或 <项目>/.agents/skills/
cp -r paper-reading <项目>/.dsh/skills/
```

#### Claude Code

```bash
# 个人级（所有项目可用）
cp -r learning-wiki ~/.claude/skills/
cp -r paper-reading ~/.claude/skills/
# 项目级（可提交进仓库共享给团队）
cp -r learning-wiki <项目>/.claude/skills/
```

#### Codex

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

## 怎么导入论文 PDF

三条通道，按优先级用；三条的产出契约完全一样，都是"带页锚点的正文 + 页码可引用"。

**通道 1 · 让 harness 自己读（首选，不需要装任何东西）**

把 PDF 放进工作区，或者说一句"导入这个 PDF 并精读"。DSH 用 `read_document`（长文可 `offset`/`limit` 分页读完）、Claude Code 与 Codex 用各自的 PDF 读入能力。

**通道 2 · 对话里上传的附件**

上传件同样走 harness 的文档读取能力。**务必用文档读取，不要当纯文本读**——中文 PDF 按纯文本读会乱码，公式会散架。

**通道 3 · 回退脚本 `pdf_extract.py`**

harness 没有文档读取能力时，或你想把 PDF 固化成可 grep、可 diff 的文本时：

```bash
# 单篇：产出 <PDF 所在目录>/_source/<论文名>.md
python paper-reading/scripts/pdf_extract.py 论文.pdf

# 指到笔记目录下，便于精读时引用
python paper-reading/scripts/pdf_extract.py 论文.pdf --out paper-notes/MFAA/_source/

# 只抽第 3 页 / 第 1–20 页（闭区间）
python paper-reading/scripts/pdf_extract.py 论文.pdf --pages 3
python paper-reading/scripts/pdf_extract.py 论文.pdf --pages 1-20

# 一个目录里的所有 PDF（默认只扫一层，加 --recursive 递归）
python paper-reading/scripts/pdf_extract.py ./pdfs/ --recursive

python paper-reading/scripts/pdf_extract.py --help
```

依赖只有 `pypdf`（没装就 `pip install pypdf`；脚本也兼容旧的 `PyPDF2`）。

### 它产出什么

`<输出目录>/<论文主文件名>.md`（`demo.pdf` → `demo.md`，**不带** `.pdf`）：

```markdown
<!-- source: demo.pdf -->
<!-- pages: 3 -->
<!-- extracted: 2025-01-01T12:00:00+08:00 -->
<!-- tool: pdf_extract.py -->

<!-- page:1 -->
第 1 页正文……

<!-- page:2 -->
> [本页无可提取文本层，可能是扫描件，需要 OCR]

<!-- page:3 -->
第 3 页正文……
```

头部四行是元信息（不污染正文解析）；每页正文前有 `<!-- page:N -->`，`N` 是 PDF 的**物理页码**——`--pages` 只裁剪输出范围，不会把页码重编号。

**这些锚点就是笔记里页码引用的依据**：正文写 `[原文 p.12]`，读者能直接翻到那一页核对。校验器会盯这条规则——笔记声明"来源类型：PDF 全文"却一个页码锚点都没有，报 `W-DEEP-PAGE`（这是防"声称读了全文、其实只看了摘要"）。

### 退出码与常见故障

| 退出码 | 含义 | 怎么办 |
|---|---|---|
| 0 | 成功（目录里没有 PDF 也算成功，只给 WARN） | — |
| 1 | 解析失败：文件损坏、或根本不是 PDF | 确认文件能打开；把 `.md` 改名成 `.pdf` 会走到这里 |
| 2 | 参数或路径错误 | 缺参数、`--pages` 格式非法/越界、路径不存在、输入不是 `.pdf` |
| 3 | 缺依赖 | `pip install pypdf`（受限环境 `pip install --user pypdf`） |
| 4 | PDF 已加密，空密码解不开 | 先解密另存，再导入 |

目录模式下会**逐文件处理**（单个文件失败不影响其它文件继续抽），最终退出码取各文件退出码的**最大值**——所以目录里只要有一个加密 PDF，整批就是 `4`，但其它文件其实已经正常写出来了。

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `[WARN ] 疑似扫描页` + `> [本页无可提取文本层…]` 占位 | 该页是图片、没有文本层 | 走 OCR（harness 的 OCR 或 `read_image`），笔记里把该处来源标成 `[OCR]` |
| `[WARN ] 目录下没有 PDF 文件` | 目录模式默认只扫一层 | 加 `--recursive`，或直接指向具体文件 |
| 引用的页码与论文印刷页码对不上 | 带封面/预印本的 PDF 物理页码 ≠ 印刷页码 | 锚点永远是物理页码；笔记里注明"页码按 PDF 计" |
| 公式抽出来是乱码 | 文本层里的数学符号编码不规范 | 以 PDF 为准，用 harness 文档读取复看该页；公式按 `references/formula-style.md` 重写 |

### 想先试试脚本？

仓库自带一个 3 页假论文 fixture，跑一遍就能看到完整输出结构（`--out` 指到工作目录，别写在仓库里）：

```bash
python paper-reading/scripts/pdf_extract.py paper-reading/evals/pdf-cases/三页样例.pdf --out ./pdf-demo
```

`paper-reading/evals/` 下还有空文本页（触发扫描页告警）与加密样例（触发退出码 4），以及生成它们的 `pdf-cases/make_fixtures.py`。

### 从 PDF 到七种产出（完整流程）

```
你：这篇 PDF 帮我精读，顺便出难点文档
它：① pdf_extract.py 落盘 → _source/<论文名>.md（带 <!-- page:N -->）
    ② 深读-<短名>.md    背景与动机 → 符号表 → 方法 → 实验 → 贡献 → 局限 → 证据与出处（含 [原文 p.N]）
    ③ 表格-<短名>.md    9 维表
    ④ 思维导图-<短名>.md + 导图-<短名>.md（Mermaid 形态，Obsidian/GitHub 可出图）
    ⑤ 难点-<短名>.md    难点与解答，每条解答带来源标记
    ⑥ paper-notes/README.md  库索引登记：主题清单 + 术语速查 + 跨论文对比 + 未解决问题 + 证据强度总览
```

## 仓库结构

```
.
├── README.md
├── LICENSE                     # MIT
├── install.ps1                 # 一条命令同步到三个平台：哈希校验 + 跑门禁 + 失败回滚
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
    ├── SKILL.md                # 主指令：七种产出（含笔记库索引）+ 证据分层纪律 + 可渲染优先 + Step 1–7
    ├── CHANGELOG.md
    ├── scripts/
    │   ├── check_paper_note.py # 机械校验：结构/公式定界符与独占行/表格/引用范围/模式混装/导图渲染/难点字段/库索引结构，七模式各一套
    │   └── pdf_extract.py      # PDF 导入：逐页提取 + `<!-- page:N -->` 页锚点 + 扫描页标记
    ├── evals/
    │   ├── run_evals.py        # 回归门禁：good/warn/bad 样本 + sample/ 真实产出 + PDF 抽取器契约 + 论文库索引
    │   ├── good-sample/        # 正样本 fixture（六种单篇模式各一；库索引正样本在 index-cases/）
    │   ├── warn-sample/        # WARN 类 fixture（应退出 0 但命中指定 WARN）
    │   ├── bad-sample/         # 负样本 fixture（故意违规，勿修）
    │   ├── pdf-cases/          # PDF 抽取器 fixture（3 页样例 / 空白页 / 加密 / 假 PDF）+ make_fixtures.py
    │   └── index-cases/        # 笔记库索引 fixture（正/警/负样本 + 漏登记反向检查）
    ├── feedback/
    │   └── ledger.example.jsonl
    ├── sample/                 # 真实产出（MFAA 论文笔记五件套）= 端到端正样本
    └── references/
        ├── deep-read-template.md  # 模式 A：精读讲解结构（含模式分离与公式块要求）
        ├── table-template.md      # 模式 B：填表纪律 + 独立交付纪律
        ├── mindmap-template.md    # 模式 C/E：四分支思维导图 + one-shot + Mermaid 形态与渲染能力对照
        ├── faq-template.md        # 模式 F：难点与解答（五字段结构 + 难点五类来源 + 反编造约束）
        ├── review-template.md     # 模式 D：汇总综述骨架 + [num] 规则
        ├── index-template.md      # 模式 G：笔记库索引骨架 + 条目形状 + 增量续写规则 + 10 个检查码
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
- **可机械化的就不靠自觉**：结构、公式定界符、表格列数、引用编号、库索引的死链与漏登记这类能查的都交给脚本；rubric 只留"忠实性""论证链""讲解密度"这些机器判不了的

## 贡献 / 反馈

Issue & PR 欢迎。改完先跑回归门禁（必须全绿）：

```bash
python learning-wiki/evals/run_evals.py
python paper-reading/evals/run_evals.py
pwsh install.ps1                # 门禁全绿后同步到三个平台（同样会跑门禁 + 哈希校验）
```

再在三个平台里至少一个实测一次（对话/论文 → 产出 → 对照对应 `quality-rubric.md` 自检）。改规则的完整流程见各 skill 的 `references/self-iteration.md`。
