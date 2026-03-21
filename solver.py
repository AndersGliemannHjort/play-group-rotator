"""CP-SAT constraint solver for play group assignments.

Uses Google OR-Tools to find provably optimal group assignments.
Hard constraints are structural guarantees (never violated), while
soft objectives guide the solver toward the fairest solution.
"""

import os

try:
    from ortools.sat.python import cp_model
except ImportError:
    raise ImportError(
        "ortools is required. Install with: pip install ortools"
    )


class PlayGroupSolver:
    """Assigns children to balanced play groups using OR-Tools CP-SAT.

    Hard constraints (always satisfied):
      - 6 groups of exactly 4 children
      - 2 boys + 2 girls per group
      - Every child in exactly one group
      - Post-iteration hosting counts differ by at most 1

    Soft objectives (minimized):
      - Repeated pairings, quadratic in prior meeting count
      - Same-gender repeats weighted 2x (scarcer meeting opportunities)
      - Repeated triplets and quartets (quartet penalty stronger than triplet)
      - Short hosting breaks (prefer 3+ iterations between hosting)
    """

    TRIPLET_WEIGHT = 8
    QUARTET_WEIGHT = 50

    def solve(
        self,
        children,
        iteration_num,
        triplet_history,
        quartet_history,
    ):
        """Find optimal group assignments for one iteration.

        Args:
            children: list of Child objects with current meeting/hosting state.
            iteration_num: absolute iteration number (1-based).
            triplet_history: dict sorted 3-tuple of names -> list of iteration nums.
            quartet_history: dict sorted 4-tuple of names -> list of iteration nums.

        Returns:
            List of 6 Group objects (host first in each), or None if infeasible.
        """
        model = cp_model.CpModel()
        n = len(children)
        num_groups = n // 4
        boys = [i for i, c in enumerate(children) if c.is_boy]
        girls = [i for i, c in enumerate(children) if c.is_girl]

        # --- Decision variables ---

        x = {
            (i, g): model.NewBoolVar(f"x_{i}_{g}")
            for i in range(n)
            for g in range(num_groups)
        }

        host = {
            (i, g): model.NewBoolVar(f"h_{i}_{g}")
            for i in range(n)
            for g in range(num_groups)
        }

        is_host = [model.NewBoolVar(f"ih_{i}") for i in range(n)]

        # --- Hard constraints ---

        # Each child in exactly one group
        for i in range(n):
            model.Add(sum(x[i, g] for g in range(num_groups)) == 1)

        # Group size and gender balance
        for g in range(num_groups):
            model.Add(sum(x[i, g] for i in range(n)) == 4)
            model.Add(sum(x[i, g] for i in boys) == 2)
            model.Add(sum(x[i, g] for i in girls) == 2)

        # Hosting: host must be in group, one host per group
        for i in range(n):
            for g in range(num_groups):
                model.Add(host[i, g] <= x[i, g])

        for g in range(num_groups):
            model.Add(sum(host[i, g] for i in range(n)) == 1)

        for i in range(n):
            model.Add(
                sum(host[i, g] for g in range(num_groups)) == is_host[i]
            )

        # Hosting fairness: after this iteration, all counts within 1 of each other.
        # post[i] = past[i] + is_host[i]; require |post[i] - post[j]| <= 1.
        past = [c.hosting_count for c in children]
        for i in range(n):
            for j in range(i + 1, n):
                d = past[i] - past[j]
                model.Add(is_host[i] - is_host[j] <= 1 - d)
                model.Add(is_host[j] - is_host[i] <= 1 + d)

        # Symmetry breaking: groups are interchangeable, so fix child 0's label
        model.Add(x[0, 0] == 1)

        name_to_idx = {children[i].name: i for i in range(n)}

        # --- Soft objective: minimize repeated meetings + hosting break cost ---

        cost = []
        var_tag = [0]

        def next_tag():
            var_tag[0] += 1
            return var_tag[0]

        # Pairwise meeting penalty (count + recency)
        for i in range(n):
            for j in range(i + 1, n):
                m = children[i].meetings.get(children[j].name, 0)
                if m > 0:
                    t = model.NewBoolVar(f"t_{i}_{j}")
                    for g in range(num_groups):
                        model.Add(t >= x[i, g] + x[j, g] - 1)

                    iters = children[i].meeting_iterations.get(
                        children[j].name, [0]
                    )
                    gap = iteration_num - max(iters)
                    recency = max(0, 4 - gap)

                    w = m * m + recency * recency
                    if children[i].is_boy == children[j].is_boy:
                        w *= 2
                    cost.append(w * t)

        # Triplet penalty: same three children in one group again
        for tri_names, iters in triplet_history.items():
            if not iters:
                continue
            idxs = [name_to_idx.get(nm) for nm in tri_names]
            if None in idxs:
                continue
            a, b, cidx = sorted(idxs)
            u = model.NewBoolVar(f"tri_{next_tag()}")
            for g in range(num_groups):
                model.Add(
                    u >= x[a, g] + x[b, g] + x[cidx, g] - 2
                )
            cnt = len(iters)
            gap = iteration_num - max(iters)
            recency = max(0, 4 - gap)
            w = self.TRIPLET_WEIGHT * (cnt * cnt + recency * recency)
            cost.append(w * u)

        # Quartet penalty: same four children in one group again (stronger)
        for q_names, iters in quartet_history.items():
            if not iters:
                continue
            idxs = [name_to_idx.get(nm) for nm in q_names]
            if None in idxs:
                continue
            a, b, cidx, d = sorted(idxs)
            u = model.NewBoolVar(f"qua_{next_tag()}")
            for g in range(num_groups):
                model.Add(
                    u >= x[a, g] + x[b, g] + x[cidx, g] + x[d, g] - 3
                )
            cnt = len(iters)
            gap = iteration_num - max(iters)
            recency = max(0, 4 - gap)
            w = self.QUARTET_WEIGHT * (cnt * cnt + recency * recency)
            cost.append(w * u)

        # Hosting break penalty: discourage hosting again soon
        for i in range(n):
            if children[i].hosting_iterations:
                gap = iteration_num - max(children[i].hosting_iterations) - 1
                if gap < 3:
                    cost.append((3 - gap) ** 2 * is_host[i])

        if cost:
            model.Minimize(sum(cost))

        # --- Solve ---

        solver = cp_model.CpSolver()
        # Longer limit improves quality: solver often stops at FEASIBLE under a
        # Default 60s per iteration; override with PLAY_GROUP_SOLVER_SECONDS.
        limit = float(os.environ.get("PLAY_GROUP_SOLVER_SECONDS", "60"))
        solver.parameters.max_time_in_seconds = max(1.0, limit)
        solver.parameters.num_workers = 8
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None

        label = "optimal" if status == cp_model.OPTIMAL else "feasible"
        obj = f", cost={int(solver.ObjectiveValue())}" if cost else ""
        print(f"({label}{obj}, {solver.WallTime():.1f}s)", end=" ")

        # --- Extract solution ---

        from group_optimizer import Group

        groups = []
        for g in range(num_groups):
            group_host = None
            members = []
            for i in range(n):
                if solver.Value(x[i, g]):
                    if solver.Value(is_host[i]):
                        group_host = children[i]
                    else:
                        members.append(children[i])
            ordered = ([group_host] if group_host else []) + members
            groups.append(Group(ordered))

        return groups
