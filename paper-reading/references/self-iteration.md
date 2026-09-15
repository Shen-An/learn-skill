# 自迭代协议（RSI）

原则：**验证提供信号，迭代消费信号。** 本 skill 只在有账本证据时改规则，改动必须过回归门禁并经人工确认。
生成笔记的流程（SKILL.md Step 1–5）中**绝不**执行本文档的任何修改动作——迭代只发生在离线复盘时。

与 `learning-wiki` 共用同一套协议形态：本文件是 `paper-reading` 的实例化版本，规则与账本独立。

## 证据层：ledger

- 路径：`feedback/ledger.jsonl`（首写时创建；字段与格式见 `feedback/ledger.example.jsonl`）
- 谁写：Step 5 交付后由 skill 自己追加，三种情形必记：
  1. `check_paper_note.py` 报出 ERROR，或 WARN 被人工判定为"本应在生成时避免"
  2. 人工过 `quality-rubric.md` 时任何一条不过导致返工
  3. 用户要求返工、修正或表达不满（含"太浅了""数字不对""没有讲清 XX"）
- `source` 取 `check_paper_note` / `rubric` / `user_rework` / `harness`；`action` 取 `fix_output`（修本次产出）或 `rule_change`（改 skill）；`mode` 取 `deep` / `table` / `mindmap` / `mmd` / `faq` / `review` / `index` / `note` / `terms` / `skill`，PDF 导入或抽取器相关的改动记 `pdf`（除 `skill` 外与 `check_paper_note.py --mode` 的取值一致，勿再造新词）
- 三个易混取值的判据（避免再次出现"没地方填就就近放一个"）：
  - `source=harness`：信号来自运行环境而非产出本身（沙箱/权限限制、工具能力缺口、代理执行失败、门禁跑不起来这类），**不记**为 `rubric`；
  - `mode=skill`：改动横跨多个模式或不落在任何单一产出上（改枚举、改协议、改模板骨架、改工作流步骤）；
  - `mode=note`：单篇索引 `paper-notes/<短名>/README.md`（模式 note）；`mode=index` 仅指合集层 `paper-notes/README.md`（模式 G）。
- **只追加，不修改不删除**——历史证据是迭代的地基，写错了就追加一条更正

## 触发条件（满足其一才进入迭代流程）

1. 用户明确要求"复盘这个 skill" / "迭代 skill"
2. 自上次版本号 bump 以来，ledger 新增 ≥ 5 条记录
3. 出现任何一条违反宪法区的记录（见下）→ 立即触发，不等攒数

## 迭代流程（离线批处理）

1. **聚类**：通读上次版本以来的 ledger 记录，归入四类根因——缺规则 / 规则表述模糊 / 校验器查不出 / 模板诱导了坏产出
2. **最小 diff**：只挑收益最大的一件事；一轮最多改一条规则或一个检查项。新规则必须注明依据的 ledger 记录（`ts` + 序号）
3. **门禁**：
   - 动了 `scripts/` 或 fixture → 必跑 `python evals/run_evals.py`，全部断言 PASS 才可继续；给 `check_paper_note.py` 新增检查项时，必须同步在 `evals/bad-sample/` 埋对应违规、在 `run_evals.py` 加断言
   - 只动 SKILL.md / 模板文字 → 用最近一次真实论文重跑一次对应模式，对比产出是否有回归
4. **人工确认**：把 diff 提案（见下方模板）交给用户，得到 yes 才落盘。AI 不得自行升版本，**也不得自行推送、打 tag 或发 release**——这三个对外动作与升版本同级，必须先拿到人工 yes；事后补一句"我已经推了"不算确认（ledger 第 19 条就是这么来的）
5. **升版本**：新增/修改规则 → minor；措辞微调 → patch；宪法区收紧 → minor。写 `CHANGELOG.md`，并在 ledger 追加一条 `action:"rule_change"` 闭环
6. **机械/人工同步**：rubric 条目若被判定可机械化 → 移入 `check_paper_note.py`，rubric 删除对应条目并注明"脚本 X 号已覆盖"；反之脚本查不了的人工项别硬塞进脚本
7. **发版收尾**（先按第 4 步拿到 yes）：`pwsh install.ps1` 同步三个 harness 并确认"一致" → 提交并推送 → 打**附注** tag `vX.Y.Z` 并推送 → 发 GitHub Release（notes 直接取 `CHANGELOG.md` 对应段落；一次覆盖多个版本时，开头先写明范围，如 v1.5.0 合发 1.3.0–1.5.0）。**只推 commit、不打 tag、不发 Release 等于没发版**——外部读者按 tag 装版本，仓库里 v1.6.0 与 v1.7.0 就是这样裸着 commit 的（ledger 第 19 条）

## 宪法区（不可放松、不可删除，只可收紧）

- 证据分层：低置信来源不得单独支撑核心结论（`grounding-rules.md`）
- 冲突数字必须并列呈现，禁止调和
- 论文没说的内容一律"未提及"，严禁用领域常识补写成论文主张
- "局限性与未来工作"必须单列且论文自述与独立判断分开
- 输出无寒暄、无自述（SKILL.md 规则 9）

## 防膨胀规则

- "不可妥协的规则"总数 ≤ 10 条：新增第 11 条时，必须先合并或删除一条旧的
- 任何规则连续两个版本在 ledger 中 0 命中 → 下轮复盘列为删除候选
- 优先改写原规则，而不是追加"例外条款"
- 迭代是**收紧或替换**，不是沉积：CHANGELOG 里看不懂的规则堆，删

## diff 提案模板

```text
问题:     ledger 09-20、09-27 两条同类：二手来源数字未标注即写入"主要发现"
根因:     deep-read-template 的"主要发现"未强制来源标记，且无坏例子对照
提案:     deep-read-template.md「四、实验验证」补一句"每个数字后缀来源标记"（+1 行 diff）
依据:     2026-09-20T21:14 / 2026-09-27T10:02
门禁:     run_evals 全 PASS；重跑 09-27 那篇论文的 deep 产出对比无回归
```
