<!-- paper-reading: note-index -->

# InstructGPT 论文笔记索引

论文：Training language models to follow instructions with human feedback（NeurIPS 2022，arXiv:2203.02155，Long Ouyang 等）

一句话结论：把"有用、诚实、无害"的目标改写成三步流水线——人工示范做监督微调、成对偏好训奖励模型、再用 PPO 按奖励模型优化，让 1.3B 的 InstructGPT 在人工评测里比 175B 的 GPT-3 更受偏好，代价是引入了奖励模型被过优化的风险，且标注成本与对齐税（部分 NLP 任务指标下降）都需要单独承担。

## 文件

- [深读-InstructGPT.md](./深读-InstructGPT.md)：精读讲解（模式 A）——SFT/RM/PPO 三段、对齐税、公开数据集与标注流程
- [难点-InstructGPT.md](./难点-InstructGPT.md)：难点与解答（模式 F）

## 证据强度提示

本节只写了两段说明文字，**刻意没有**用「- 」列表项，用来触发 `E-NOTE-EVID`。

高置信（原文可核）：论文身份与 arXiv 编号；1.3B 优于 175B GPT-3 的人工偏好比例。
低置信（我的推断）：把"对齐税"主要归因到偏好数据分布与预训练分布不一致。

## 待核入口

- 正文：arXiv:2203.02155
- 对照工作：Anthropic 的 HH-RLHF 与 Constitutional AI
