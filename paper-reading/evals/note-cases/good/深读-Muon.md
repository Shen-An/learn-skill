# Muon is Scalable for LLM Training 精读讲解

> fixture 桩文件：note-cases/good 用例只校验同目录的 `README.md`（单篇索引），本文件与其余产出文件只用于让链接指向真实文件。

背景：Muon 此前只在 CIFAR-10 级的小模型上报告过加速；本文把它接到 3B/16B MoE 的预训练管线，并补上"一致性 RMS 缩放"这一步，使更新尺度与 AdamW 可比 [原文 p.3]。
