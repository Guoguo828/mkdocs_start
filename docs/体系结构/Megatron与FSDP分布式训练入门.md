# Megatron 与 FSDP 分布式训练入门

## 一、先说结论：这两个东西分别是什么

### 1. FSDP 是什么
FSDP 的全称是 **Fully Sharded Data Parallel**。它是 PyTorch 提供的一种**分布式数据并行训练方案**。

最核心的一句话：

> 普通数据并行是“每张卡各放一整份模型”，FSDP 是“每张卡只放模型的一部分，需要算的时候再把需要的参数临时聚合起来”。

所以 FSDP 的主要目标不是“改变模型怎么计算”，而是：

1. **降低单卡显存压力**
2. **让更大的模型能训起来**
3. **在多卡上把参数、梯度、优化器状态分片保存**

它很像 DeepSpeed ZeRO-3 的思路。PyTorch 官方文档也明确说明，FSDP 是一种对参数进行分片的封装，思想和 ZeRO Stage 3 接近。

### 2. Megatron 是什么
现在大家说 “Megatron”，通常指 NVIDIA 这一套大模型训练栈，核心是 **Megatron-Core / Megatron-LM**。

它不是单一算法，而是一整套**大模型并行训练方案**，重点解决的是：

1. **模型太大，单卡放不下**
2. **单纯靠数据并行不够，需要把一个模型本身拆到多张卡上算**
3. **需要把 Tensor Parallel、Pipeline Parallel、Context Parallel、Expert Parallel 这些并行方式组合起来**

一句话理解：

> FSDP 更偏“把模型状态切开保存”，Megatron 更偏“把模型计算本身切开执行”。

当然，现实里这两者经常是**组合使用**的，不是二选一。

---

## 二、为什么会需要这些分布式训练技术

训练大模型时，瓶颈通常来自两个方面：

### 1. 显存不够
训练时显存里不只要放参数，还要放：

1. 参数（Parameters）
2. 梯度（Gradients）
3. 优化器状态（Optimizer States，例如 Adam 的一阶、二阶动量）
4. 激活值（Activations）

很多时候真正吃显存的，不只是参数本身，而是这几类东西加起来。

### 2. 算力和吞吐不够
即使显存够，一张卡训练几十亿、上百亿参数模型也会非常慢。于是就要想办法：

1. 把数据拆开给多张卡
2. 把模型拆开给多张卡
3. 把通信和计算尽量重叠

所以分布式训练本质上在解决两件事：

1. **内存扩展**
2. **计算扩展**

---

## 三、先建立最重要的总框架：几种并行到底在并什么

### 1. 数据并行 Data Parallel, DP
每张 GPU 跑**同一个模型**，但处理**不同的数据批次**。

优点：

1. 思想最直观
2. 工程上最常见
3. 容易扩展吞吐

缺点：

1. 每张卡都要保存完整模型时，显存浪费大
2. 模型太大时根本放不下

普通 DDP（DistributedDataParallel）就是这一路。

### 2. 张量并行 Tensor Parallel, TP
把**同一层里的权重矩阵**拆到多张 GPU 上共同计算。

例如一个很大的线性层：

\[
Y = XW
\]

如果矩阵 \(W\) 太大，就可以按列或按行切到多张卡上。每张卡只算一部分，最后再拼接或汇总。

这就是 Megatron 最经典的并行方式之一。

### 3. 流水线并行 Pipeline Parallel, PP
把模型按**层**切成几段。

例如 24 层 Transformer：

1. GPU0 负责第 1 到 6 层
2. GPU1 负责第 7 到 12 层
3. GPU2 负责第 13 到 18 层
4. GPU3 负责第 19 到 24 层

数据像流水线一样一段一段往后传。

### 4. 序列/上下文并行 Sequence Parallel / Context Parallel
把长序列这一维拆开，让不同 GPU 处理不同 token 段，重点缓解**长上下文**下的激活和注意力显存压力。

### 5. 专家并行 Expert Parallel, EP
主要用于 MoE（Mixture of Experts）模型，把不同专家放在不同设备上。

---

## 四、FSDP 的原理：它到底做了什么

### 1. 和 DDP 的区别

#### DDP
每个进程/每张卡都有一份**完整模型副本**：

1. 前向各算各的
2. 反向各算各的
3. 最后用 `all-reduce` 同步梯度

所以 DDP 的特点是：

1. **实现简单**
2. **通信模式清晰**
3. **但模型状态是完整复制的**

#### FSDP
FSDP 会把这些状态按数据并行组切分：

1. 参数分片
2. 梯度分片
3. 优化器状态分片

也就是说，8 张卡训练时，不再是每张卡都各存一整份参数，而是每张卡只存其中 1/8 左右的分片。

### 2. FSDP 的执行过程
可以把 FSDP 理解成“**平时分片保存，计算前临时聚合，算完再拆回去**”。

一个简化版过程如下：

#### 前向传播前
每张卡原本只持有自己的参数分片。  
当某一层要计算时，FSDP 会通过 `all-gather` 把这一层完整参数临时凑出来。

#### 前向传播时
当前层拿到完整参数后，正常做前向计算。

#### 前向结束后
如果配置为完全分片，参数会再次分片回去，避免完整参数长期占显存。

#### 反向传播时
反向计算需要对应层参数，FSDP 会再次按需聚合。  
梯度算出来以后，会通过 `reduce-scatter` 之类的操作把梯度重新切分并分发。

#### 优化器更新时
每张卡只更新自己那部分参数对应的优化器状态和参数分片。

### 3. FSDP 为什么能省显存
因为在大多数时间里，每张卡只保留：

1. 自己负责的参数分片
2. 自己负责的梯度分片
3. 自己负责的优化器状态分片

完整参数只在少数计算时刻短暂出现。

### 4. FSDP 的代价是什么
省显存不是白来的，它用更多通信换显存：

1. 前向前要聚合参数
2. 反向时也要做额外通信
3. 如果切得太碎，通信开销可能很重
4. 工程上比 DDP 更复杂

所以 FSDP 的关键 trade-off 是：

> **用通信复杂度换内存容量。**

### 5. 一句话抓住 FSDP

> FSDP 属于数据并行，但它不是“复制整个模型”，而是“分片模型状态，只在需要时临时还原局部完整参数”。

---

## 五、Megatron 的原理：它在并行什么

Megatron 的核心思想不是只做一种并行，而是把 Transformer 训练里最重的部分拆开，让多张卡**共同完成一个模型的计算**。

### 1. Tensor Parallel：把层内矩阵切开
Transformer 里的大头计算基本都是矩阵乘法，比如：

1. Attention 的 QKV 投影
2. Attention 输出投影
3. MLP 的两层线性变换

Megatron 会把这些大矩阵按列或按行切到不同 GPU 上。

举个最常见的 MLP 直觉：

1. 第一层线性变换按列切开，各卡分别算一部分输出
2. 激活函数各自在本地做
3. 第二层线性变换按行切开
4. 中间穿插必要的 `all-reduce` / `all-gather`

这样单层参数和单层计算都被拆开了。

#### Tensor Parallel 的优点

1. 能处理单层参数非常大的模型
2. 对 Transformer 特别适合

#### Tensor Parallel 的问题

1. 层与层之间通信很频繁
2. 很依赖高速互联
3. TP 规模不是越大越好

### 2. Pipeline Parallel：把层段切开
Megatron 也支持把模型分成多个 stage。

不同于 TP 是“同一层多人一起算”，PP 是“不同层由不同人接力算”。

但流水线并行会带来一个经典问题：

> **pipeline bubble（流水线气泡）**

也就是某些 stage 会有空等时间。为减少 bubble，通常会把一个 batch 再拆成多个 **micro-batch**，让流水线更满。

### 3. Sequence Parallel：把激活沿序列维切开
Megatron 在 TP 基础上还会做 Sequence Parallel。它的核心收益是：

1. 让某些激活不必在每张 TP 卡上都完整复制
2. 缓解长序列训练时的显存压力

你可以把它理解成：

> 在已经做了张量并行以后，继续把“序列维上的中间结果”拆开存和算。

### 4. Context Parallel：应对超长上下文
当上下文长度很长时，注意力相关的激活和通信会非常重。Megatron 的 Context Parallel 进一步把上下文维度拆到多卡上，用来支持更长的序列。

### 5. Expert Parallel：给 MoE 用
如果模型不是稠密 Transformer，而是 MoE，那么不同 expert 可以分布到不同 GPU。路由器决定 token 去哪个 expert 算，这就是 Expert Parallel。

---

## 六、Megatron 和 FSDP 到底是什么关系

这两个东西经常一起出现，是因为它们解决的问题不一样：

### 1. FSDP 解决的是“模型状态怎么放”
重点是：

1. 参数怎么分片
2. 梯度怎么分片
3. 优化器状态怎么分片

### 2. Megatron 解决的是“模型计算怎么拆”
重点是：

1. 层内矩阵怎么拆
2. 模型层怎么分段
3. 长序列怎么拆
4. MoE 专家怎么拆

### 3. 现实中的组合方式
一个常见组合是：

1. **Megatron TP/PP/CP** 负责模型并行
2. **DP 或 FSDP** 负责数据并行维度

也就是说，一个超大模型训练常常不是只用一种并行，而是多维并行叠加。

例如：

1. TP = 4
2. PP = 2
3. DP/FSDP = 8

总共就会用到 \(4 \times 2 \times 8 = 64\) 张卡。

---

## 七、什么是 Megatron FSDP

NVIDIA 官方文档里现在有一个明确概念叫 **Megatron FSDP**。它本质上是 **Megatron-Core 里的 FSDP 实现/能力**，面向大语言模型训练做了优化。

可以把它理解为：

1. 保留 FSDP“完全分片”的核心思想
2. 更贴合 Megatron 训练栈
3. 更适合和 TP、PP、CP 等并行方式一起用

所以“Megatron FSDP”不是完全脱离 FSDP 的新概念，而是：

> **把 FSDP 这条路放进 Megatron 体系里，并针对大模型场景做工程优化。**

---

## 八、三者对比：DDP、FSDP、Megatron

| 方案 | 主要思想 | 解决重点 | 优势 | 代价 |
|---|---|---|---|---|
| DDP | 每卡一整份模型，梯度同步 | 吞吐扩展 | 简单、成熟、稳定 | 显存占用高 |
| FSDP | 参数/梯度/优化器状态分片 | 显存扩展 | 更容易训大模型 | 通信更多，工程更复杂 |
| Megatron | 把模型计算本身拆到多卡 | 超大模型训练 | 支持 TP/PP/CP/EP 等复杂并行 | 系统复杂度更高 |

最简化的理解：

1. **DDP**：多个人各拿一本完整教材，各做不同题，最后对答案
2. **FSDP**：每个人只拿教材的一部分，需要时互相借页
3. **Megatron**：一本教材本身被拆成章节，多个人接力或协同完成

---

## 九、学习这些东西之前，必须先懂哪些基础

如果基础顺序乱了，后面会非常痛苦。最短路径如下。

### 第 1 步：先把单机单卡训练吃透
你至少要完全搞懂：

1. forward / backward / optimizer step
2. batch size、gradient accumulation
3. mixed precision（FP16/BF16）
4. activation checkpointing

因为后面很多分布式优化，本质就是在这套流程上改“谁来存、谁来算、何时通信”。

### 第 2 步：搞懂分布式通信基础
必须知道这些概念：

1. rank
2. world size
3. process group
4. `all-reduce`
5. `all-gather`
6. `reduce-scatter`
7. `broadcast`

如果这些原语不懂，FSDP 和 Megatron 看起来就会像魔法。

### 第 3 步：先学 DDP，再学 FSDP
不要一上来就看 FSDP。

正确顺序应该是：

1. 先理解 DDP 为什么每卡都要放完整模型
2. 再理解 DDP 的瓶颈在哪里
3. 再看 FSDP 如何把模型状态切分掉

### 第 4 步：再学模型并行
学 Megatron 时，顺序建议是：

1. Tensor Parallel
2. Pipeline Parallel
3. Sequence / Context Parallel
4. Expert Parallel

原因很简单：前两个最核心，也最常见。

---

## 十、建议你怎么开始学：一条最省时间的路线

下面这条路线是“先把框架搭起来，再逐步深入”的版本。

### 第 1 阶段：3 天内建立全局认识
目标：先知道每个名词在解决什么问题。

你应该完成：

1. 弄懂 DDP 和 FSDP 的区别
2. 弄懂数据并行、张量并行、流水线并行的区别
3. 能口头说清楚“为什么训练大模型一定会走向多种并行组合”

建议做法：

1. 先看 PyTorch 官方 FSDP 文档或教程
2. 再看 NVIDIA Megatron Core 的 Parallelism Guide

### 第 2 阶段：1 周内把 FSDP 吃透
目标：真正明白 FSDP 的执行流程。

你需要重点想明白这几个问题：

1. 为什么 DDP 显存占用高
2. FSDP 为什么能省显存
3. FSDP 在 forward/backward 前后分别通信了什么
4. 为什么说它是“拿通信换显存”

建议学习动作：

1. 画出 DDP 的内存分布图
2. 画出 FSDP 的内存分布图
3. 自己手写一版伪流程：
   `shard -> all-gather -> forward -> reshard -> backward -> reduce-scatter -> step`

### 第 3 阶段：1 周内把 Megatron 主线吃透
目标：明白 Megatron 的几个并行维度分别在拆什么。

建议顺序：

1. 先盯住 Transformer 的 MLP 和 Attention
2. 理解 TP 怎么切矩阵
3. 理解 PP 怎么切层
4. 理解 micro-batch 为什么能减少 pipeline bubble
5. 最后再补 Sequence/Context Parallel

### 第 4 阶段：开始看真实训练配置
目标：看懂别人训练脚本里的并行配置。

你至少要能看懂：

1. `tensor_model_parallel_size`
2. `pipeline_model_parallel_size`
3. `data_parallel_size`
4. `micro_batch_size`
5. `global_batch_size`

看不懂这些参数，就还没真正进入工程层面。

---

## 十一、如果老师问你“原理”，你可以这样回答

下面这段可以直接拿去当口头回答的骨架。

### 1. FSDP 的原理
FSDP 是数据并行的一种升级版。普通数据并行会在每张 GPU 上复制完整模型，而 FSDP 会把参数、梯度和优化器状态分片到不同 GPU 上保存。某一层前向或反向计算前，再临时通过 `all-gather` 拿到所需完整参数，计算完成后重新分片。这样能显著降低显存占用，但会引入更多通信开销。

### 2. Megatron 的原理
Megatron 的核心是模型并行。它把 Transformer 的大矩阵计算拆到多张 GPU 上做，这叫 Tensor Parallel；把模型不同层拆到不同 GPU 上顺序执行，这叫 Pipeline Parallel；在长序列场景下，还可以进一步把序列维或上下文维拆开，这就是 Sequence/Context Parallel。Megatron 的目标是让超大模型不仅“放得下”，还“算得动”。

### 3. 二者关系
FSDP 主要解决模型状态的存储问题，Megatron 主要解决模型计算的拆分问题。实际训练超大模型时，这两类技术经常结合使用。

---

## 十二、一个容易混淆但很重要的点

### 1. FSDP 不等于所有分布式训练
很多初学者会把 FSDP 当成“大模型分布式训练”的总称，这是不对的。

FSDP 只是其中一条路线，而且主要是**分片数据并行**。

### 2. Megatron 也不只是 Tensor Parallel
很多人一提 Megatron 就只想到 TP，其实 Megatron 的核心价值恰恰在于：

1. 它把多种并行方式系统化了
2. 它专门面向 Transformer/LLM 做了工程优化

### 3. 真正的大模型训练通常是“组合拳”
现实里经常同时出现：

1. Mixed Precision
2. Activation Checkpointing
3. FSDP 或 ZeRO
4. Tensor Parallel
5. Pipeline Parallel
6. 长序列相关并行

不要试图用单一技术解释全部训练系统。

---

## 十三、你现在最值得优先掌握的知识顺序

如果你时间有限，只抓下面这条主线：

1. **先懂 DDP**
2. **再懂 FSDP**
3. **再懂 TP**
4. **再懂 PP**
5. **最后看 Sequence/Context/EP**

原因：

1. DDP 是最基础的参照系
2. FSDP 是最常见的大模型显存扩展方案之一
3. TP 和 PP 是 Megatron 的核心
4. 后面的并行更多是进阶扩展

---

## 十四、给你的一个实际学习计划

### 第 1 天

1. 看懂 DDP 的训练流程
2. 看懂 `all-reduce` 是做什么的

### 第 2 天

1. 看懂 FSDP 为什么能省显存
2. 画出 FSDP 的参数分片和临时聚合过程

### 第 3 天

1. 看懂 Tensor Parallel 如何切线性层
2. 看懂 Pipeline Parallel 如何切层

### 第 4 到 5 天

1. 阅读 Megatron Core 的并行文档
2. 看几个真实训练配置参数

### 第 6 到 7 天

1. 自己写一篇 1 到 2 页总结
2. 能不用稿子讲清楚：
   - FSDP 是什么
   - Megatron 是什么
   - 为什么二者经常一起出现

如果你能做到这一步，入门已经算完成了。

---

## 十五、推荐阅读顺序

### 第一优先级：官方资料

1. PyTorch 官方 FSDP 文档  
   https://docs.pytorch.org/docs/stable/fsdp.html

2. PyTorch 官方 FSDP 教程  
   https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html

3. NVIDIA Megatron Core Parallelism Guide  
   https://docs.nvidia.com/megatron-core/developer-guide/0.16.0/user-guide/parallelism-guide.html

4. NVIDIA Megatron Core User Guide  
   https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/index.html

5. NVIDIA Megatron FSDP 文档  
   https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/features/custom_fsdp.html

6. NVIDIA Megatron-LM GitHub  
   https://github.com/NVIDIA/Megatron-LM

### 第二优先级：读资料时重点盯住的问题

1. 这个技术是在解决显存问题，还是计算扩展问题？
2. 它分的是参数、梯度、优化器状态，还是模型层、矩阵、序列？
3. 它引入了什么通信操作？
4. 它适合单纯多卡，还是超大模型训练？

---

## 十六、最后用一句话收尾

> **FSDP 重点在“把模型状态切开存”，Megatron 重点在“把模型计算切开做”，而现代大模型训练往往就是把这两类思路叠在一起。**

