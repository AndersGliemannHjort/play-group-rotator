# play-group-rotator

CLI tool that assigns 24 children (12 boys, 12 girls) into 6 balanced groups of
4 per "iteration" (a weekly play-group meeting), across multiple iterations,
maximizing diversity of who meets whom and keeping hosting duties fair.

## Usage

```
python main.py <iterations>   # 1-12 new iterations per run
```

Reads `input/names_gender.json` (24 children) and, if present,
`input/past_iterations.json` (history to replay). Writes
`output/Play_groups_*.json` and `output/Summary_*.txt`. Copy the groups file
back into `input/past_iterations.json` before the next run.

`replit.md` is stale — it describes an older weighted-backtracking design
(`constraint_solver.py`, `weights_config.json`) that no longer exists. Ignore it.

## Architecture

- `child_manager.py` — loads/validates children, `Child` tracks per-child
  meeting/hosting history.
- `group_optimizer.py` — orchestration: calls the solver, validates output,
  updates running statistics (meetings, triplet/quartet history, hosting).
- `solver.py` — the actual optimization: Google OR-Tools **CP-SAT**. Hard
  constraints (group size, 2B+2G, one host per group, hosting fairness ±1)
  are guaranteed; a soft objective (quadratic in repeat-meeting count and
  recency, weighted more heavily for triplets/quartets/same-gender repeats)
  is minimized within a time budget (`PLAY_GROUP_SOLVER_SECONDS`, default 60s).
- `output_formatter.py` — writes the JSON groups file and a human-readable
  summary (hosting fairness, pair-meeting matrix, recurring-group detection).

`main.py` solves iterations **one at a time, sequentially**: each iteration is
fully solved and locked in before the next is modeled, using only the history
available at that point.

## Tried and reverted: joint multi-iteration solving (2026-08-01)

**Motivation:** the user observed occasional repeated triplets/quartets when
generating large batches (5-12 iterations per run). The sequential solver is
a greedy, horizon-1 strategy — iteration *k* can't know what would make
iteration *k+1..N* easier, so it can spend combinatorial "diversity budget"
in ways that force later iterations into repeats.

**What was built:** a full rewrite of `solver.py` to solve all N requested
iterations **together** in one CP-SAT model (`x[i,g,k]` indexed by
iteration `k`), so the solver could trade off early-iteration choices
against later diversity needs. This included:
- A "running-total, charged per-occurrence" cost formula that provably
  collapses to the original per-iteration formula at N=1 (verified both
  algebraically and empirically — an old greedy solution, replayed through
  the new formula, scored exactly the value implied by summing its own
  original per-iteration costs).
- Stronger symmetry breaking (canonical group-labeling per iteration) since
  the original single-child-pin trick doesn't scale across a multi-iteration
  model — group-label symmetry compounds multiplicatively across iterations.
- A warm-start hint: since the joint model alone performed *worse* than
  plain greedy, it was seeded by quickly running the greedy sequential
  solve internally first and feeding that solution to CP-SAT via `AddHint`.

**Why it was reverted — it doesn't work in practice:**

Even after symmetry breaking and warm-starting, the joint model could not
reliably beat the plain greedy sequential baseline within any practical time
budget:

| Batch | Greedy (sequential) | Joint (with hint) |
|---|---|---|
| N=4, ~4 min budget | cost 893, 0 repeats | cost 892-914 (noisy), 0 repeats |
| N=8, 8 min budget | cost 2358, 0 repeats | cost 2390, **2 repeated triplets** |
| N=4, 15 min budget | cost 893 | cost 902 — plateaued at 907 by **8 seconds**, then **zero improvement for the remaining ~12 minutes** |

Root causes:
1. **The search plateaus almost immediately and does not escape.** The
   15-minute run's own solver-reported optimality gap stayed at 70% — CP-SAT
   itself has no confidence the plateaued value is near-optimal, it simply
   stops finding improving moves. This is not a "needs more time" problem.
2. **Model size.** Extending the per-iteration quadratic repeat-cost formula
   across a batch requires CP-SAT-native quadratic terms
   (`AddMultiplicationEquality`) for every tracked pair *per iteration*,
   since CP-SAT has no native quadratic objective. This produces thousands
   of auxiliary variables (running totals, squared-cost gates, windowed
   AND-reifications for recency), and that machinery appears to defeat
   CP-SAT's LNS/local-search repair moves — they can't find productive
   neighborhoods to explore from the hinted starting point.
3. **A real correctness gap, not just a performance one:** to keep the model
   tractable, only triplets/quartets with *pre-existing* history were
   tracked (mirroring the original code). That's a safe simplification for
   quartets (a repeat requires 6 pairs to also repeat, already penalized),
   but not for triplets (only 3 pairs) — three pairs with no prior history
   can cheaply repeat together within the same batch, forming a *new*
   repeated triplet the model never penalized. This is what produced the 2
   repeated triplets in the N=8 test above.

**If this is revisited**, the loose lower bounds and total stall suggest
the fix isn't more time or a better hint — it's a fundamentally lighter
objective encoding that avoids the per-pair-per-iteration quadratic
auxiliary-variable blowup, or a different search strategy entirely (e.g.
manual large-neighborhood search re-solving small windows of adjacent
iterations with the existing single-iteration CP-SAT model, rather than one
giant joint model). The simpler, cheaper lever that was *not* tried: just
raising `PLAY_GROUP_SOLVER_SECONDS` for large batches to give the existing
per-iteration solver more time on the specific iterations most likely to
produce repeats.
