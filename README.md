# learn-skill

> 一组通用的 **Agent Skill**：把学习与读论文的对话沉淀成可复练、可核查的结构化笔记。
> 同一份 `SKILL.md` 在 **DSH / OpenAI Codex / Claude Code** 三个 harness 通用（它们共享目录 bundle 格式）。

| Skill | 一句话 | 触发 |
|-------|--------|------|
| [`learning-wiki/`](./learning-wiki) | 把 AI 问答学习对话沉淀为结构化学习 Wiki | "总结这次学习，做成 wiki" |
| [`paper-reading/`](./paper-reading) | 把论文加工成可核查的中文精读笔记（讲解 / 填表 / 思维导图 + 可渲染导图 / 难点与解答 / 中英对照术语表 / 综述），并把整个笔记库管成 wiki（主题清单 / 术语速查 / 跨论文对比 / 证据强度总览） | "讲一下这篇论文" / "这篇论文有什么难点" / "出个中英对照术语表" / "整理我的论文笔记库" |

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

读论文时最贵的不是翻译，而是**分不清哪句话有据、哪句话是二手转述**。AI 总结里的数字、动机、消融常常是二手甚至编的，直接当结论用会带偏整个判断。本 skill 把"读论文"固化成八种可校验的产出：

| 模式 | 触发说法 | 产物 | 关键约束 |
|------|---------|------|---------|
| A 精读讲解 | "讲一下这篇论文" | `深读-<短名>.md` | 开头一段话总结核心；公式用 Markdown 数学（行间 `$$` 独占一行）；符号表；局限单列 |
| B 逐篇填表 | "按模板整理" | `表格-<短名>.md` | 只有一张 9 维表，表外无任何文字，每格 1–3 句 |
| C 思维导图（大纲） | "生成思维导图" | `思维导图-<短名>.md` | 固定四分支、层级 ≤4、无代码围栏 |
| E 可渲染导图 | 与 C 成套产出 | `导图-<短名>.md` | Mermaid mindmap：唯一 `root((短名))`、四分支顺序固定、层级 ≤4、节点文本禁用 ASCII `( ) [ ] { } , ; : %` |
| F 难点与解答 | "这篇论文有什么难点" | `难点-<短名>.md` | ≥3 条难点，每条含 `**难点**` / `**解答**`，解答必须带来源标记 |
| H 专业术语表 | "出术语表""中英术语对照" | `术语-<短名>.md` | 六节固定结构；**英文原词必须保留**（英文列缺拉丁字母即 ERROR）；全量收录（< 15 行告警）；出处可用 `[原文 p.7]`；≥5 条英文原句摘录 |
| D 汇总综述 | "写文献综述" | `综述-<主题>.md` | 五节固定结构、`[num]` 标注、不给文献列表 |
| G 笔记库索引 | "整理我的论文笔记库"；每次交付后自动维护 | `paper-notes/README.md` | 固定五节 + 条目形状（链接 + 一句话结论 + 证据/代码括注）；增量只追加、不重排；跨论文冲突数字必须并列；死链与漏登记由校验器拦 |

**默认交付集（v1.6.0 起）**：说"读论文 / 讲论文 / 总结 / 精读"，或只丢来 PDF/链接而没点名模式时，默认**成套产出 A + B + C + E + F + H**（G 照旧必做）——六件全部落盘、各自独立成文件，正文只展开你点名的那个模式，其余静默落盘并在交付开头列出"文件清单 + 每件一句话"与省略原因。点名单个模式（"只讲一下""填这个表""要能渲染的导图""出个术语表"）时就只出那一件；`D` 只在一次给多篇且要求"对比/综述/趋势"时产出，**不进默认集**。

> 上表八种是**产出种类**。此外每篇论文目录里还有一个**单篇索引** `README.md`（模式 `note`）：它不是第九种产出，而是把已交付的文件登记成入口页（论文身份 + 一句话结论 + 全量文件登记 + 证据强度提示 + 待核入口），同样可机械校验——`--mode note` 共 11 项，专拦**漏登记**、死链、缺 `（模式 X）` 标签。真实踩过：某篇笔记的索引漏登记了两个早已交付的产出，索引不全比没有索引更误导人。

输入支持 **PDF**（工作区路径或上传件，转成带页锚点的 `_source/` 文本，引用可标到页如 `[原文 p.12]`）、DOI/arXiv、官方摘要、他人总结、官方代码仓库。它的核心机制是**证据分层**：每条断言都要归到 `[原文 p.12]` / `[代码]` / `[摘要]` / `[二手]` / `[OCR]` / `[推断]`（另有实验章节定位标签 `[实验]` 与数字引用 `[19]`），二手数字必须与原文并列或标"待核对"，两个来源冲突时**两个都写、不许调和**。此外强制"读者假设"：有领域通用基础、无本小方向基础，术语首现必须给出大白话解释与相邻概念的分界。导图另出 Mermaid 形态，**并如实说明渲染能力**：Obsidian / GitHub 能出图，DSH Web GUI 只做语法高亮、不出图（要出图就打开 `导图-<短名>.md`）。

笔记多起来之后，`paper-notes/README.md` 作为**合集层**回答另一个问题："我读过哪些论文、它们彼此在哪里冲突、我的证据只到哪一层"。它按主题分组登记（条目 = 链接 + 一句话结论 + 证据类型/有无代码）、给术语速查、跨论文对比、未解决问题与证据强度总览，**只追加、不重排**，冲突数字在对比表里同样并列——像 wiki 一样长期维护，而不是一次性的目录清单。

### 产出长什么样

```
paper-notes/
├── README.md               # 库索引（合集层）：主题清单 + 术语速查 + 跨论文对比 + 未解决问题 + 证据强度总览
└── <论文短名>/
    ├── README.md           # 单篇索引（模式 note）：论文身份 + 一句话结论 + 全量文件登记 + 证据强度提示 + 待核入口
    ├── _source/<论文名>.md  # PDF 导入产物，含 <!-- page:N --> 页锚点
    ├── 深读-<短名>.md       # 背景与动机 → 符号表 → 方法 → 实验 → 贡献 → 局限 → 证据与出处
    ├── 表格-<短名>.md
    ├── 思维导图-<短名>.md   # 四分支大纲（主形态，跨 harness 可读）
    ├── 导图-<短名>.md       # 同一导图的 Mermaid 可渲染形态
    ├── 难点-<短名>.md       # 难点与解答，每条带来源标记
    ├── 术语-<短名>.md       # 中英对照全量术语表（英文原词必须保留）
    └── 综述-<主题>.md       # 多篇时
```

两个索引层都可机械校验：单篇索引 `python paper-reading/scripts/check_paper_note.py "paper-notes/<短名>/README.md" --mode note`（首行标记 `<!-- paper-reading: note-index -->`，`--mode auto` 也能自动认出），合集层 `--mode index`（首行标记 `<!-- paper-reading: collection-index -->`）。

参考实例：`paper-notes/MFAA/`（对一篇 TIFS 2025 对抗攻击论文的真实产出，其中五件同时作为 `paper-reading/sample/` 的回归正样本），以及 `paper-notes/README.md`（同一篇论文的库索引，可直接 `python paper-reading/scripts/check_paper_note.py paper-notes/README.md --mode index` 校验）。

## 安装

三个平台都遵循 `<skill名>/SKILL.md` 目录 bundle 格式，把目标 skill 文件夹整个放进对应扫描目录即可，无需编译安装。

### 最省事：直接让 harness 自己装（自然语言）

**三个 harness 都能听懂"帮我装这个 skill"，不用手敲 `cp`。** 把下面这段话原样丢给 DSH / Claude Code / Codex 就行：

```text
安装 https://github.com/Shen-An/learn-skill 里的 paper-reading 与 learning-wiki 两个 skill：
clone 仓库 → 把两个 skill 目录整个拷进你本机的 skill 扫描目录 → 跑各自 evals/run_evals.py 确认门禁全过 → 报告装到了哪里、版本号是多少。
```

短一点的说法同样有效：「装 learn-skill 这个仓库里的 skill」「安装 Shen-An/learn-skill 的 paper-reading」。它会自己找到该落哪个目录——DSH `~/.agents/skills/`、Claude Code `~/.claude/skills/`、Codex `~/.codex/skills/`——装完再跑一遍门禁确认装上去的是好的。**Codex 不认斜杠命令**，这一步全程自然语言；DSH 与 Claude Code 也可以直接说人话，不必写成 `/` 命令。

想钉版本就说清 tag（「装 v1.7.1 那一版」→ `git clone --branch v1.7.1`）；网络受限、或你想先看它做什么再落盘，就退到下面两条路。

### 一条命令同步：`install.ps1`

```powershell
pwsh install.ps1                    # 两个 skill 同步到三个平台根目录
pwsh install.ps1 -DryRun            # 只看会做什么，不写盘
pwsh install.ps1 -Only paper-reading
pwsh install.ps1 -Roots "$HOME\.agents\skills"
```

脚本自动发现仓库里所有含 `SKILL.md` 的子目录，对每个 (skill × 根目录) 执行：**已是同版本则跳过**（顺手清掉副本里的 `__pycache__` 残留）；否则 **旧版改名保全 → 拷新版 → 逐文件 SHA-256 比对 → 跑该 skill 的回归门禁 → 通过才删旧版，不通过自动回滚**。退出码 0（全成功）/ 1（有失败）。安装副本一律不含本地证据账本 `feedback/ledger.jsonl`（该文件由运行时自建）。默认根目录为 `~/.agents/skills`、`~/.claude/skills`、`~/.codex/skills`，可用 `-Roots` 覆盖；`-SkipGate` 跳过门禁（不推荐）、`-KeepBackup` 保留被替换的旧版目录。

### 手动安装：三个 harness 各自的装法

差异只在**入口**与**能力**，产出契约完全一致（同一份 `SKILL.md`）：

| 维度 | DSH | Claude Code | Codex |
|------|-----|-------------|-------|
| 用户级扫描目录 | `~/.agents/skills/` | `~/.claude/skills/` | `~/.codex/skills/` |
| 项目级扫描目录 | `<项目>/.agents/skills/` | `<项目>/.claude/skills/` | 见官方文档 |
| 触发方式 | `/paper-reading` 或自然语言 | `/paper-reading` 或自然语言 | **自然语言**（不认斜杠命令） |
| 读 PDF | `read_document`（可 `offset`/`limit` 分页） | 内置 PDF 读入 | 内置读取，不可用时走脚本 |
| 看 Mermaid 导图 | 只按代码块显示（无渲染器） | 取决于终端/编辑器 | 取决于渲染器 |
| 跑校验器 | `python paper-reading/scripts/check_paper_note.py <文件> --mode auto` | 同左 | 同左 |

**DSH**——用户级热发现，装完立刻可用，不用重启：

```powershell
# 用户级：所有项目可用
Copy-Item learning-wiki,paper-reading "$HOME\.agents\skills\" -Recurse -Force
# 项目级：随仓库共享给同项目的人
Copy-Item learning-wiki,paper-reading .\.agents\skills\ -Recurse -Force
```

```bash
# macOS / Linux 等价写法
cp -r learning-wiki paper-reading ~/.agents/skills/
cp -r learning-wiki paper-reading <项目>/.agents/skills/
```

**Claude Code**——个人级所有项目可用，装完重开会话让它重新扫描：

```bash
cp -r learning-wiki paper-reading ~/.claude/skills/
# 项目级：可提交进仓库共享给团队
cp -r learning-wiki paper-reading <项目>/.claude/skills/
```

**Codex**——全局目录，触发靠自然语言（不认斜杠命令）：

```bash
cp -r learning-wiki paper-reading ~/.codex/skills/
# 项目级与更多细节见官方文档：https://learn.chatgpt.com/docs/build-skills
```

这三个根目录就是 `install.ps1` 的默认值，要改位置用 `-Roots`。装完验一下：在对应 harness 里说一句"讲一下这篇论文"，看它是否照 `SKILL.md` 的 Step 1 先落 `_source/`、再按模式成文，最后跑一次校验器。

## 使用

在任意学习或读论文的对话里（哪怕对话已经进行了很久）：

```
/learning-wiki     # 总结这次学习，做成学习 wiki
/paper-reading     # 讲一下这篇论文 / 导入这个 PDF 并精读 / 按模板填表 / 生成思维导图（含可渲染 Mermaid）/ 这篇论文有什么难点 / 写文献综述
```

可选指定：输出路径（默认 `./learning-<主题>/` 与 `./paper-notes/<短名>/`）、只要某一模式、增量更新已有目录。

## 把论文给它

**PDF 直接拖进对话就行**（或给出工作区路径、DOI/arXiv 链接、官方摘要、他人总结、代码仓库），再说一句你要什么。harness 自己会把文档当文档读、长文分页读完，并把正文落成带页锚点的 `_source/<论文名>.md`——笔记里的 `[原文 p.12]` 因此能直接翻页核对。

只有当 harness 没有文档读取能力、或你想把 PDF 固化成可 grep / 可 diff 的文本时，才需要回退脚本：

```bash
python paper-reading/scripts/pdf_extract.py 论文.pdf --out paper-notes/<短名>/_source/
```

用法、产出格式、退出码与常见故障见 `paper-reading/references/input-intake.md`（按需加载，不占 README）。

### 一次完整交付长什么样（以 PDF 为例）

```
你：（把 PDF 拖进来）这篇帮我精读，顺便出难点文档
它：① 读 PDF（harness 文档读取；必要时才用 pdf_extract.py 落盘）→ _source/<论文名>.md（带 <!-- page:N -->）
    ② 深读-<短名>.md    背景与动机 → 符号表 → 方法 → 实验 → 贡献 → 局限 → 证据与出处（含 [原文 p.N]）
    ③ 表格-<短名>.md    9 维表
    ④ 思维导图-<短名>.md + 导图-<短名>.md（Mermaid 形态，Obsidian/GitHub 可出图）
    ⑤ 难点-<短名>.md    难点与解答，每条解答带来源标记
    ⑥ 术语-<短名>.md    中英对照全量术语（英文列保留原词 + 英文原句摘录，保住英文能力）
    ⑦ README.md        单篇索引：全量文件登记 + 证据强度提示 + 待核入口（--mode note 可校验）
    ⑧ paper-notes/README.md  库索引登记：主题清单 + 术语速查 + 跨论文对比 + 未解决问题 + 证据强度总览
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
    ├── SKILL.md                # 主指令：八种产出（含笔记库索引与中英术语表）+ 证据分层纪律 + 可渲染优先 + Step 1–7
    ├── CHANGELOG.md
    ├── scripts/
    │   ├── check_paper_note.py # 机械校验：结构/公式定界符与独占行/表格/引用范围/模式混装/导图渲染/难点字段/单篇索引/库索引结构/术语表结构，九模式各一套
    │   └── pdf_extract.py      # PDF 导入：逐页提取 + `<!-- page:N -->` 页锚点 + 扫描页标记
    ├── evals/
    │   ├── run_evals.py        # 回归门禁：good/warn/bad 样本 + sample/ 真实产出 + PDF 抽取器契约 + 合集索引 + 术语表 + 出处标记口径 + 单篇索引
    │   ├── good-sample/        # 正样本 fixture（六种单篇模式各一；库索引正样本在 index-cases/，术语表在 terms-cases/，单篇索引在 note-cases/）
    │   ├── warn-sample/        # WARN 类 fixture（应退出 0 但命中指定 WARN）
    │   ├── bad-sample/         # 负样本 fixture（故意违规，勿修）
    │   ├── pdf-cases/          # PDF 抽取器 fixture（3 页样例 / 空白页 / 加密 / 假 PDF）+ make_fixtures.py
    │   ├── index-cases/        # 笔记库索引 fixture（正/警/负样本 + 漏登记反向检查）
    │   ├── terms-cases/        # 专业术语表 fixture（正/警/负样本：英文列缺英文、出处非法、重复登记等）
    │   ├── faq-cases/          # 出处标记口径 fixture（带页码 [原文 p.N] / 定位标签 [实验] 必须放行，契约外标记必须拦）
    │   └── note-cases/         # 单篇索引 fixture（正/警/负样本：漏登记、死链、缺模式标签等）
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
        ├── terms-template.md      # 模式 H：中英对照全量术语表骨架（六节 + 六列 + 全量扫描法 + 11 个检查码）
        ├── note-index-template.md # 模式 note：单篇索引骨架（标记行 + 全量文件登记 + 证据强度四类 + 待核入口 + 11 个检查码）
        ├── formula-style.md       # 公式：Markdown 数学定界符 / 记法约定 / 渲染自检
        ├── input-intake.md        # 输入接入：PDF/摘要/DOI/二手 的可讲深度与页锚点规范
        ├── grounding-rules.md     # 出处标记表（六类来源 + [实验] 定位标签 + 数字引用）/ 冲突处理 / 可讲深度判定
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

## 自迭代改进（RSI）与 PR 流程

### 为什么它需要一套流程

skill 的规则不能"想到就改"：一次随手的措辞变更可能把一条规则悄悄改坏，而且事后没人知道当初为什么改。所以两个 skill 都带一套 **RSI 协议**（验证提供信号 → 迭代消费信号）：**改动只由证据驱动**——先记账、攒够证据、跑门禁、人工确认，才允许动规则。

证据账本 `feedback/ledger.jsonl`（只追加，不修改不删除）：

| 字段 | 取值 |
|------|------|
| `source` | `check_paper_note`（校验器报的 ERROR，或被判定"本应在生成时避免"的 WARN）、`rubric`（人工过质检清单导致的返工）、`user_rework`（用户要求返工、修正或表达不满）、`harness`（运行环境类信号：沙箱/权限限制、工具能力缺口、代理执行失败、门禁跑不起来） |
| `mode` | `deep` / `table` / `mindmap` / `mmd` / `faq` / `review` / `index` / `note` / `terms` / `skill`；PDF 导入与抽取器相关记 `pdf`（除 `skill` 外与 `check_paper_note.py --mode` 取值一致，勿造新词）。`skill` = 改动横跨多个模式或不落在单一产出上（改枚举、改协议、改模板骨架、改工作流步骤） |
| `action` | `fix_output`（只修本次产出）或 `rule_change`（要改 skill 本身） |

**触发条件**（满足其一才进入迭代）：① 用户明确要求"复盘 / 迭代这个 skill"；② 自上次版本 bump 以来 ledger 新增 ≥ 5 条；③ 出现违反"宪法区"的记录（证据分层、冲突数字必须并列、不编造、局限单列、无寒暄）→ 立即触发，不等攒数。

**六步流程**：聚类根因（缺规则 / 规则表述模糊 / 校验器查不出 / 模板诱导了坏产出）→ **最小 diff**（一轮最多改一条规则或一个检查项，并注明依据的 ledger 记录）→ 门禁 → 人工确认（**AI 不得自行升版本**）→ 升版本 + 写 `CHANGELOG.md` + 追加一条 `action:"rule_change"` 闭环 → 机械 / 人工同步（能机械化的移进校验器，机器查不了的人工项留在 rubric）。

门禁怎么选：动了 `scripts/` 或 fixture → **必跑** `python evals/run_evals.py`，全绿才继续，且新增检查项必须同步在 `evals/bad-sample/` 埋对应违规、在 `run_evals.py` 加断言；只动 `SKILL.md` 或模板文字 → **用最近一篇真实论文重跑对应模式**，对比产出有没有回归。

提案模板（交给维护者确认时照这个填）：

```text
问题:     ledger 09-20、09-27 两条同类：二手来源数字未标注即写入"主要发现"
根因:     deep-read-template 的"主要发现"未强制来源标记，且无坏例子对照
提案:     deep-read-template.md「四、实验验证」补一句"每个数字后缀来源标记"（+1 行 diff）
依据:     2026-09-20T21:14 / 2026-09-27T10:02
门禁:     run_evals 全 PASS；重跑 09-27 那篇论文的 deep 产出对比无回归
```

协议全文见 `paper-reading/references/self-iteration.md` 与 `learning-wiki/references/self-iteration.md`，含宪法区（只可收紧、不可放松）与防膨胀规则（不可妥协的规则 ≤ 10 条；连续两版在 ledger 中 0 命中的规则列为删除候选；优先改写原规则而不是追加例外条款）。

### 提 PR 的流程

```bash
git clone https://github.com/Shen-An/learn-skill.git
cd learn-skill
git switch -c fix/paper-reading-<短描述>

# 改 skill：SKILL.md / references/ / scripts/ / evals/
python learning-wiki/evals/run_evals.py      # 动了 scripts/ 或 fixture：必跑，必须全绿
python paper-reading/evals/run_evals.py
pwsh install.ps1 -DryRun                     # 确认安装面没被改坏（只看会做什么，不写盘）

git add -A
git commit -m "fix(paper-reading): <一句话说明改了哪条规则、依据哪条 ledger>"
git push -u origin fix/paper-reading-<短描述>
gh pr create --fill --base main
```

PR 描述里带齐四样东西（缺一样通常会被打回）：

1. **依据**：对应的 ledger 记录（`ts` + 第几条）或 issue 编号——没有证据的"我觉得应该这样"不合并
2. **门禁输出**：动了 `scripts/` 或 fixture 时，贴断言数变化（如 `gate 298 → 312 assertions`）与全绿结果
3. **真实产出对比**：只动 `SKILL.md` / 模板文字时，贴"最近一篇真实论文重跑该模式"的前后差异
4. **新增检查项**：说明在 `evals/bad-sample/` 埋了什么违规、`run_evals.py` 加了哪条断言去抓它（新检查项没有负样本等于没测）

硬性约定：**一轮 PR 只改一条规则或一个检查项**；不新增超过 10 条的"不可妥协的规则"；优先改写原规则，而不是追加例外条款。合并后由维护者升版本、写 `CHANGELOG.md`、打 tag 并发 release。

### 发版

- 版本语义：新增 / 修改规则 → minor；纯措辞微调 → patch；宪法区收紧 → minor
- 顺序：`CHANGELOG.md` 先写清"来自用户要求 / 依据 ledger 第 N 条" → 打 tag `vX.Y.Z` → 发 release（release notes 直接用 CHANGELOG 对应段落）
- 一次发版对三个 harness 同时生效：改完记得 `pwsh install.ps1` 把新版同步到你本机的三个 skill 根目录

## 贡献 / 反馈

Issue & PR 欢迎。最短路径：

```bash
python learning-wiki/evals/run_evals.py     # 回归门禁，必须全绿
python paper-reading/evals/run_evals.py
pwsh install.ps1                           # 同步到三个平台（同样会跑门禁 + 哈希校验）
```

提交前请在三个平台里至少实测一个（真实对话 / 论文 → 产出 → 对照对应 `quality-rubric.md` 自检）。改规则要走的流程、证据格式与 PR 要求见上一节；协议原文见 `paper-reading/references/self-iteration.md` 与 `learning-wiki/references/self-iteration.md`。
