# 离散事件系统中二阶观测器的程序化构造

## 项目简介

本项目实现了离散事件系统中二阶观测器的自动化构造流程。通过输入特定格式的 DES 和 agents 的 json 文件，使用`src\order2_observer.py` 即可得到 json 格式的二阶观测器。

## 理论背景

### 有限状态自动机

有限状态自动机定义为

$$G=(Q,E,\delta,Q_0),$$

其中 $Q$ 为有限状态集，$E$ 为有限事件集，$\delta\subseteq Q\times E\times Q$ 为转移关系，$Q_0\subseteq Q$ 为初始状态集。

带标记有限状态自动机（LFSA）定义为

$$S=(Q,E,\delta,Q_0,\Sigma,\ell),$$

其中 $\Sigma$ 为有限输出字母表，$\ell:E\to\Sigma\cup\{\epsilon\}$ 为标记函数。可观事件集与不可观事件集分别为

$$E_o=\{e\in E\mid \ell(e)\in\Sigma\},\qquad E_{uo}=\{e\in E\mid \ell(e)=\epsilon\}.$$

对 $\alpha\in\Sigma^*$，当前状态估计定义为

$$M(S,\alpha)=\{q\in Q\mid \exists q_0\in Q_0,\exists s\in E^*:q_0\xrightarrow{s}q\land\ell(s)=\alpha\}.$$

### 并发组合

给定 $S_i=(Q_i,E_i,\delta_i,Q_{0i},\Sigma,\ell_i)$（$i=1,2$），其并发组合定义为

$$CC(S_1,S_2)=(Q',E',\delta',Q'_0,\Sigma,\ell'),$$

其中

$$Q'=Q_1\times Q_2,\qquad Q'_0=Q_{01}\times Q_{02},$$

$$E'=E'_o\cup E'_{uo},$$

$$E'_o=\{(e_1,e_2)\mid e_i\in E_{io},\ \ell_1(e_1)=\ell_2(e_2)\},$$

$$E'_{uo}=\{(e_1,\epsilon)\mid e_1\in E_{1uo}\}\cup\{(\epsilon,e_2)\mid e_2\in E_{2uo}\}.$$

转移关系 $\delta'$ 定义为

$$((q_1,q_3),(e_1,e_2),(q_2,q_4))\in\delta'\iff(q_1,e_1,q_2)\in\delta_1\land(q_3,e_2,q_4)\in\delta_2,$$

$$((q_1,q_3),(e_1,\epsilon),(q_2,q_3))\in\delta'\iff(q_1,e_1,q_2)\in\delta_1,$$

$$((q_1,q_3),(\epsilon,e_2),(q_1,q_4))\in\delta'\iff(q_3,e_2,q_4)\in\delta_2,$$

且 $\ell'((e_1,e_2))=\ell_1(e_1)=\ell_2(e_2)$。

### 观测器

LFSA $S$ 的观测器定义为确定性有限状态自动机

$$Obs(S)=(Q_{obs},\ell(E_o),\delta_{obs},q_{0,obs}),$$

其中

$$Q_{obs}=2^Q,$$

$$q_{0,obs}=\bigcup_{q_0\in Q_0}\ \bigcup_{s\in E_{uo}^*}\delta(q_0,s)=M(S,\epsilon),$$

$$\delta_{obs}(X,a)=\bigcup_{q\in X}\ \bigcup_{\substack{e\in E_o\\\ell(e)=a}}\ \bigcup_{s\in E_{uo}^*}\delta(q,es).$$

### 二阶观测器

对智能体 $A_i$ 的标记函数 $\ell_i:E\to\Sigma_i\cup\{\epsilon\}$，$A_2$ 在观测到 $\alpha\in\ell_2(L(G))$ 后对 $A_1$ 状态估计的二阶估计定义为

$$M_{A_1\leftarrow A_2}(G,\alpha)=\{M(G,\ell_1(s))\mid s\in\ell_2^{-1}(\alpha)\cap L(G)\}\subseteq 2^Q.$$

二阶谓词定义为

$$PRED_2\subseteq 2^{2^Q}.$$

二阶观测器定义为

$$Obs_{A_1\leftarrow A_2}(G)=Obs_{\ell_2}\!\left(CC^{G,Obs_{A_1}}_{A_1\to A_2}\right),$$

其中 $Obs_{A_1}=Obs_{\ell_1}(G)$，$CC^{G,Obs_{A_1}}_{A_1\to A_2}$ 由 $CC_{\ell_1}(G_{A_1},Obs_{A_1})$ 将事件对 $(e_1,e_2)$ 投影为 $e_1$，并以 $\ell_2$ 重标记得到。

## 项目架构

```text
.
├── src/                 # 核心算法与转换工具
│   ├── order2_observer.py   # 二阶观测器构造入口
│   ├── observer.py          # 一阶观测器构造
│   ├── CC.py                # LFSA 并发合成算子
│   ├── fa_agent_to_lfsa.py  # FSA 与 agent 合并得到 LFSA
│   ├── fa_to_lfsa.py        # FSA 转 LFSA
│   ├── lfsa_to_fa.py        # LFSA 转 FSA
│   └── relabel_composition.py # 组合结果投影与重标记
├── data/
│   ├── models/          # DES 模型输入
│   ├── agents/          # agent 配置输入
│   └── results/         # 算法输出与中间结果
└── docs/                # 理论文献与说明
```

## 例子

![alt text](tmp/pdfs/example27-109.png)

## How to run

To use the python script that **generating high-order observer** from an FSA and two agents, locate `src\order2_observer.py`. If you ran it in VScode, click the button of code-runner extension and follow the guidance.
