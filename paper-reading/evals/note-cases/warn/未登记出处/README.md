<!-- paper-reading: note-index -->

# DPO 论文笔记索引

论文：Direct Preference Optimization: Your Language Model is Secretly a Reward Model（NeurIPS 2023，arXiv:2305.18290，Rafael Rafailov 等）

一句话结论：证明带 KL 约束的 RLHF 最优解可以改写成对策略自身的闭式偏好损失，于是跳过"先训奖励模型再跑 PPO"两步、直接在偏好数据上做分类式训练，代价是失去了显式奖励模型这一可解释中间层、且对偏好数据的分布与质量更敏感。

## 文件

- [深读-DPO.md](./深读-DPO.md)：精读讲解（模式 A）——RLHF 目标推导、隐式奖励的形式、与 PPO 的对比实验
- [术语-DPO.md](./术语-DPO.md)：中英对照全量专业术语表（模式 H）

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；式 (7) 的隐式奖励改写 [原文 p.4]。
- 低置信（我的推断）：把"训练更稳"归因到去掉了 PPO 的采样环节。

## 待核入口

- 正文：arXiv:2305.18290
- 对照工作：PPO 与 SLiC-HF 的超参敏感性
