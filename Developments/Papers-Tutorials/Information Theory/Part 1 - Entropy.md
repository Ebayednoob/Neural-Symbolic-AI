# An Interactive Guide to Information Theory: Summary

This document summarizes the core concepts of Information Theory as presented in the interactive tutorial based on the lecture by Sam Cohen.

---

## 1 · What is Information Theory?

Information theory is a mathematical framework for **quantifying** and **communicating** information.  
It addresses three fundamental questions:

1. **Quantifying Information**  
   *How can we describe and measure the amount of information obtained from a signal?*

2. **Efficient Encoding**  
   *How can data be encoded efficiently to minimize storage or transmission resources while allowing perfect reconstruction?*

3. **Noisy Communication**  
   *How can we ensure reliable communication even when the transmission medium is noisy and may introduce errors?*

---

## 2 · Surprise and Entropy

### The Notion of “Surprise”

The “surprise” of an event is a measure of its unpredictability.  
It is defined by three axioms:

- It is continuous with respect to the event’s probability.  
- More probable events are **less** surprising.  
- The surprise of two independent events is the **sum** of their individual surprises.

The only function satisfying these properties is the **negative logarithm** of the probability.  
For an event $A$:

$$
S(A) = -\log_2 P(A)
$$

Surprise is measured in **bits** when the logarithm uses base 2.

---

### Entropy · The Average Surprise

While *surprise* relates to a single outcome, **entropy** measures the *average* surprise of a random variable across all its possible outcomes—it quantifies total uncertainty.

For a discrete random variable $X$ with outcomes $x \in \mathcal{X}$ and a probability mass function $p(x)$:

$$
H(X) = - \sum_{x \in \mathcal{X}} p(x) \log_2 p(x)
$$

Alternatively, entropy can be written as the expected value of the surprise:

$$
H(X) = \mathbb{E}[-\log_2 p(X)]
$$

> **Note:** By convention, $0 \log 0 = 0$, since an impossible event contributes nothing to the average surprise.  
> Entropy is **maximized** when all outcomes are equally likely (maximum uncertainty), and is **zero** when one outcome is certain (no uncertainty).

---

## 3 · Related Quantities

### Kullback–Leibler (KL) Divergence

**KL Divergence** (or *relative entropy*) measures how one probability distribution $P$ diverges from another distribution $Q$:

$$
D_{\mathrm{KL}}(P \| Q) = \sum_{x \in \mathcal{X}} P(x) \log_2 \left( \frac{P(x)}{Q(x)} \right)
$$

Key properties:

- $D_{\mathrm{KL}}(P \| Q) \geq 0$
- $D_{\mathrm{KL}}(P \| Q) = 0$ **if and only if** $P = Q$
- It is **not symmetric**:  
  $D_{\mathrm{KL}}(P \| Q) \neq D_{\mathrm{KL}}(Q \| P)$ in general

---

### Mutual Information

**Mutual Information**, $I(X;Y)$, quantifies the dependency between two random variables $X$ and $Y$. It measures the reduction in uncertainty about one variable given knowledge of the other.

It can be defined as the KL divergence between the joint distribution $P(X,Y)$ and the product of their marginal distributions $P(X)P(Y)$:

$$
I(X;Y) = D_{\mathrm{KL}}(P(X,Y) \| P(X)P(Y))
$$

This leads to a more intuitive formula based on entropy:

$$
I(X;Y) = H(X) + H(Y) - H(X, Y)
$$

- If $X$ and $Y$ are **independent**, then $I(X;Y) = 0$
- If $X$ and $Y$ are **perfectly correlated**, then $I(X;Y) = H(X) = H(Y)$

---
