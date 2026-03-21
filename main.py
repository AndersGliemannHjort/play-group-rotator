#!/usr/bin/env python3
"""Play Group Rotation Optimizer.

Assigns 24 children (12 boys, 12 girls) into 6 balanced groups of 4,
using constraint programming to maximize meeting diversity and hosting
fairness across multiple iterations.

Usage: python main.py <number_of_iterations>
"""

import sys
import os
import argparse

from child_manager import ChildManager
from group_optimizer import GroupOptimizer
from output_formatter import OutputFormatter
from html_report import generate_html_report


def validate_input_files():
    input_dir = "input"
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    names_file = os.path.join(input_dir, "names_gender.json")
    if not os.path.exists(names_file):
        print(f"Error: Required file '{names_file}' not found.")
        sys.exit(1)

    past_file = os.path.join(input_dir, "past_iterations.json")
    return names_file, past_file if os.path.exists(past_file) else None


def main():
    parser = argparse.ArgumentParser(
        description="Optimize play group rotations using constraint programming"
    )
    parser.add_argument(
        "iterations", type=int, help="Number of iterations to generate (1-12)"
    )
    args = parser.parse_args()

    if not 1 <= args.iterations <= 12:
        print("Error: iterations must be between 1 and 12.")
        sys.exit(1)

    names_file, past_file = validate_input_files()
    os.makedirs("output", exist_ok=True)

    try:
        manager = ChildManager()
        children = manager.load_children_from_file(names_file)
        manager.validate_children(children)

        optimizer = GroupOptimizer()

        past_iterations = []
        past_count = 0
        if past_file:
            past_iterations = manager.load_past_iterations(past_file, children)
            past_count = len(past_iterations)
            optimizer.process_past_iterations(children, past_iterations)
            print(f"Loaded {past_count} past iteration(s)")

        print(f"Generating {args.iterations} new iteration(s)...")
        new_iterations = []

        for i in range(1, args.iterations + 1):
            abs_num = past_count + i
            print(f"  Solving iteration {abs_num}...", end=" ", flush=True)
            groups = optimizer.create_iteration(
                children, abs_num, past_iterations + new_iterations
            )
            if not groups:
                print("FAILED")
                print(
                    f"Error: could not find valid groups for iteration {abs_num}"
                )
                sys.exit(1)
            new_iterations.append(groups)
            print("done")

        formatter = OutputFormatter()

        existing = os.listdir("output") if os.path.exists("output") else []
        max_seq = 0
        for name in existing:
            parts = name.split("_")
            if len(parts) >= 3 and parts[-1].split(".")[0].isdigit():
                max_seq = max(max_seq, int(parts[-1].split(".")[0]))
        seq = max_seq + 1

        groups_path = os.path.join(
            "output", f"Play_groups_{args.iterations}_{seq}.json"
        )
        formatter.write_groups_file(
            new_iterations, groups_path, past_count, past_iterations
        )

        summary_path = os.path.join(
            "output", f"Summary_{args.iterations}_{seq}.txt"
        )
        formatter.write_summary_file(
            children,
            new_iterations,
            summary_path,
            optimizer.warnings,
            past_count,
            optimizer,
        )

        report_path = os.path.join(
            "output", f"Report_{args.iterations}_{seq}.html"
        )
        generate_html_report(
            children, new_iterations, report_path, past_count
        )

        print(f"\nOutput:")
        print(f"  {groups_path}")
        print(f"  {summary_path}")
        print(f"  {report_path}")
        print(
            f"\nTo use these results as input for the next run, copy"
            f"\n  {groups_path}"
            f"\n  to input/past_iterations.json"
        )

        if optimizer.warnings:
            print(
                f"\n{len(optimizer.warnings)} warning(s) — see summary."
            )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
