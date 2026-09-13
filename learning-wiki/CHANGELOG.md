# Changelog

版本号规则与修改流程见 `references/self-iteration.md`：任何版本变更必须有 ledger 证据 + `python evals/run_evals.py` 门禁通过 + 人工确认。

## 1.2.0 — 2026-09-13

闭环升级：验证→自迭代从口号变成可执行机制。依据：本轮 skill 复盘对话。

- **新增 RSI 闭环**：`references/self-iteration.md`（触发条件 / 最小 diff / 宪法区 / 防膨胀）；`feedback/ledger.example.jsonl`（证据账本格式，Step 5 命中即追加）
- **新增回归门禁** `evals/`：`run_evals.py` 断言正样本 `sample-wiki` 0 ERROR / 0 WARN、负样本 `bad-wiki` 的 8 类埋错逐类被抓到；skill 改动的准入条件
- **校验器扩展**：链接可达性由"仅 README"（E2）推广到全文件（E5）；新增 W3 悬空引用检查（`见 NN §小节` 指向的章节文件与小节标题必须真实存在）
- **fixture 真实化**：`sample-wiki/` 从单文件占位重写为 3 章真实 wiki，且真正通过校验器（旧版声称"已通过机械校验"实为虚假声明——它自己就是第一条被抓到的教训）
- **rubric 机械化**：链接可达、悬空引用两条移入脚本；quality-rubric 只保留机器查不了的人工项，并标注对应检查码

## ≤ 1.1.0

无 changelog（本文件自 1.2.0 起设立；后续每次迭代必须在此追加条目）。
