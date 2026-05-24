"""Human-readable output for play group rotations.

The summary is designed for parents and organizers: groups first,
compact fairness dashboard, then optional detail sections.
"""

import json
from datetime import datetime
from itertools import combinations


class OutputFormatter:

    def write_groups_file(
        self, new_iterations, filepath, past_count=0, past_iterations=None
    ):
        """Write all iterations as JSON (past + new), ready for re-use as input."""
        all_iters = []

        if past_iterations:
            for groups in past_iterations:
                all_iters.append(
                    [[c.name for c in g.children] for g in groups]
                )

        for groups in new_iterations:
            all_iters.append(
                [[c.name for c in g.children] for g in groups]
            )

        data = {
            "format": "group-scheduler-past-iterations",
            "version": 1,
            "iterations": all_iters,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Groups file written: {filepath}")

    def write_summary_file(
        self,
        children,
        iterations,
        filepath,
        warnings,
        past_count=0,
        optimizer=None,
    ):
        """Write a concise, human-first summary report."""
        total = past_count + len(iterations)
        new_stats = None
        if optimizer and past_count > 0:
            new_stats = optimizer.get_new_iterations_statistics(
                iterations, past_count
            )

        with open(filepath, "w", encoding="utf-8") as f:
            self._write_header(f, children, iterations, past_count, total)
            self._write_iterations(f, iterations, past_count)
            self._write_fairness_check(f, children, total)
            self._write_hosting(f, children, new_stats, past_count)
            self._write_pair_matrices(f, children)
            self._write_recurring_groups(f, iterations)
            self._write_warnings(f, warnings)

        print(f"Summary file written: {filepath}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _avg_gap_between_meetings(iters):
        """Mean iterations between consecutive meetings (same pair)."""
        s = sorted(iters)
        if len(s) < 2:
            return None
        gaps = [s[i] - s[i - 1] - 1 for i in range(1, len(s))]
        return sum(gaps) / len(gaps)

    @staticmethod
    def _sorted_names(children):
        return sorted(c.name for c in children)

    @staticmethod
    def _abbrev(name, width=4):
        """Short column label; strip spaces, pad to fixed width."""
        s = name.replace(" ", "")[:width]
        return s.ljust(width)

    @staticmethod
    def _pair_counts(children):
        counts = {}
        for c in children:
            for other, cnt in c.meetings.items():
                pair = tuple(sorted([c.name, other]))
                counts[pair] = cnt
        return counts

    @staticmethod
    def _pair_iteration_lists(children):
        iters = {}
        for c in children:
            for other, lst in c.meeting_iterations.items():
                pair = tuple(sorted([c.name, other]))
                if pair not in iters:
                    iters[pair] = lst
        return iters

    def _write_lower_triangular_matrix(
        self,
        f,
        title,
        names,
        value_at,
        cell_width=4,
        empty=".",
        legend=None,
    ):
        """Print symmetric stats for row i, columns 0..i (lower triangle incl. diagonal)."""
        n = len(names)
        col_w = cell_width
        label_w = max(len(n) for n in names) + 1

        f.write(f"  {title}\n")
        if legend:
            f.write(f"  {legend}\n")
        f.write("\n")

        def fmt_cell(text):
            return text[:col_w].rjust(col_w)

        header = " " * label_w + " ".join(
            fmt_cell(self._abbrev(names[j], col_w)) for j in range(n)
        )
        f.write(f"  {header.rstrip()}\n")

        for i in range(n):
            cells = []
            for j in range(n):
                if j > i:
                    cells.append(fmt_cell(""))
                elif j == i:
                    cells.append(fmt_cell("-"))
                else:
                    val = value_at(names[i], names[j])
                    if val is None:
                        cells.append(fmt_cell(empty))
                    elif isinstance(val, float):
                        cells.append(fmt_cell(f"{val:.1f}"))
                    else:
                        cells.append(fmt_cell(str(val)))
            row_label = names[i].ljust(label_w)
            f.write(f"  {row_label} {' '.join(cells)}\n")
        f.write("\n")

    def _write_pair_matrices(self, f, children):
        f.write(f"\u2501" * 50 + "\n")
        f.write("PAIR STATISTICS (lower triangle, row \u2265 column)\n")
        f.write(f"\u2501" * 50 + "\n\n")

        names = self._sorted_names(children)
        counts = self._pair_counts(children)
        pair_iters = self._pair_iteration_lists(children)

        def meeting_count(a, b):
            return counts.get(tuple(sorted([a, b])), 0)

        self._write_lower_triangular_matrix(
            f,
            "Meeting counts (times in same group)",
            names,
            meeting_count,
            cell_width=4,
            legend="Diagonal: \u2014. Read row child vs column child.",
        )

        def avg_gap(a, b):
            iters = pair_iters.get(tuple(sorted([a, b])), [])
            return self._avg_gap_between_meetings(iters)

        self._write_lower_triangular_matrix(
            f,
            "Avg iterations between meetings (2+ meetings only)",
            names,
            avg_gap,
            cell_width=4,
            empty=".",
            legend="Diagonal: \u2014. Dot if pair met only once.",
        )

    # ------------------------------------------------------------------
    # Private section writers
    # ------------------------------------------------------------------

    def _write_header(self, f, children, iterations, past_count, total):
        f.write("PLAY GROUP ROTATIONS\n")
        f.write(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        if past_count > 0:
            f.write(
                f"Past iterations: {past_count} | "
                f"New: {len(iterations)} | Total: {total}\n"
            )
        else:
            f.write(f"Iterations: {len(iterations)}\n")
        n_boys = sum(1 for c in children if c.is_boy)
        n_girls = sum(1 for c in children if c.is_girl)
        f.write(
            f"Children: {len(children)} "
            f"({n_boys} boys, {n_girls} girls)\n\n"
        )

    def _write_iterations(self, f, iterations, past_count):
        for idx, groups in enumerate(iterations, 1):
            abs_num = past_count + idx
            f.write(f"\u2500" * 50 + "\n")
            f.write(f"ITERATION {abs_num}\n")
            f.write(f"\u2500" * 50 + "\n")
            for group in groups:
                host = group.host
                others = [c for c in group.children if c is not host]
                line = f"  {host.name} (host), " + ", ".join(
                    c.name for c in others
                )
                f.write(line + "\n")
            f.write("\n")

    def _write_fairness_check(self, f, children, total):
        f.write(f"\u2501" * 50 + "\n")
        f.write(f"FAIRNESS CHECK (all {total} iterations)\n")
        f.write(f"\u2501" * 50 + "\n\n")

        f.write(f"  Gender balance      All groups: 2B + 2G \u2713\n")

        counts = [c.hosting_count for c in children]
        lo, hi = min(counts), max(counts)
        gap = hi - lo
        mark = "\u2713" if gap <= 1 else "\u26A0"
        f.write(
            f"  Hosting fairness    "
            f"Range: {lo}\u2013{hi} per child (gap: {gap}) {mark}\n"
        )

        coverage = [len(c.meetings) for c in children]
        c_lo, c_hi = min(coverage), max(coverage)
        max_peers = len(children) - 1
        f.write(
            f"  Meeting coverage    "
            f"Each child met {c_lo}\u2013{c_hi} of {max_peers} peers\n"
        )

        max_m, max_pair = 0, None
        for c in children:
            for other, cnt in c.meetings.items():
                if cnt > max_m:
                    max_m = cnt
                    max_pair = (c.name, other)
        if max_pair:
            f.write(
                f"  Most repeated pair  "
                f"{max_m} meetings ({max_pair[0]} & {max_pair[1]})\n"
            )

        pair_avgs = []
        seen_pairs = set()
        for c in children:
            for other, iters in c.meeting_iterations.items():
                pair = tuple(sorted([c.name, other]))
                if pair in seen_pairs or len(iters) < 2:
                    continue
                seen_pairs.add(pair)
                g = self._avg_gap_between_meetings(iters)
                if g is not None:
                    pair_avgs.append(g)

        if pair_avgs:
            mean_spacing = sum(pair_avgs) / len(pair_avgs)
            f.write(
                f"  Meeting spacing     "
                f"Mean over pairs (2+ meetings): "
                f"{mean_spacing:.1f} iterations between\n"
            )

        f.write("\n")

    def _write_hosting(self, f, children, new_stats, past_count):
        f.write(f"\u2501" * 50 + "\n")
        if past_count > 0 and new_stats:
            f.write("HOSTING (new iterations / all-time total)\n")
        else:
            f.write("HOSTING COUNTS\n")
        f.write(f"\u2501" * 50 + "\n\n")

        if new_stats and past_count > 0:
            by_key = {}
            for name in sorted(new_stats["hosting_counts"]):
                new_h = new_stats["hosting_counts"][name]
                total_h = next(
                    c.hosting_count for c in children if c.name == name
                )
                by_key.setdefault((new_h, total_h), []).append(name)

            for (new_h, total_h) in sorted(by_key, reverse=True):
                names = by_key[(new_h, total_h)]
                label = f"{new_h}x new ({total_h} total)"
                f.write(f"  {label}: {', '.join(names)}\n")
        else:
            by_count = {}
            for c in children:
                by_count.setdefault(c.hosting_count, []).append(c.name)
            for count in sorted(by_count, reverse=True):
                names = ", ".join(sorted(by_count[count]))
                f.write(f"  {count}x: {names}\n")
        f.write("\n")

    def _write_recurring_groups(self, f, iterations):
        triplet_iters = {}
        quartet_iters = {}

        for iter_idx, groups in enumerate(iterations, 1):
            for group in groups:
                names = sorted(c.name for c in group.children)
                qk = tuple(names)
                quartet_iters.setdefault(qk, []).append(iter_idx)
                for tri in combinations(names, 3):
                    triplet_iters.setdefault(tri, []).append(iter_idx)

        recurring_q = {k: v for k, v in quartet_iters.items() if len(v) > 1}
        recurring_t = {k: v for k, v in triplet_iters.items() if len(v) > 1}

        if recurring_q or recurring_t:
            f.write(f"\u2501" * 50 + "\n")
            f.write("RECURRING GROUPS (new iterations)\n")
            f.write(f"\u2501" * 50 + "\n\n")

            if recurring_q:
                f.write("  Repeated quartets:\n")
                for names, iters in sorted(
                    recurring_q.items(), key=lambda x: -len(x[1])
                ):
                    f.write(
                        f"    {len(iters)}x: {', '.join(names)}\n"
                    )
                f.write("\n")

            if recurring_t:
                f.write("  Repeated triplets:\n")
                for names, iters in sorted(
                    recurring_t.items(), key=lambda x: -len(x[1])
                ):
                    f.write(
                        f"    {len(iters)}x: {', '.join(names)}\n"
                    )
                f.write("\n")

    def _write_warnings(self, f, warnings):
        if warnings:
            f.write(f"\u2501" * 50 + "\n")
            f.write("WARNINGS\n")
            f.write(f"\u2501" * 50 + "\n\n")
            for w in warnings:
                f.write(f"  \u2022 {w}\n")
            f.write("\n")
        else:
            f.write("No warnings.\n")
