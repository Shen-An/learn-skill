<!-- paper-reading: note-index -->

# GPT-3 论文笔记索引

论文：Language Models are Few-Shot Learners（NeurIPS 2020，arXiv:2005.14165，Tom B. Brown 等）

一句话结论：把模型放大到 1750 亿参数并全部改用上下文示例代替梯度更新，证明"少样本学习"可以随规模涌现：许多任务上不给一个梯度也能接近微调基线，代价是推理成本随参数线性上升、上下文窗口限制了可用示例数，且论文自述这一能力在部分任务上仍远低于人类。

## 文件

- [深读-GPT3.md](./深读-GPT3.md)：精读讲解（模式 A）——三种设定（zero/one/few-shot）、数据污染处理、任务清单与局限
- [术语-GPT3.md](./术语-GPT3.md)：中英对照全量专业术语表（模式 H）

## 待核入口

- 正文：arXiv:2005.14165
- 对照工作：T5 与 SOTA 微调基线在 SuperGLUE 上的差值
