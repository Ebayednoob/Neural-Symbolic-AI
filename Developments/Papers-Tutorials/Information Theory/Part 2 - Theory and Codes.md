# Information Theory & Codes: A Deep Dive
_A multipart lesson on the foundations of data compression._

---

## Part 1: Entropy & Information

Information theory begins with a simple question: **how do we quantify information?** The answer lies in the concept of **entropy**, which measures the average uncertainty or "surprise" of a random variable.

### Visualizing Entropy

A distribution with **low entropy** is predictable. A distribution with **high entropy** is unpredictable. The **maximum possible entropy** for a variable with |X| outcomes occurs when all outcomes are equally likely (the uniform distribution).

**Concept:**  
An interactive calculator could show a 3-outcome probability distribution. As you adjust the probabilities with a slider, you would see the entropy value H(X) change. Entropy is maximized when the probabilities are as close to uniform as possible and minimized when one outcome is nearly certain.

---

### Fano's Inequality: The Limits of Guessing

**Fano's inequality** gives us a hard limit on our ability to guess a random variable X even if we have information from a related variable Y. It connects the remaining uncertainty (conditional entropy) to the probability of making an error.

**Fano's Inequality:**

```math
H(X|Y) ≤ H(Pₑ) + Pₑ * log₂(|X| - 1)
```

If your probability of error (Pₑ) is low, the right side of the inequality is small. This forces the conditional entropy H(X|Y) to also be small, meaning you must have low uncertainty about X given Y. You **cannot** have a low error rate and high uncertainty simultaneously.

**Concept:**  
A visualization could show how the maximum allowable conditional entropy (the "Fano Bound") changes as you adjust the error rate Pₑ and the number of outcomes |X|. This demonstrates that for a given error rate, there is a hard cap on how much uncertainty can remain.

---

## Part 2: The Language of Codes

A **code** is a system for translating symbols from one alphabet (e.g., English letters) into another (e.g., binary digits). The goal is to create a representation that is both efficient and, crucially, unambiguous.

### The Concatenation Problem & The Need for Better Codes

Simply assigning a unique binary string to each symbol isn't enough. When we concatenate codewords, we can create **ambiguity**. This is the core problem that leads to the study of different code properties.

#### Key Definitions

- **Uniquely Decodable (UD):** Every sequence of symbols maps to a unique encoded string. This is the minimum requirement for a useful code.
- **Prefix Code:** No codeword is a prefix of another codeword. This is a much stronger condition that makes decoding incredibly simple and fast.

---

### Visualizing Codes with Trees

We can visualize a binary code as a **binary tree**. Each edge represents a bit (0 for left, 1 for right). A codeword corresponds to a path from the root.

#### Prefix Code Tree

In a prefix code, all codewords are located at the **leaf nodes** of the tree. You cannot continue a path past a valid codeword.

**Example:**  
`{A: 0, B: 10, C: 110, D: 111}`

#### Non-Prefix Code Tree

In a non-prefix code, at least one codeword is an **internal node** on the path to another codeword. This is what creates ambiguity.

**Example:**  
`{A: 0, B: 01, C: 011, D: 111}`  
(Here, 'A' is a prefix of 'B' and 'C')

---

### Interactive Decoder

The practical difference is huge. A **prefix code** can be decoded instantly. A **non-prefix (but uniquely decodable)** code might require you to look far ahead in the message to resolve ambiguity.

**Concept:**  
An interactive decoder would show that when decoding a message from a prefix code, each codeword is identified immediately. For a non-prefix code like the one above, decoding the string `0011111` is tricky. You can't know the first '0' is an 'A' until you've processed the rest of the string to see that the full message is `ACD`. A decoder would have to backtrack.

---

## Part 3: Efficiency & Optimal Codes

We want our codes to be **unambiguous**, but also **efficient**. An efficient code uses **shorter codewords for more frequent symbols**, minimizing the average length of an encoded message.

---

### The Kraft-McMillan Theorem

This remarkable theorem connects the property of unique decodability to codeword lengths. It tells us the **mathematical constraint** that all UD code lengths must obey.

**Kraft-McMillan Theorem:**  
A uniquely decodable D-ary code with lengths L₁, L₂, ... exists **if and only if:**
```math
∑ (1 / D^Lᵢ) ≤ 1
```

Crucially, it also proves that for any set of lengths that satisfies this inequality, a **prefix code can be constructed**. This means we lose **no efficiency** by restricting ourselves to easy-to-decode prefix codes!

**Concept:**  
A Kraft Inequality Checker would let you input a set of codeword lengths. It would calculate the sum and tell you if a prefix code with those lengths is possible.  
- Lengths `1, 2, 2` result in `1/2 + 1/4 + 1/4 = 1` → ✅ valid  
- Lengths `1, 1, 2` result in `1/2 + 1/2 + 1/4 = 1.25` → ❌ invalid

---

### Building an Optimal Prefix Code: Huffman Coding

The Kraft-McMillan theorem is an **existence proof**. The **Huffman algorithm** is a **constructive proof**: a simple, greedy algorithm that creates an optimal prefix code for a given probability distribution.

The algorithm repeatedly merges the two least probable symbols into a new "meta-symbol", building a binary tree from the leaves up to the root.

**Concept:**  
An interactive Huffman coder would take a set of symbols and their frequencies as input (e.g., `a:45, b:13, c:12, d:16, e:9, f:5`). It would then automatically:

- Generate the **optimal Huffman code table**, showing the efficient binary codeword for each symbol.
- Display the resulting **Huffman tree**, visually representing the code structure.
- Calculate the **average codeword length** for the given frequencies.

---
