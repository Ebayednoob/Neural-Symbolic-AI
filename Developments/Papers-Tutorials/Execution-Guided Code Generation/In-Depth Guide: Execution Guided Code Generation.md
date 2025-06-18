# An In-Depth Guide to Execution-Guided Code Generation

This document provides a detailed technical and mathematical breakdown of the paper **"Execution Guided Line-by-Line Code Generation"** by Lavon, Katz, and Wolf. We explore the core concepts, the feedback mechanism, and the mathematics that power the EG-CFG method.

---

## 1. The Core Problem: Static vs. Dynamic Code Generation

Traditional Large Language Models (LLMs) are trained on vast amounts of static code from the internet. When asked to generate a program, they excel at recognizing and reproducing syntactic patterns they have seen before. However, this approach has a fundamental limitation: it lacks an understanding of runtime execution.

### Static Approach
The model generates a complete block of code and only then can it be tested. If it fails, the entire process must be repeated, often with only high-level feedback like "an error occurred." This is inefficient and often leads to code that looks correct but contains subtle, hard-to-find bugs.

### Human Approach
A human programmer rarely writes a full program without testing. They write small fragments, run them, check variable states, and use this immediate, granular feedback to debug and guide their next steps.

### The EG-CFG Goal
The goal of **Execution-Guided Classifier-Free Guidance (EG-CFG)** is to make LLMs work more like human programmers by integrating real-time execution feedback directly into the generation process.

---

## 2. The EG-CFG Method: A Detailed Look

EG-CFG is an **inference-time technique**, meaning it doesn't require retraining the model. It works by intelligently guiding a standard pre-trained LLM during the generation process.

### 2.1 Initial Setup: The Prompt

The process begins with a structured prompt ```\( p_{\text{inst}} \)``` containing all the necessary information:
```
p_inst = (p_0, p_task, T, f_name)
```

- **p₀**: A base instruction template (e.g., few-shot examples).
- **p_task**: Natural language description of the task.
- **T**: A set of unit tests ```\({t_j}\)``` that the generated code must pass.
- **f_name**: Name of the function to be generated.

---

### 2.2 The Dynamic Feedback and Guidance Cycle

This is the **core innovation** of EG-CFG. For each line of code, the model follows a four-step loop:

#### Step 1: Explore Possible Futures (Beam Search)

Use beam search to generate **s** diverse candidates, each extending the solution by **d** lines.
```
c_j ∼ M(p_sol; d, t) for j = 1, ..., s
```

- **p_sol**: Current solution prefix.
- **M**: The language model.
- **d**: Completion horizon (lines per candidate).
- **t**: Sampling temperature (exploration control).
- **s**: Beam width (number of candidates).

#### Step 2: Ensure Executability (AST Parsing)

Filter candidates into syntactically valid Python using:
```
ĉ_j = ExtractExecutable(c_j)
```

This may involve appending `pass` or trimming incomplete lines.

#### Step 3: Execute and Gather Traces

Each valid candidate ```\( \hat{c}_j \)``` is tested against each ```\( t_m ∈ T \),``` producing execution traces ```\( e_{j,m} \),``` which include:

- Executed lines
- Variable states
- Function calls & return values
- Detailed runtime errors

#### Step 4: Form the Guidance Signal

Aggregate all ```\( \hat{c}_j \)``` and their traces into a new prompt ```\( p_{\text{dyn}} \):```
```
p_dyn = [p_sol (prefix), p_signal, p_sol (suffix)]
```

This prompts the model: *"Here’s what happened with each candidate—what should you write next?"*

---

## 3. The Mathematics of Guidance: Classifier-Free Guidance (CFG)

CFG steers the model by interpolating between standard and guided predictions.

### CFG Formula:
```
log M_CFG(w_i | p_sol, p_dyn) = log M(w_i | p_sol) + γ [log M(w_i | p_dyn) − log M(w_i | p_sol)]
```

Where:
```
- **log M(wᵢ | p_sol)**: The unconditional distribution (prior).
- **log M(wᵢ | p_dyn)**: The conditional (guided) distribution.
- **[ ... ]**: The **guidance signal**, or directional nudge from execution feedback.
- **γ**: The guidance scale hyperparameter.
```
#### Behavior:
```
- **γ = 0**: No guidance.
- **γ = 1**: Fully guided.
- **γ > 1**: Amplified guidance.
```
---

## 4. The Full Inference Loop and Parallelism

The complete loop for line-by-line generation:

1. Begin with the problem prompt.
2. For each line:
   - Generate candidate continuations (beam search).
   - Execute and collect traces.
   - Form the dynamic prompt \( p_{\text{dyn}} \).
   - Use CFG to pick the next best token.
   - Append it to the current solution.
3. Repeat until the function is complete.

### Parallelism Advantage

EG-CFG allows **parallel exploration** with different:

- Temperatures \( t \)
- Guidance scales \( γ \)

Multiple agents can explore diverse reasoning paths. The **first agent** to pass all test cases returns the final solution; all others are halted.

---

## 5. Results and Conclusion

EG-CFG achieves **state-of-the-art results** on:

- **MBPP**
- **HumanEval-ET**
- **CodeContests**

Even outperforming larger, closed-source models.

### Key Insight:

> Integrating **execution-based feedback** during generation significantly improves code reliability and correctness.

By mimicking the **"write-test-debug"** cycle of human programmers, EG-CFG **bridges the gap** between static pattern-matching and runtime reasoning.

---

## References

- Lavon, Y., Katz, E., & Wolf, L. (2023). *Execution Guided Line-by-Line Code Generation*. arXiv preprint arXiv:2305.XXXX.
