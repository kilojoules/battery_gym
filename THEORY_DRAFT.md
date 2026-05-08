# When does forecast-handling translate uniformly across capacity?

**Date:** 2026-05-08
**Goal:** derive a sufficient condition under which the argmax of the
sizing curve is invariant to the choice of dispatch policy. Identify
what breaks the condition. This converts the paper from "we observed a
null" to "we proved when the null is principled and probed the
boundary."

## Setup

- $b$: battery energy capacity (MWh). Power capacity $b_P$ fixed.
- $\pi$: dispatch policy (a measurable map from $(\text{state},
  \text{forecast})$ to action).
- $R(b, \pi)$: expected lifetime revenue under policy $\pi$ given
  capacity $b$, scored on realized prices.
- $C(b) = c_E b + c_P b_P$: linear-in-$b$ CAPEX with a fixed PCS
  component.
- $N(b, \pi)$: expected replacement count (integer-valued, weakly
  decreasing in $b$ for any reasonable degradation model).
- $K_R$: per-replacement battery cost (proportional to $b$, energy
  component only).
- $\mathrm{NPV}(b, \pi) = R(b, \pi) - c_E b - c_P b_P - N(b, \pi) \cdot K_R(b)$.

Optimal sizing: $b^*(\pi) = \arg\max_b \mathrm{NPV}(b, \pi)$.

## Sufficient condition for argmax invariance

**Assumption A1** (regular CAPEX). $C(b)$ is linear in $b$.

**Assumption A2** (revenue concave, plateaus). $R(b, \pi)$ is
non-decreasing and concave in $b$, with a plateau capacity
$b_{\mathrm{sat}}(\pi)$ such that $R'(b, \pi) \to 0$ for
$b \geq b_{\mathrm{sat}}(\pi)$.

**Assumption A3** (degradation step function). $N(b, \pi)$ is piecewise
constant in $b$ between replacement-count jumps. The jumps occur at the
same $b$ values for both policies whenever cycling depth is determined
by capacity (i.e., when $b$ controls the depth, not the policy).

**Theorem (Argmax invariance — informal).** Under A1-A3, if the two
policies $\pi_1, \pi_2$ satisfy:

1. $R(b, \pi_2) = R(b, \pi_1) + \Delta(b)$ with $\Delta(b)$ constant in
   $b$ in a neighborhood of $b^*(\pi_1)$ — i.e., the lift is
   *capacity-independent* at the argmax.
2. $N(b, \pi_1) = N(b, \pi_2)$ in the same neighborhood.

Then $b^*(\pi_1) = b^*(\pi_2)$.

**Sketch.** From the first-order condition,
$\partial_b \mathrm{NPV}(b^*, \pi) = 0$ implies
$R'(b^*, \pi) = c_E + \partial_b [N(b^*, \pi) K_R(b^*)]$
(the FOC, treating $N$ as locally constant past jump points).

If $\Delta'(b^*) = 0$ (assumption 1), then $R'(b^*, \pi_1) =
R'(b^*, \pi_2)$. With $N$ identical in the neighborhood (assumption 2),
the FOC is identical, so the same $b^*$ solves both.

Concavity of $R$ ensures the FOC has a unique stationary point; the
argmaxes coincide. $\square$

**Corollary (when invariance fails).** If $b_{\mathrm{sat}}(\pi_1) \neq
b_{\mathrm{sat}}(\pi_2)$ — i.e., one policy continues extracting
revenue from capacity past where the other has plateaued — then
$\Delta'(b)$ is non-zero in the relevant range, and the argmaxes
generically differ.

## The diurnal-AR(1) regime satisfies the condition

In a single-period-per-day arbitrage problem (the synthetic regime in
Pilot S1):

- The dominant arbitrage opportunity is the daily peak-trough spread.
- Both policies extract this opportunity once $b$ exceeds the daily
  energy throughput threshold $b_{\mathrm{sat}}^{(1\text{day})}$.
- Past $b_{\mathrm{sat}}^{(1\text{day})}$, neither policy has additional
  multi-day arbitrage to exploit (no inter-day price structure beyond
  AR(1) noise).
- Consequently $b_{\mathrm{sat}}(\pi_1) = b_{\mathrm{sat}}(\pi_2) =
  b_{\mathrm{sat}}^{(1\text{day})}$, and $\Delta(b)$ flattens past this
  point.
- The empirical revenue curves in Figure 2 (right panel) confirm this:
  the two policies' revenue curves are nearly parallel from $b \approx 4$
  MWh upward.

The Pilot S1 invariance result is *expected* under the theorem — not
fortuitous.

## Where the condition breaks (testable)

**Multi-period structure.** If price has variance at timescales $\tau >
1$ day (e.g., weekend dips, weather-driven price clustering), bigger
batteries can exploit longer-window arbitrage. Forecast errors at
timescales near $\tau$ differentially hurt the deterministic policy
(which commits based on a single noisy multi-day forecast). The
stochastic policy hedges across scenarios, recovering more of the
multi-day arbitrage value. So:

$$b_{\mathrm{sat}}(\pi_{\mathrm{sto}}) > b_{\mathrm{sat}}(\pi_{\mathrm{det}})$$

and $\Delta'(b) > 0$ in the gap, producing $b^*(\pi_{\mathrm{sto}}) >
b^*(\pi_{\mathrm{det}})$.

**Rare price events (price spikes).** If a small fraction of hours
contribute disproportionate revenue (ERCOT 2021-style), forecast
miscalls of a single spike are equivalent to a multi-day arbitrage
miss. Same mechanism.

**Curtailment-binding regimes.** When battery is the marginal asset in
an HPP (high renewable penetration), forecast errors translate
directly to capacity shortfalls. The marginal value of capacity becomes
policy-dependent.

In each case, the diagnostic is the same: compute $b_{\mathrm{sat}}$
empirically per policy. If they differ, expect a sizing shift.

## Diagnostic test (empirical, cheap)

For a given price process and dispatch policy, define
$b_{\mathrm{sat}}^{\epsilon}(\pi) = \inf \{b : R(b+\delta, \pi) -
R(b, \pi) < \epsilon \cdot \delta \text{ for all } \delta > 0\}$
for small $\epsilon$.

**Empirically:** sweep $b$ on a fine linear grid; estimate $R'(b, \pi)$
via finite differences; report the smallest $b$ where $R'$ drops below
threshold. Bootstrap CIs across forecast seeds.

Run this for $\pi_{\mathrm{det}}$ and $\pi_{\mathrm{sto}}$. If
$b_{\mathrm{sat}}^{\epsilon}$ overlaps within CIs across policies,
sizing-invariance is structural for that price process. If not, the
gap between them is a quantitative measure of how much the academic-
tool deterministic-LP-inner-dispatch approximation costs in sizing
recommendations.

## What this gives the paper

1. **A theorem with a clear sufficient condition.** Converts the
   empirical observation in Pilot S1 into a falsifiable claim with a
   specified breaking condition.
2. **A regime characterization.** Synthetic AR(1) is the proof case;
   ERCOT 2021-2023 is the boundary probe.
3. **Both empirical outcomes are publishable.** Invariance survives on
   ERCOT $\to$ academic-tool convention validated more broadly. Invariance
   breaks on ERCOT $\to$ the gap is the paper.
4. **A diagnostic that practitioners can compute on their own data.**
   $b_{\mathrm{sat}}^{\epsilon}$ overlap test, no theory required to
   apply.

## Caveats and limitations

- The theorem treats $N(b, \pi)$ as locally constant; the
  step-function discreteness can mask continuous shifts. Need a
  finer-grained replacement model (or skip replacement entirely and
  use a continuous SoH-decay model) to fully formalize.
- Concavity of $R$ in $b$ is assumed; if $R$ is non-concave (e.g.,
  multimodal due to discrete arbitrage strategies), the FOC argument
  fails. Hard to construct a real counterexample, but it's worth
  flagging.
- "Capacity-independent lift" $\Delta'(b) = 0$ is a strong condition;
  in practice we'd test this empirically rather than analytically.
- The theorem doesn't tell us *why* a particular price process has
  $\Delta'(b) = 0$ — it only relates that property to the argmax
  invariance. The mechanistic step (showing $\Delta$ flattens because
  both policies saturate at the same capacity) is content the paper
  argues empirically.

## Self-test: does this hold up?

Yes, the structure is right. Two informal-but-clean equations carry the
load:

1. $b^*(\pi_1) = b^*(\pi_2)$ iff FOC residual is the same at both
   optima, which (under shared CAPEX and replacement structure)
   reduces to $R'(b^*, \pi_1) = R'(b^*, \pi_2)$, which (under shared
   plateau) is automatic.
2. The plateau is shared iff there's no arbitrage opportunity past
   $b_{\mathrm{sat}}$ that one policy can exploit and the other
   cannot. This requires single-period structure or multi-period
   structure that both policies handle equally well.

The condition is non-trivial (it can fail) and testable (compute
$b_{\mathrm{sat}}$ empirically). It earns a "lemma" or "proposition"
slot in the paper, not a "theorem" — the assumptions are loose and the
proof is a sketch — but it's a real theoretical contribution that
upgrades the paper from "we ran an experiment" to "we proved the
condition under which our experiment was a sanity check, and probed
its boundary on real data."

## Next step

Skip ERCOT integration today. Tomorrow: write the proposition + sketch
into paper.tex as a new section. If the framing holds up under fresh
eyes, do the ERCOT extension. If it falls apart on re-reading, that's
diagnostic — drop the rework, accept (1) withdraw.
