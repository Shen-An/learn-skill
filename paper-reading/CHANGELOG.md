# Changelog

版本号规则与修改流程见 `references/self-iteration.md`：任何版本变更必须有 ledger 证据 + `python evals/run_evals.py` 门禁通过 + 人工确认。

## 1.2.0 — 2026-09-13

两项来自用户直接要求的迭代（触发条件 1）。依据见 `feedback/ledger.jsonl` 第 3 条记录。

- **思维导图新增可渲染形态**：保留 `思维导图-<短名>.md`（文本大纲，跨 harness 可读、可 grep）作为主形态，**新增** `导图-<短名>.md`（Mermaid mindmap，单一围栏块、唯一 `root((短名))` 根、四分支顺序固定、层级 ≤4、节点文本禁用 ASCII `( ) [ ] { } , ; : %`）作为渲染形态；两者成套产出，互不内嵌。`references/mindmap-template.md` 补"Mermaid 形态 + 渲染能力对照"段
- **如实说明渲染能力**：查证 DSH Web GUI 不含 mermaid 渲染器（`resources/app` 全库只有 shiki 的 `mermaid` 语法高亮定义），因此 SKILL.md 规则 2 改为"可渲染优先，且只承诺渲染器做得到的"，Delivery 纪律要求明确告知读者：Mermaid 在 Obsidian / GitHub 能出图，在 DSH Web GUI 只按代码块显示
- **新增模式 F：难点与解答**（`难点-<短名>.md`）：新增 `references/faq-template.md`（五字段结构 + 难点五个来源分类 + 反编造约束）；机械校验新增 `faq` 模式
- **校验器新增两个模式**（`mmd` 与 `faq`，共 14 个新 CODE）：`E-MMD-H1/FENCE/KEYWORD/ROOT/BRANCH/DEPTH/SYNTAX`、`W-MMD-BLOAT/TEXT`、`E-FAQ-H1/SEC/FIELD/CITE/DUP`、`W-FAQ-MISCONCEPT/SELFCHECK/SHORT/TONE`；`--mode auto` 按文件名识别（`思维导图` 优先于 `导图`）
- **门禁扩容**：新增 `导图-示例.md`、`难点-示例.md` 两个正样本；`sample/` 真实产出增加 `导图-MFAA.md` 与 `难点-MFAA.md`（两者都过 0 ERROR / 0 WARN）
- **`quality-rubric.md` 扩到 31 条**，新增 G 节"可渲染导图与难点文档"

## 1.1.0 — 2026-09-13

三项来自用户直接要求的迭代（触发条件 1：用户明确要求迭代本 skill）。依据见 `feedback/ledger.jsonl` 首条记录。

- **模式彻底分离**：新增硬约束"思维导图与填表不得内嵌进讲解文档、必须独立成文件与独立成块呈现"（SKILL.md 规则 6 + Step 5 交付纪律）；`mindmap-template.md`、`table-template.md`、`deep-read-template.md` 各自补"交付纪律/模式分离"段；校验器新增 `E-DEEP-MIX`（深读文档内出现 ≥2 个思维导图固定分支名即报错）。动机：原交付把三件套塞进同一条长回复，读者要在讲解末尾再读一遍同样的内容，反而不好看
- **公式规范化为可渲染的 Markdown 数学**：新增 `references/formula-style.md`（定界符、记法约定表、必备配套、自检清单）；行间公式统一改为 `$$` **独占一行**的三行块；范数用 `\lVert ... \rVert`、算子用 `\operatorname{...}`、自适应括号用 `\left(...\right)`；校验器新增 `E-DEEP-MATH-LINE`（`$$` 与公式同行即报错）。动机：原写法 `$$ 公式 $$` 同行，在部分渲染器下不显示为数学；`\|` 还会被表格解析误当列分隔符（本次真实产出里已抓到一例）
- **PDF 导入通道**：新增 `scripts/pdf_extract.py`（`pypdf`/`PyPDF2` 回退、`--pages` 区间、页锚点 `<!-- page:N -->`、扫描页标记、汇总表、退出码 0/2/3/4）；新增 `references/input-intake.md`（六类输入的接入路径与可讲深度、PDF 导入固定流程、**来源类型声明**枚举）；SKILL.md Step 1 改为"材料接入与定位"。校验器新增 `W-DEEP-SRC-KIND`（缺来源类型声明）与 `W-DEEP-PAGE`（声明 PDF 全文却无页码锚点）
- **证据标记升级**：`[原文]` 细化为 `[原文 p.N]`，新增 `[OCR]`；`quality-rubric.md` 扩到 25 条并新增 F 节"格式可渲染"
- **门禁扩容**：`evals/` 新增 `warn-sample/` 用例（WARN 类 fixture 断言退出码 0 且命中目标 WARN、不得含 ERROR），bad-sample 扩充到覆盖新增 ERROR 码

## 1.0.0 — 2026-09-13

首版。由用户既有提示词资产（逐篇填表 / 汇总综述 / 思维导图 / 论文精读讲解）固化而来，并把"论文精读"从一次性提示词升级为可校验、可迭代的 skill。

- **四种模式固化为一个 skill**：A 精读讲解（`深读-<短名>.md`）、B 逐篇填表（`表格-<短名>.md`）、C 思维导图（`思维导图-<短名>.md`）、D 汇总综述（`综述-<主题>.md`）；模式选择规则与产物路径写进 SKILL.md，避免每次都从零拼提示词
- **新增证据分层纪律**：`references/grounding-rules.md` 定义 `[原文]`/`[代码]`/`[摘要]`/`[二手]`/`[推断]` 五级标记、冲突处理规则、可讲深度判定表。这是首版最重要的升级：原提示词模板没有区分"原文结论"与"二手转述"，AI 总结里的数字会被直接当成论文结论
- **公式规范**：行内 `$...$`、行间 `$$...$$`，符号首现即释，公式块 ≥3 个时必备符号与记号表
- **思维导图保留原四分支契约**：`研究背景与目标`/`研究方法`/`关键研究结果`/`研究结论与意义`，一级分支不多不少，禁止代码围栏
- **填表保留原"只输出表格"契约**：表外不得有任何文字，每格 1–3 句，缺信息填"未提及"
- **新增机械校验器** `scripts/check_paper_note.py`：四模式各自的结构/公式/表格/引用检查（ERROR 必修，WARN 人工判断）
- **新增回归门禁** `evals/run_evals.py`：正样本 0 ERROR / 0 WARN，负样本埋错逐类被抓；`sample/` 存放真实产出作为端到端正样本
- **新增 RSI 闭环**：`feedback/ledger.example.jsonl`（证据账本格式）+ `references/self-iteration.md`（触发条件 / 最小 diff / 宪法区 / 防膨胀）
