"""Group optimization orchestration.

Thin coordination layer between the CP-SAT solver and the rest of the system.
Owns the Group data class, manages child statistics updates, and validates output.
"""

from itertools import combinations


class Group:
    """A play group of 4 children. The first child is the host."""

    def __init__(self, children):
        self.children = children
        self.host = children[0] if children else None

    def get_boys(self):
        return [c for c in self.children if c.is_boy]

    def get_girls(self):
        return [c for c in self.children if c.is_girl]

    def __str__(self):
        names = [c.name for c in self.children]
        host = self.host.name if self.host else "None"
        return f"Group(host={host}, members={names})"


class GroupOptimizer:
    """Orchestrates iterative play group generation."""

    def __init__(self):
        from solver import PlayGroupSolver

        self.solver = PlayGroupSolver()
        self.warnings = []
        self.triplet_history = {}
        self.quartet_history = {}

    def create_iteration(self, children, iteration_num, previous_iterations):
        """Create optimal groups for one iteration and update child statistics."""
        groups = self.solver.solve(
            children,
            iteration_num,
            self.triplet_history,
            self.quartet_history,
        )
        if not groups:
            self.warnings.append(
                f"Iteration {iteration_num}: no feasible solution found"
            )
            return None

        if not self._validate(groups, iteration_num):
            return None

        self._update_statistics(groups, iteration_num)
        return groups

    def process_past_iterations(self, children, past_iterations):
        """Replay past iterations to rebuild child statistics."""
        for iteration_num, groups in enumerate(past_iterations, 1):
            self._update_statistics(groups, iteration_num)

    def _update_statistics(self, groups, iteration_num):
        for group in groups:
            if group.host:
                group.host.hosting_count += 1
                group.host.hosting_iterations.append(iteration_num)
            for c1 in group.children:
                for c2 in group.children:
                    if c1 is not c2:
                        c1.meetings[c2.name] = (
                            c1.meetings.get(c2.name, 0) + 1
                        )
                        c1.meeting_iterations.setdefault(
                            c2.name, []
                        ).append(iteration_num)

            names = sorted(c.name for c in group.children)
            for tri in combinations(names, 3):
                self.triplet_history.setdefault(tri, []).append(
                    iteration_num
                )
            self.quartet_history.setdefault(tuple(names), []).append(
                iteration_num
            )

    def _validate(self, groups, iteration_num):
        if len(groups) != 6:
            self.warnings.append(
                f"Iteration {iteration_num}: expected 6 groups, got {len(groups)}"
            )
            return False

        all_names = []
        for i, g in enumerate(groups, 1):
            if len(g.children) != 4:
                self.warnings.append(
                    f"Iteration {iteration_num}, group {i}: "
                    f"expected 4 children, got {len(g.children)}"
                )
                return False
            b, gl = len(g.get_boys()), len(g.get_girls())
            if b != 2 or gl != 2:
                self.warnings.append(
                    f"Iteration {iteration_num}, group {i}: "
                    f"{b}B+{gl}G (expected 2B+2G)"
                )
            all_names.extend(c.name for c in g.children)

        if len(all_names) != len(set(all_names)):
            self.warnings.append(
                f"Iteration {iteration_num}: duplicate children in groups"
            )
            return False
        if len(all_names) != 24:
            self.warnings.append(
                f"Iteration {iteration_num}: "
                f"expected 24 children, got {len(all_names)}"
            )
            return False
        return True

    def get_new_iterations_statistics(self, new_iterations, past_iteration_count):
        """Compute hosting and meeting stats for new iterations only."""
        stats = {"hosting_counts": {}, "meeting_matrix": {}}

        all_names = set()
        for groups in new_iterations:
            for group in groups:
                for child in group.children:
                    all_names.add(child.name)

        for name in all_names:
            stats["hosting_counts"][name] = 0
            stats["meeting_matrix"][name] = {}

        for groups in new_iterations:
            for group in groups:
                if group.host:
                    stats["hosting_counts"][group.host.name] += 1
                for c1 in group.children:
                    for c2 in group.children:
                        if c1 is not c2:
                            d = stats["meeting_matrix"][c1.name]
                            d[c2.name] = d.get(c2.name, 0) + 1

        return stats
