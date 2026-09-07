# 要求输入

## 要求

1、	学习有限自动机及正则语言理论

2、	学习并发合成算子，并掌握其物理直观意义，最后程序化实现该算子。

3、	学习观测器，并掌握其物理直观意义，最后程序化实现观测器。

4、	学习高阶观测器，并掌握其物理直观意义，最后程序化实现高阶观测器。

## 目标

1、	程序化实现并发合成算子，了解并发合成算子可以被用来解决有限自动机中的哪些问题。

2、	程序化实现观测器，并了解观测器可以被用来解决有限自动机中的哪些问题

3、	程序化实现高阶观测器，并了解高阶观测器可以被用来解决一串有限自动机序列场景下的哪些认知推理问题。

# 内容输出

## 映射到报告中的内容

### Introduction

认知推理问题介绍：

**Whether A_1 can uniquely determine the state of G?**

**So you mean we can propose an algorithm to determine whether #Q'|beta = 1?**

To solve this question, Zhang proposed Hight-order observer.

To understand the tool, first we should review some basic knowledges.

**Does this tool finally solve out this question?**

Yes!

the core is theorem 25, we read beta in obs_{A_1 <- A_2} to know the M_{A_1 <- A_2}(G, beta). 

$$
G,A_1,A_2
\rightarrow Obs_{A_1}
\rightarrow CC\text{ concurrent composition}
\rightarrow Obs_{A_1\leftarrow A_2}.
$$

For each (A_2) observation (\beta), inspect:

$$
Y=M_{A_1\leftarrow A_2}(G,\beta).
$$

If every (X\in Y) satisfies (|X|=1), then (A_2) knows (A_1) can uniquely determine
(G)’s state.

To infer A_1's inference, first we should know all possible output A_1 may see. Every observation alpha comes from a path, and the path must output beta for A_2. In other words, the only restriction for path is l_2(s) = beta.

#### what is M_{A_1\leftarrow A_2}(G,\beta)?

It is (A_2)’s estimate of what (A_1) may estimate:

$$
M_{A_1\leftarrow A_2}(G,\beta)
=
\{M_1(G,\ell_1(s)):s\in L(G),\ell_2(s)=\beta\}.
$$

Each element is one possible (A_1) state estimate.

#### is a state estimate a subset of all states?

Yes.

#### what is the application in real world for this outcome?

Example: satellite scheduling.

- (A_1): onboard controller.
- (A_2): ground CP scheduler.
- Contact is unavailable between communication windows.
- (A_2) only receives delayed telemetry (\beta).

The scheduler infers whether (A_1) knows the satellite state before preparing a safe
task schedule.

#### complexity

2-EXPTIME

### Regular Languages and FAs

- basic knowledge

### CC

1. basic knowledge-base LFSA
2. 物理直观意义
3. 程序化
4. 可以解决的问题

### Observer

1. Basic knowledge
2. 物理直观意义
3. 程序化
4. 可以解决的问题

### High-order Observer

1. Basic knowledge
2. 物理直观意义
3. 程序化
4. 可以解决的问题

### future work

## 映射到 PPT 中的内容

1. 标题页
2. 问题描述
   1. mathematical definition of G
   2. mathematical definition of Agent
3. 基础概念介绍
   1. LFSA
   2. Observer
   3. CC
4. 二阶观测器构造流程
5. 定理25与Example 27
6. 时间、空间复杂度与总结

## some not organized thoughts

### whats the math def of knows? For example, A_1 knows G.

I think there is no need to write sentence like A_1 knows G. Or we def "knows" by: $E_1$ must be a subset of $E$.

  $$
  G\in\mathcal I_{A_1},
  $$

### whats the math def of G|_alpha, instead of using "the current states under output alpha"

$G|_\alpha = M(G, \alpha)$, or to be more specific, there G is required to an LFSA, so exactly the G is (G,A_1).

### what is M_1(G, alpha)?

G is an FSA.

### what is PRED^1?

(PRED^1\subseteq2^Q) is the set of state estimates satisfying a chosen property.

  Example: uniqueness
  [
  PRED^1={X\subseteq Q:|X|=1}.
  ]

  If (M(S,\alpha)={q_2}), it satisfies (PRED^1); ({q_1,q_2}) does not.

### is case studay 1 an example for PRED^1?

Yes.

### what is the meaning of aka in slide 6?

aka = also known as

---

cc -> verify almost all **inference-based properties**(detectability, diagnosability and predictability), and removes two fundamental assumptions of **deadlock-freeness** and **divergence-freeness**.

cc + observer -> solve concealment-based properties(e.g. all kinds of state-based opacity)

the classical tools -> detector, twin-plant and verifier all depend on the above two assumptions. They have almost the same complexity with cc.

---

LFSA -> compared with FSA, it adds letters and labeling function.

**So LFSA can be regarded as FSA + agent**

You need infer what your readers don't know!

**to def current-state estimate, we need def LFSA first**

current-state estimate(LFSA, output_alpha) -> set of states

---

def of cc(LFSA based)

### is cc an LFSA?

Yes. Noticed that the two LFSAs share the same alphabet. 

def of observer(LFSA based)

### observer is an DFA? 

But it dont have final states while DFA has. So it is not a standard DFA? We'd better call it a **deterministic finite-state transition system**.

Its events are got by labels(aka letters)

### whats the meaning of wrt in slide 20?

wrt = with respect to

transition_obs(q_0_obs, alpha) = M(S,alpha)

so we only need to read the obs to get the current-state estimate of LFSA S.

### what is the initial state of obs?

M(S, epsilon)

### How many initial state an LFSA has?

1 or more.

### How many initial state an obs has?

only 1. the unobservable closure of all original initial states.

### is obs's def base on LFSA? 

yes.

### can we change LFSA to other kinds of automata?

not determined.

### why dont reduce an LFSA to somehow a DFA since we only concern the label not the events. So just remove all events and rename labels by events then we get an DFA.

---

