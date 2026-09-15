# FlashAttention 精读讲解

> fixture 桩文件：warn/缺待核入口 只校验同目录的 `README.md`，本文件只用于让链接指向真实文件。

IO 复杂度：标准注意力需要 O(N²) 的 HBM 读写，分块后降到 O(N²d²M⁻¹) [原文 p.3]。
