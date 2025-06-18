# Interactive Tutorial: Flow Matching & Diffusion Models

This tutorial, based on _"An Introduction to Flow Matching and Diffusion Models,"_ will guide you through the fundamental principles of these powerful generative models. We'll explore how they transform simple noise into complex data, like images, by following the path laid out by differential equations.

---

## 1. The Goal: Transforming Noise into Data

The core idea of generative modeling is to learn a transformation from a simple, easy-to-sample probability distribution, `p_init` (e.g., a standard Gaussian N(0, I)), to a complex, target data distribution, `p_data` (e.g., the distribution of all photorealistic images of cats).

- **Objects as Vectors:** Any object (image, video, molecule) is represented as a high-dimensional vector `z ∈ ℝᵈ`.
- **Generation as Sampling:** "Generating" an object is drawing a sample `z` from the data distribution `p_data`.
- **The Transformation:** The model transforms a random vector `x₀` sampled from `p_init` into a vector `x₁` that appears sampled from `p_data`.

This transformation is achieved by simulating a differential equation over a time interval, typically `t ∈ [0, 1]`.

---

## 2. The How: Ordinary & Stochastic Differential Equations

The path from noise to data is defined by a differential equation:

### Flow Models (ODEs)

A flow model uses a deterministic path. The evolution of a sample `X_t` at time `t` is governed by an ODE:

```
dX_t/dt = u_t(X_t)
```

Where:
- `X_t`: Sample position at time `t`
- `u_t(X_t)`: A vector field parameterized by a neural network, defining velocity at point `X_t`

> Think of `u_t` as arrows in space. Starting at `X₀`, follow the arrows to reach `X₁`.

### Diffusion Models (SDEs)

A diffusion model introduces randomness via a stochastic differential equation:

```
dX_t = u_t(X_t) dt + σ_t dW_t
```

Where:
- `σ_t dW_t`: Brownian noise component
- `σ_t`: Diffusion coefficient (noise level)
- `dW_t`: Brownian motion increment

> Even with the same `X₀`, the stochastic process gives a different `X₁` every time.

---

## 3. The What: Constructing the Training Target

To train the neural network `u_t^θ`, we need a vector field that guarantees transformation from `p_init` to `p_data`.

### Step 1: Define a Probability Path

Create a smooth interpolation `p_t(x)` from `p₀ = p_init` to `p₁ = p_data` using:

```
x_t = α_t * z + β_t * ε
```

Where:
- `z ~ p_data`, `ε ~ p_init`
- `α_t`, `β_t` are scheduling coefficients with:
  - `α₀ = 0`, `β₀ = 1` → pure noise
  - `α₁ = 1`, `β₁ = 0` → pure data

### Step 2: Find the Target Vector Field

Using the **Marginalization Trick**:

```
u_t^target(x) = E_{z ~ p_data}[u_t^target(x | z)]
```

For the Gaussian path, the conditional vector field has a closed-form (from Eq. 21):

```
u_t^target(x | z) = ( (dα_t/dt - (β_t * dβ_t/dt) / α_t) * z ) + (β_t * dβ_t/dt / α_t) * x
```

This is the ground truth used for **flow matching**.

### Step 3: Extend to SDEs with a Score Function

The full SDE generating `p_t`:

```
dX_t = [u_t^target(X_t) + 2σ_t² ∇log p_t(X_t)] dt + σ_t dW_t
```

To estimate `∇log p_t(x)`, use the conditional score:

```
∇log p_t(x | z) = - (1 / β_t²) * (x - α_t * z)
```

This is the ground truth for **score matching**.

---

## 4. The How: Training with Flow and Score Matching

We train our models using MSE losses against conditional targets.

### Conditional Flow Matching (CFM)

Train the vector field network `u_t^θ` with:

```
L_CFM(θ) = E_{t,z,ε} [ || u_t^θ(α_t z + β_t ε) - u_t^target(α_t z + β_t ε | z) ||² ]
```

### Conditional Score Matching (CSM)

Train the score network `s_t^θ` (or ε_θ to predict noise) with:

```
L_CSM(θ) = E_{t,z,ε} [ || s_t^θ(α_t z + β_t ε) - ∇log p_t(α_t z + β_t ε | z) ||² ]
```

---

By optimizing these loss functions, `u_t^θ` and `s_t^θ` learn to approximate the true marginal vector field and score function, allowing generation of new samples from `p_data`.

