<!-- paper-reading:note-index -->

# CoT 论文笔记索引

论文：Chain-of-Thought Prompting Elicits Reasoning in Large Language Models（NeurIPS 2022，arXiv:2201.11903，Jason Wei 等）

一句话结论：把"给出中间推理步骤"从训练目标改成提示词写法，在 540B 模型上让 GSM8K 的解题率从 17.9% 跳到 56.9%，而小模型上这个收益几乎消失，说明它买的是"已有能力被写出来"而不是新能力，代价是对模型规模与提示词措辞高度敏感。

## 文件

- [深读-CoT.md](./深读-CoT.md)：精读讲解（模式 A）——涌现现象、八类推理任务的实验设计、消融
- [难点-CoT.md](./难点-CoT.md)：难点与解答（模式 F）——为什么小模型反而变差

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；GSM8K 17.9%→56.9% 的表格数字 [原文 p.6]。
- 低置信（我的推断）：把"措辞敏感"解释成提示词与预训练分布的对齐程度。

## 待核入口

- 正文：arXiv:2201.11903
- 对照工作：Zero-shot CoT（"Let's think step by step"）
