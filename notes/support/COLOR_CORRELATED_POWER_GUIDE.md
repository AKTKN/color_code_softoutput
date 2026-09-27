# Power-guide color-correlated decoding

This 2026-09-27 update supersedes the guide-probability rule in
`COLOR_CORRELATED_ORIGINAL_DEM.md`. Candidate scheduling and original mechanism
index alignment are retained.

For an original X/Z DEM source probability `q_i`, guide set `G`, and positive
finite constructor option `color_correlated_b`, guided candidate generation uses

```text
q_i^(G) = q_i^(1/b)   if i is in G
          q_i         otherwise.
```

The implementation caps values that round to one at `1 - 1e-14` for finite
matching weights. `b=1` is the unchanged prior; `b>1` increases probabilities
strictly between zero and one. This is an imposed guide heuristic, not a
Bayesian posterior or calibrated conditional probability.

Only stage 1 receives the updated probabilities. Its existing symbolic
decomposition supplies the parity probability of every affected column:

```text
p_a^(G) = (1 - product_{i in B(a)} (1 - 2 m_ai q_i^(G))) / 2,
```

where `m_ai` is the symbolic column's source multiplier. Stage-2 matrix and
probabilities are the ordinary target-color decomposition without changes.
All candidates, including the ordinary three, are mapped to the original X/Z
DEM source order and ranked by unchanged log odds
`sum_i correction_i log((1-q_i)/q_i)`. The color-correlated decoder requires
`color_correlated_weight_basis: original_dem` and uses it by default.

The decoder caches the symbolic stage-1 source maps and bounded guide-specific
stage-1 probability arrays and PyMatching objects. It also keeps one original
stage-2 matcher per color and an original-source correction map and weight
vector per decoder instance. The caches are local to the decoder instance and
do not change the base DEM. An independent full-redecomposition oracle checks
the stage-1 probabilities for multiple guides and all colors. A bounded
12-guide d=5, five-round uniform-noise timing measured about 0.0019 s for the
cached symbolic calculation versus 0.4047 s for full re-decomposition; this
is a subroutine comparison, not a whole-decoder speedup claim.

Saved color-correlated runs made under earlier guide rules cannot be
reinterpreted using this implementation.
