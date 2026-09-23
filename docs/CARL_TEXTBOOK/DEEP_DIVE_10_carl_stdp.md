# 🔬 DEEP DIVE #10 — `carl_stdp.py` (Every Line, Every Number, Every Why)
> *278 lines. Zero skipped. Three-factor Hebbian learning, R-STDP, and Quantum decision-making.*

---

## FILE PURPOSE

This file implements CARL's **associative memory and deliberation system** — the answer to "how does CARL learn which actions lead to good outcomes?"

Three classes:
1. **`STDPSynapse`**: The learning rule itself — how synaptic weights change based on spike timing and reward
2. **`STDPActionEvaluator`**: Uses STDP to score actions — "how good was this action in this context?"
3. **`QuantumDeliberator`**: Chooses between competing action strategies using quantum-inspired probability

---

## LINES 1–16: Docstring — The Three-Factor Rule

```python
"""
Three-factor learning rule:
  ΔW = learning_rate × Reward × Eligibility_Trace

Where eligibility trace tracks STDP correlations:
  dE/dt = -E/tau_E + STDP(pre, post)

And STDP:
  pre before post  → LTP (Long Term Potentiation) — strengthen
  post before pre  → LTD (Long Term Depression)   — weaken
"""
```

**What is "three-factor"?**

Classic Hebbian learning: `ΔW = pre × post` (two factors)  
STDP: `ΔW = f(pre timing, post timing)` (still two factors, but timing-sensitive)  
**Three-factor:** `ΔW = Reward × Eligibility_Trace` = `Reward × f(pre timing, post timing)`

**Why add the third factor (Reward)?** Without reward, STDP strengthens ANY synapse where pre fired before post — regardless of outcome. A neuron that fired before a bad outcome would get strengthened just as much as one before a good outcome. The reward gating means "only strengthen if the outcome was positive." This is what real dopaminergic reward learning does (Izhikevich 2007, confirmed by Legenstein et al. 2008).

**Why "Eligibility Trace" instead of instant weight update?** There's a time delay between action and reward (~0.1-10 seconds in animals). The eligibility trace "remembers" which synapses fired recently — like a temporary mark that says "I was just active." When reward arrives later, it stamps those marked synapses: "whatever you just did, it was good — get stronger." Without eligibility traces, a reward can only strengthen the synapses that fired at the EXACT moment of reward, not the ones that caused the reward 1 second ago.

---

## LINES 22–29: Global Constants

```python
TAU_PRE   = 20.0   # ms — pre-synaptic trace decay
TAU_POST  = 20.0   # ms — post-synaptic trace decay
TAU_E     = 50.0   # ms — eligibility trace decay
A_PLUS    = 0.01   # LTP amplitude
A_MINUS   = 0.012  # LTD amplitude (slightly asymmetric — bias toward depression)
W_MAX     = 2.0    # Maximum synaptic weight
W_MIN     = -0.5   # Minimum (allows weak inhibition)
LR        = 0.008  # Reward modulation learning rate
```

**Why `TAU_PRE = TAU_POST = 20.0 ms`?** These set the time window for STDP. A pre-synaptic spike raises A_pre, which decays with tau=20ms. If a post-synaptic spike arrives within 20ms after the pre spike, A_pre is still non-zero → LTP occurs. Beyond 20ms, A_pre ≈ 0 → no STDP signal.

Biologically, STDP has a window of ~20ms (Bi and Poo 1998). 20ms is the standard.

**Why `TAU_E = 50.0 ms`?** Eligibility traces persist longer than individual spike traces. This 50ms window allows reward to arrive up to 3× later than the spike event and still reinforce the right synapses.

**Why `A_MINUS = 0.012 > A_PLUS = 0.01`?** Asymmetric STDP. LTD is 20% stronger than LTP. This creates a **bias toward synaptic weakening** — without reward, the network naturally depresses connections. This prevents runaway potentiation (all weights growing to W_MAX) and ensures only rewarded connections survive.

Biologically, this asymmetry is widely observed (Song et al. 2000) and gives rise to stable competition between synapses.

**Why `W_MAX = 2.0`?** Limits how strong any single synapse can become. Prevents one synapse from monopolizing all output computation.

**Why `W_MIN = -0.5`?** Allows WEAK INHIBITION. Not all synapses are excitatory — some can be inhibitory (negative). -0.5 allows some suppression of actions, but caps inhibition at half the strength of excitation.

**Why `LR = 0.008`?** The learning rate scales how fast weights change per unit of reward × eligibility. 0.008 is small — stable but non-zero. Too large → oscillatory weight dynamics. Too small → learning takes forever.

---

## LINES 40–60: `STDPSynapse.__init__()`

```python
def __init__(self, pre_size, post_size, init_scale=0.1):
    self.W = np.random.randn(pre_size, post_size) * init_scale
```

**`W` shape: (pre_size, post_size) = (20, 9)**

20 = `full_dim = state_dim(5) + visual_dim(15)` — the state encoding  
9 = `n_actions` — the action candidates

`W[i, j]` = strength of synapse from pre-neuron i (encodes state) to post-neuron j (encodes action j).

**`np.random.randn() × init_scale`**: Initial weights from N(0, 0.1²). This is small random initialization so CARL starts with weak but diverse associations. If init_scale=0 (all zeros), the symmetry would prevent any neuron from ever being preferred — the network would never differentiate.

---

```python
    self.E = np.zeros((pre_size, post_size), dtype=float)
```

**Eligibility trace matrix**: Same shape as W. `E[i,j]` = how "recently active" synapse (i→j) was. This is the "mark" that reward uses to decide which weights to update.

---

```python
    self.A_pre  = np.zeros(pre_size,  dtype=float)   # (pre_size,)
    self.A_post = np.zeros(post_size, dtype=float)   # (post_size,)
```

**Spike traces:**
- `A_pre[i]`: Running trace of pre-neuron i's recent activity
- `A_post[j]`: Running trace of post-neuron j's recent activity

These decay exponentially after each spike. They're NOT spike counts — they're continuous soft memories of "how recently did this neuron fire?"

---

```python
    self.reward_buf = deque(maxlen=5)
```

**`deque(maxlen=5)`**: A double-ended queue capped at 5 elements. When element 6 is appended, element 1 is automatically removed. This is a circular buffer of the 5 most recent reward signals. Used to smooth reward with a 5-step average.

**Why average over 5 steps?** Reward signals can be noisy. Single-step reward: `DA = 1.2` might be due to sensor noise, not actual food. 5-step average: smooths over ~150ms (5 × 30ms) — long enough to filter noise, short enough to still be responsive.

---

## LINES 62–108: `STDPSynapse.step()` — The Learning Update

```python
def step(self, pre_spikes, post_spikes, reward, dt=1.0):
```

**`pre_spikes`**: Shape (pre_size,) = (20,). Binary or rate vector — how much each pre-neuron just fired. Range [0, 1].  
**`post_spikes`**: Shape (post_size,) = (9,). One-hot vector of which action was taken.  
**`reward`**: Scalar. Positive = good outcome, negative = bad.  
**`dt`**: Timestep in units compatible with TAU values. Here dt=1.0 (each call = 1 unit of time).

---

```python
    decay_pre  = np.exp(-dt / TAU_PRE)    # = exp(-1/20) = 0.9512
    decay_post = np.exp(-dt / TAU_POST)   # = exp(-1/20) = 0.9512
    decay_e    = np.exp(-dt / TAU_E)      # = exp(-1/50) = 0.9802
```

**Exact exponential decay factors:**

The ODE for a trace: `dA/dt = -A/τ`  
Exact solution for one step: `A(t+dt) = A(t) × e^(-dt/τ)`

`exp(-1/20) = 0.9512`: Each step, A_pre retains 95.12% of its previous value. After 20 steps: `0.9512^20 = 0.368 = 1/e` (one time constant).

`exp(-1/50) = 0.9802`: Eligibility trace is slower — retains 98% per step.

Why compute these factors ONCE and multiply? `e^(-dt/τ)` is computed ONCE and applied to ALL neurons at once (`self.A_pre *= decay_pre` is vectorized). Much faster than looping over each neuron.

---

```python
    self.A_pre  *= decay_pre    # Decay all pre-synaptic traces
    self.A_post *= decay_post   # Decay all post-synaptic traces
    self.E      *= decay_e      # Decay all eligibility traces
```

Three separate vectorized decays. `*=` modifies in-place (no new array allocation — memory efficient).

**Why decay BEFORE computing STDP?** The decayed trace represents "what happened BEFORE this timestep." We compute STDP using the OLD traces (which pre-spikes happened before this current post-spike). This preserves causal order.

---

```python
    # LTP: post fired, pre just fired (pre causes post) → strengthen
    if np.any(post_spikes > 0):
        ltp = np.outer(self.A_pre, post_spikes) * A_PLUS
        self.E  += ltp
        self.ltp_events += int(np.sum(post_spikes > 0))
```

**LTP (Long-Term Potentiation) — "pre before post" learning:**

If a post-synaptic neuron fires NOW, AND pre-synaptic neuron i recently fired (A_pre[i] > 0), then synapse (i→j) contributed to this post-spike. Strengthen it.

**`np.outer(self.A_pre, post_spikes)`**: Outer product.  
`A_pre` shape (20,), `post_spikes` shape (9,) → result shape (20, 9).  
Entry [i, j] = `A_pre[i] × post_spikes[j]`.

**What this means:**
- For each currently-firing post-neuron j (where `post_spikes[j] > 0`):
  - For each pre-neuron i with recent activity (where `A_pre[i] > 0`):
    - Add `A_pre[i] × post_spikes[j] × A_PLUS` to eligibility trace E[i,j]

This says: "Neuron i was recently active AND neuron j just fired — their synapse might be causal. Mark it (E increases) by an amount proportional to how recently i fired and how strongly j fired."

**`× A_PLUS = × 0.01`**: Scales the eligibility increase. Each post-spike adds at most 0.01 to E per synapse per step.

---

```python
    # LTD: pre fired, post just fired before → depress
    if np.any(pre_spikes > 0):
        ltd = np.outer(pre_spikes, self.A_post) * (-A_MINUS)
        self.E  += ltd
        self.ltd_events += int(np.sum(pre_spikes > 0))
```

**LTD (Long-Term Depression) — "post before pre" → depression:**

If a pre-synaptic neuron fires NOW, AND post-synaptic neuron j recently fired BEFORE (A_post[j] > 0), then the pre-spike arrived AFTER the post-spike — the pre-spike is IRRELEVANT to what caused the post-spike. Weaken the synapse.

**`np.outer(pre_spikes, self.A_post)`**: Shape (20, 9).  
Entry [i, j] = `pre_spikes[i] × A_post[j]`.

**`× (-A_MINUS)`**: Negative — this DECREASES the eligibility trace.

**Why `(-A_MINUS)`?** We could write `self.E -= ltd_positive`. Writing `× (-A_MINUS)` and then `+= ltd` achieves the same result. The eligibility trace can go NEGATIVE — this means this synapse is currently "anti-marked." When reward arrives, if E[i,j] < 0, the weight DECREASES even for positive reward (the synapse is penalized for this pattern regardless of reward).

---

```python
    # ── Update traces AFTER correlation (causal order) ───
    self.A_pre  += pre_spikes
    self.A_post += post_spikes
```

**CRITICAL CAUSAL ORDERING**: Traces are updated AFTER computing STDP.

Why? When we compute LTP, we use `A_pre` (the trace of PAST pre-spikes) to know "did pre fire BEFORE post?" If we updated `A_pre += pre_spikes` FIRST, then `A_pre` would include the CURRENT pre-spikes too, making it look like pre "caused" post even when they fired simultaneously. Updating AFTER preserves the causal story: "A_pre is the history of pre-spikes before THIS moment."

---

```python
    self.reward_buf.append(reward)
    avg_reward = float(np.mean(self.reward_buf)) if self.reward_buf else 0.0

    if abs(avg_reward) > 1e-4:
        dW = LR * avg_reward * self.E
        self.W  = np.clip(self.W + dW, W_MIN, W_MAX)
        self.total_weight_change += float(np.linalg.norm(dW))
```

**Three-factor weight update:**
```
ΔW = LR × reward × E
W_new = clip(W_old + ΔW, -0.5, 2.0)
```

`dW` shape: (20, 9) — same as W and E.

**`if abs(avg_reward) > 1e-4`**: Only update if reward is non-negligible. This prevents noise (tiny reward fluctuations near zero) from corrupting the weights with irrelevant small updates. `1e-4 = 0.0001` — anything smaller than this is considered "zero reward."

**`LR × avg_reward × self.E`**: The three factors:
1. `LR = 0.008`: Learning rate (scales overall magnitude of change)
2. `avg_reward`: Sign and magnitude of reward (+ = strengthen, − = weaken)
3. `self.E`: Which synapses were recently active (eligibility) and in which direction (LTP or LTD)

**Example:**
- E[3, 1] = +0.05 (synapse 3→1 recently showed LTP pattern)
- avg_reward = +0.8 (positive reward: food found)
- dW[3,1] = 0.008 × 0.8 × 0.05 = +0.00032

Small change per step, but after 100 rewarded episodes: `+0.032` — measurable strengthening.

---

## LINES 110–112: `predict()`

```python
def predict(self, pre_activity):
    return np.tanh(self.W.T @ pre_activity)   # (post_size,)
```

**Forward pass:**
- `self.W.T` shape: (9, 20) — note TRANSPOSE. We want output per action.
- `pre_activity` shape: (20,)
- `self.W.T @ pre_activity`: (9,) — dot product of each action's weights with state

**`np.tanh(...)`**: Squashes output to (-1, 1). High positive = this action is well-associated with the current state. High negative = this action was punished in this state.

**Why tanh not softmax?** We want a QUALITY score per action (can be negative, allowing explicit punishment), not a probability (which would require all positives summing to 1). Tanh allows each action to be independently good or bad.

---

## LINES 136–195: `STDPActionEvaluator`

### `encode_state()` — Lines 152–155

```python
def encode_state(self, x, v_pop):
    proprio = np.clip(np.abs(x) / np.array([8., 3., 0.7, 3., 0.35]), 0., 1.)
    return np.concatenate([proprio, v_pop])
```

`x` = state vector: [x_pos, x_vel, pitch, pitch_vel, neck_angle] — 5 values.

**Normalization factors `[8., 3., 0.7, 3., 0.35]`:**  
Each divisor is the expected MAXIMUM of that variable:
- `8.0`: Max position ±8m from start
- `3.0`: Max velocity ±3 m/s
- `0.7`: Max pitch ±0.7 rad (±40°)
- `3.0`: Max pitch velocity ±3 rad/s
- `0.35`: Max neck angle ±0.35 rad (±20°)

`np.abs()`: Takes absolute value — treats left vs. right symmetrically. A 3m displacement left and 3m right are equally "far from center."

`np.clip(..., 0., 1.)`: Clamps to [0, 1]. If position exceeds 8m (outside normal range), don't let it go above 1.0 (which would break downstream math).

**`v_pop`**: Visual population code — 15 values encoding what the camera sees. Concatenated with proprioception to give the full 20D state.

**Why `np.abs()`?** The STDP synapse doesn't track direction — it tracks magnitude. Whether CARL is turning left or right, the synapse learns "turning is associated with this outcome." Left/right is handled by the sign of the action, not the sign of the state.

---

### `encode_action()` — Lines 157–162

```python
def encode_action(self, u):
    idx = int(np.argmin([abs(u - a) for a in self.action_map]))
    spikes = np.zeros(self.n_actions)
    spikes[idx] = 1.0
    return spikes
```

`self.action_map = [-8., -5., -2., -1., 0., 1., 2., 5., 8.]`: 9 discrete steering values (negative = left, positive = right).

**`np.argmin([abs(u - a) for a in self.action_map])`**: Finds the index of the closest discrete action to the continuous command `u`. If `u = 1.7`, the closest discrete action is `2.0` (index 6).

**One-hot encoding**: `spikes[idx] = 1.0`, all others 0. "Action 6 fired; actions 0-5 and 7-8 didn't." This is the "post-synaptic spike" pattern.

**Why discretize actions?** STDP works with discrete spikes. The continuous motor command must be quantized to one of 9 bins to create a meaningful spike pattern. 9 bins provide enough resolution for steering while keeping the network small.

---

### `update()` — Lines 164–185

```python
def update(self, xk, v_pop, uk, surprise, nm_DA):
    raw_reward  = nm_DA - surprise * 0.5
    reward = raw_reward - self.reward_baseline
    self.reward_baseline += (raw_reward - self.reward_baseline) / self.baseline_tau

    threshold = 0.15
    pre_spikes  = pre_spikes * float(surprise > threshold)
    post_spikes = post_spikes * float(surprise > threshold)

    self.synapse.step(pre_spikes, post_spikes, reward, dt=1.0)
```

**Reward computation:**
```
raw_reward = DA - 0.5 × surprise
```

- `DA`: Dopamine level (high = reward)
- `- 0.5 × surprise`: Prediction error penalty. High surprise = model was wrong = not as good as it seemed
- Combined: "How rewarding was this outcome, adjusted for how unexpected it was?"

**Baseline subtraction:**  
`reward = raw_reward - reward_baseline`

`reward_baseline` tracks the running average of `raw_reward`. Subtracting it means:
- `reward > 0`: Better than average → positive RPE → strengthen
- `reward < 0`: Worse than average → negative RPE → weaken

`reward_baseline += (raw_reward - reward_baseline) / 200.0`: Moving average with τ=200 steps. This makes "baseline" = "expected outcome over the last 200 actions" (~6.7 seconds at 30Hz).

**Surprise threshold gate:**
```python
pre_spikes  = pre_spikes * float(surprise > threshold)
```

`float(surprise > 0.15)` → 1.0 if surprising, 0.0 if not.

If `surprise ≤ 0.15`: Both pre and post spikes become ZERO → STDP computation is skipped → weights don't change.

**Why gate on surprise?** Learning should only happen when something UNEXPECTED occurred. If CARL's model perfectly predicted the outcome (`surprise ≈ 0`), there's nothing new to learn. Only update weights when the world surprised the model — that's when new information is available.

---

## LINES 207–274: `QuantumDeliberator`

### Docstring — The Concept

```python
"""
Instead of argmin(cost), each strategy is a quantum amplitude.
Interference between strategies: aligned predictions amplify,
conflicting predictions cancel. Final choice by Born rule probability.

This produces GENUINELY PROBABILISTIC decisions — not random noise,
but structured uncertainty that reflects actual ambiguity.
"""
```

**Classical decision-making (argmin):** Always pick the minimum-cost action deterministically. If two strategies tie at cost=2.5, arbitrarily pick one.

**Quantum-inspired decision-making:** Strategies with similar costs "interfere" with each other. The final probability reflects genuine ambiguity — tied strategies both get ~50% probability. Very clear winners get near-100%.

**What's "quantum-inspired"?** It uses the MATH of quantum mechanics (complex amplitudes, interference, Born rule) without actually requiring a quantum computer. This is a metaphorical model that produces better-calibrated uncertainty than argmin.

---

### `deliberate()` — Lines 222–264

```python
def deliberate(self, strategies_costs):
    costs = np.array([c for _, _, _, c in strategies_costs], dtype=float)
```

`strategies_costs`: List of tuples: `(name, u, s, cost)`. Example:
```
[("FOOD", 2.0, 0.0, 1.2),
 ("OBSTACLE", -3.0, 0.0, 0.8),
 ("BALANCED", 0.0, 0.0, 2.1)]
```

**Step 1: Normalize costs**
```python
costs_norm = costs - costs.min()
if costs_norm.max() > 1e-6:
    costs_norm /= costs_norm.max()
```

Shift by minimum (so best strategy = 0), scale by range (so worst = 1). Result: each strategy's "badness" relative to the best, in [0, 1].

Why normalize? Quantum phases are in [0, π]. We need to map costs → [0, π].

---

**Step 2: Complex amplitudes**
```python
phases = costs_norm * math.pi
amplitudes = np.exp(1j * phases)  # complex amplitudes
```

Each strategy gets a complex amplitude `A_i = e^(iθ_i)` where `θ_i = cost_normalized × π`.

- Best strategy (cost=0): `θ = 0`, `A = e^0 = 1+0j` (real, constructive)
- Worst strategy (cost=1): `θ = π`, `A = e^(iπ) = -1+0j` (real, destructive)
- Medium strategy (cost=0.5): `θ = π/2`, `A = e^(iπ/2) = 0+1j` (imaginary, neither)

This is **Euler's formula**: `e^(iθ) = cos(θ) + i·sin(θ)`.

**`1j`**: Python's imaginary unit. `np.exp(1j * phases)` creates a complex numpy array.

---

**Step 3: Interference**
```python
total_amplitude = amplitudes.sum()
coherent_probs = np.abs(amplitudes * np.conj(total_amplitude)).real
```

`amplitudes.sum()`: Sum of all complex amplitudes. If all strategies are similar (all phases ≈ 0), they CONSTRUCTIVELY INTERFERE → large total. If strategies conflict (phases spread from 0 to π), they PARTIALLY CANCEL → smaller total.

`np.conj(total_amplitude)`: Complex conjugate. If `total = a+bi`, `conj(total) = a-bi`.

`amplitudes * np.conj(total_amplitude)`: Element-wise complex multiplication. This measures how "aligned" each strategy's amplitude is with the total — the "overlap" with the consensus.

`np.abs(...).real`: Magnitude of the complex product. This is always real (though numpy returns it as complex with zero imaginary part, hence `.real`).

**Geometric interpretation:** Think of each amplitude as a unit vector in the complex plane. The total amplitude is their vector sum. The overlap of each with the total = how aligned that strategy is with the overall "direction of consensus."

---

**Step 4: Born Rule normalization**
```python
probs = coherent_probs / total_p
```

**Born Rule**: In quantum mechanics, probability = |amplitude|². Here:
```
P_i ∝ |A_i · A_total*|
```
Normalized so all probabilities sum to 1.

Why Born Rule? It naturally gives:
- Strategies strongly aligned with consensus → high probability
- Strategies opposed to consensus → low probability
- With uncertainty (multiple similar strategies) → spread probabilities

---

**Step 5: Sampling**
```python
chosen_idx = int(np.random.choice(len(strategies_costs), p=probs))
```

`np.random.choice(n, p=probs)`: Samples one index from [0, n-1] with probabilities `probs`. This is **probabilistic selection**, NOT argmax.

**Why sample rather than argmax?** If the top two strategies have probabilities [0.48, 0.46], argmax always picks strategy 0. But sampling picks strategy 1 with 46% frequency — this explores the second-best option 46% of the time, which can find novel solutions that pure exploitation misses.

---

## LINES 266–274: `decision_uncertainty()`

```python
def decision_uncertainty(self):
    last = self.history[-1]['probs']
    last = np.clip(last, 1e-8, 1.)
    entropy = float(-np.sum(last * np.log(last)))
    max_ent = float(np.log(len(last)))
    return float(entropy / max_ent)
```

**Shannon Entropy:**
```
H = -Σ p_i × log(p_i)
```

- Uniform distribution (all equal): H = log(n) — MAXIMUM uncertainty
- One strategy 100%: H = 0 — NO uncertainty

**`max_ent = log(n)`**: The maximum possible entropy for n strategies.

**`entropy / max_ent`**: Normalized entropy in [0, 1].

- 1.0 = completely uncertain (all strategies equally probable)
- 0.0 = completely certain (one strategy dominates)

**`np.clip(last, 1e-8, 1.)`**: Prevents `log(0) = -∞` error. 1e-8 is small enough to have negligible effect on entropy.

**How this is used in `carl_simulation.py`**: When uncertainty is high, CARL requests more sensory precision (boosted `sigma_ACh`), takes slower, more careful actions, and triggers an NE surge — "I'm not sure what to do, be alert."

---

## LINE 277: `import math`

```python
import math
```

Note: This import is at the BOTTOM of the file (line 277). This is unusual — normally imports go at the top. This is a **late import** used in `QuantumDeliberator.deliberate()` for `math.pi`. Python allows imports anywhere; they just add `math` to the module namespace at execution time. This is likely an oversight (should be moved to line 1) but functionally harmless because `deliberate()` is never called before this import executes.

---

## COMPLETE ALGORITHM REFERENCE

| Operation | Formula | Code | Why |
|---|---|---|---|
| Pre trace decay | `A_pre *= e^(-dt/τ_pre)` | `A_pre *= decay_pre` | Exponential forgetting |
| LTP eligibility | `E += A_pre ⊗ post × A+` | `np.outer(A_pre, post) * A_PLUS` | "Pre caused post" signal |
| LTD eligibility | `E -= pre ⊗ A_post × A-` | `np.outer(pre, A_post) * (-A_MINUS)` | "Pre arrived late" penalty |
| Weight update | `ΔW = LR × R × E` | `dW = LR * avg_reward * E` | Three-factor rule |
| Born rule prob | `P_i ∝ \|A_i · A*_total\|` | `coherent_probs = np.abs(...)` | Quantum-inspired probability |
| Shannon entropy | `H = -Σp log(p)` | `entropy / max_ent` | Uncertainty measure |
