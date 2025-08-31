"""
Output Formatter Module
Handles formatting and writing of output files.
"""

import os
from datetime import datetime


class OutputFormatter:
    """Formats and writes output files for group iterations and summaries."""

    def write_groups_file(self,
                          all_iterations,
                          filepath,
                          past_iteration_count=0):
        """Write groups output file with comma-separated format."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Add header if there are past iterations
                if past_iteration_count > 0:
                    f.write(
                        f"Based on {past_iteration_count} previous iteration(s)\n\n"
                    )

                for iteration_num, groups in enumerate(all_iterations, 1):
                    absolute_iteration_num = past_iteration_count + iteration_num
                    f.write(f"=== ITERATION {absolute_iteration_num} ===\n")

                    for group_num, group in enumerate(groups, 1):
                        # Write children names separated by commas with spaces
                        names = [child.name for child in group.children]
                        f.write(', '.join(names) + '\n')

                    f.write('\n')  # Empty line between iterations

            print(f"Groups file written: {filepath}")

        except Exception as e:
            raise Exception(f"Error writing groups file: {e}")

    def write_summary_file(self,
                           children,
                           all_iterations,
                           filepath,
                           warnings,
                           debug_log=None,
                           past_iteration_count=0,
                           optimizer=None):
        """Write detailed summary report."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("CHILD GROUP ROTATION SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")

                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                if past_iteration_count > 0:
                    f.write(f"Past Iterations: {past_iteration_count}\n")
                    f.write(f"New Iterations: {len(all_iterations)}\n")
                    f.write(
                        f"Total Iterations: {past_iteration_count + len(all_iterations)}\n"
                    )
                else:
                    f.write(f"Total Iterations: {len(all_iterations)}\n")
                f.write(f"Total Children: {len(children)}\n\n")

                # Add algorithm overview section
                f.write("ALGORITHM OVERVIEW & MATHEMATICAL REALITIES\n")
                f.write("=" * 50 + "\n\n")

                f.write("How the System Works:\n")
                f.write(
                    "This optimizer uses a weighted constraint satisfaction algorithm that balances\n"
                )
                f.write(
                    "multiple competing goals. The system prioritizes constraints in a specific\n"
                )
                f.write(
                    "hierarchy, with gender balance as the absolute requirement, followed by\n"
                )
                f.write(
                    "hosting fairness, meeting diversity, and break prevention.\n\n"
                )

                f.write("Constraint Hierarchy (in order of importance):\n")
                f.write(
                    "1. Gender Balance (Critical): Every group must have exactly 2 boys and 2 girls\n"
                )
                f.write(
                    "2. Hosting Fairness (High): Children should host approximately equal numbers of times\n"
                )
                f.write(
                    "3. Meeting Diversity (High): Children should meet different people when possible\n"
                )
                f.write(
                    "4. Host break length (Medium): Discourages consecutive hosting periods\n\n"
                )

                f.write("Expected Outcomes Due to Mathematical Reality:\n\n")

                f.write("✓ What You'll Always See:\n")
                f.write(
                    "- Perfect gender balance (2 boys + 2 girls) in every group\n"
                )
                f.write(
                    "- Girls will tend to have more reoccuring meetings with the same boys than the same girls, and vice versa\n"
                )
                f.write(
                    "- Fair hosting distribution (max difference of 1 hosting between any two children)\n"
                )
                f.write(
                    "- Good host rotation (break prevention naturally prevents consecutive hosting)\n"
                )
                f.write(
                    "- Good meeting diversity with minimal repeated groupings\n"
                )
                f.write(
                    "- Randomized selection eliminating alphabetical bias\n\n")

                f.write("⚠️ What You May Sometimes See:\n")
                f.write(
                    "- Some children meeting 2-3 times across multiple iterations\n"
                )
                f.write(
                    "- Occasional repeated triplets (same 3 children grouped together multiple times)\n"
                )
                f.write(
                    "- Occasional 2-iteration hosting breaks (instead of ideal 3+ iterations)\n"
                )
                f.write(
                    "- Minor variations in hosting schedules to optimize meeting diversity\n\n"
                )

                f.write("Why Trade-offs Occur:\n")
                f.write(
                    "With 24 children forming 6 groups over multiple iterations, perfect optimization\n"
                )
                f.write(
                    "of all constraints simultaneously is mathematically impossible. The system\n"
                )
                f.write("prioritizes constraints based on importance:\n\n")
                f.write("- Gender balance is NEVER compromised\n")
                f.write(
                    "- Hosting fairness takes precedence over other patterns\n"
                )
                f.write(
                    "- Meeting diversity may require flexible hosting schedules\n"
                )
                f.write(
                    "- Break lengths yield when necessary for higher priorities\n\n"
                )

                f.write("Understanding the Algorithm's Approach:\n")
                f.write(
                    "The system represents optimal solutions given the constraint priorities.\n"
                )
                f.write(
                    "When conflicts arise between different goals, the algorithm will sacrifice\n"
                )
                f.write(
                    "lower-priority constraints to maintain the most important requirements,\n"
                )
                f.write(
                    "always ensuring gender balance while maximizing overall fairness and diversity.\n\n"
                )
                f.write("=" * 50 + "\n\n")

                # Get statistics for new iterations only
                if optimizer and past_iteration_count > 0:
                    new_stats = optimizer.get_new_iterations_statistics(
                        all_iterations, past_iteration_count)
                    hosting_counts = new_stats['hosting_counts']
                    meeting_matrix = new_stats['meeting_matrix']
                    hosting_iterations_data = new_stats['hosting_iterations']
                else:
                    # Fallback to full statistics if no optimizer or no past iterations
                    hosting_counts = {}
                    meeting_matrix = {}
                    hosting_iterations_data = {}
                    for child in children:
                        hosting_counts[child.name] = child.hosting_count
                        meeting_matrix[child.name] = child.meetings
                        hosting_iterations_data[
                            child.name] = child.hosting_iterations if hasattr(
                                child, 'hosting_iterations') else []

                # Write hosting statistics
                f.write(
                    "HOSTING COUNTS, INCLUDING HISTORICAL HOSTING COUNTS\n")
                f.write("-" * 20 + "\n")

                # Sort by hosting count (descending) then by name
                sorted_hosting = sorted(hosting_counts.items(),
                                        key=lambda x: (-x[1], x[0]))

                for name, count in sorted_hosting:
                    # Get historical total from child object
                    total_count = None
                    for child in children:
                        if child.name == name:
                            total_count = child.hosting_count
                            break

                    if total_count is not None and past_iteration_count > 0:
                        f.write(
                            f"{name:<20} {count:>3} times ({total_count} total across all iterations)\n"
                        )
                    else:
                        f.write(f"{name:<20} {count:>3} times\n")

                # Hosting statistics
                counts = list(hosting_counts.values())
                f.write(f"\nHosting Statistics:\n")
                f.write(
                    f"  Min: {min(counts)}, Max: {max(counts)}, Avg: {sum(counts)/len(counts):.1f}\n\n"
                )

                # Write hosting proximity section
                f.write("HOSTING PROXIMITY FOR NEW ITERATIONS\n")
                f.write("-" * 17 + "\n")
                f.write(
                    "Shows minimum iterations between hosting periods (children who host multiple times):\n\n"
                )

                # Calculate hosting proximity for children with multiple hostings
                proximity_data = []
                for child_name in hosting_iterations_data:
                    child_hosting_iterations = hosting_iterations_data[
                        child_name]
                    if len(child_hosting_iterations) > 1:
                        # Calculate all breaks between hosting periods
                        sorted_iterations = sorted(child_hosting_iterations)
                        breaks = []
                        for i in range(1, len(sorted_iterations)):
                            break_length = sorted_iterations[
                                i] - sorted_iterations[i - 1] - 1
                            breaks.append(break_length)

                        # Get minimum break
                        min_break = min(breaks)
                        proximity_data.append(
                            (child_name, min_break, sorted_iterations))

                # Sort by minimum break (ascending), then by name (alphabetical)
                proximity_data.sort(key=lambda x: (x[1], x[0]))

                if proximity_data:
                    for name, min_break, iterations in proximity_data:
                        iteration_list = ", ".join(map(str, iterations))
                        break_text = "iteration" if min_break == 1 else "iterations"
                        f.write(
                            f"{name:<20} {min_break} {break_text} (will host in: {iteration_list})\n"
                        )
                else:
                    f.write("No children hosted multiple times.\n")

                f.write("\n")

                # Write meeting details in vertical list format
                f.write("MEETING DETAILS FOR ALL ITERATIONS\n")
                f.write("-" * 40 + "\n")
                f.write(
                    "Shows how many times each child has been grouped with others across all iterations:\n\n"
                )

                # Sort children by name for consistent output
                sorted_child_names = sorted(meeting_matrix.keys())

                for child_name in sorted_child_names:
                    f.write(f"{child_name}:\n")

                    # Get meeting counts from NEW iterations statistics
                    new_meeting_counts = meeting_matrix[child_name].copy(
                    ) if child_name in meeting_matrix else {}

                    # Get meeting counts from ALL iterations (including past)
                    # Find the child object to get complete meeting history
                    child_obj = next(
                        (c for c in children if c.name == child_name), None)
                    all_meeting_counts = child_obj.meetings.copy(
                    ) if child_obj else {}

                    # Write NEW iterations meetings
                    f.write("  NEW iterations:\n")
                    if new_meeting_counts:
                        sorted_new_meetings = sorted(
                            new_meeting_counts.items(),
                            key=lambda x: (-x[1], x[0]))
                        new_groups = {}
                        for other_name, count in sorted_new_meetings:
                            if count not in new_groups:
                                new_groups[count] = []
                            new_groups[count].append(other_name)

                        for count in sorted(new_groups.keys(), reverse=True):
                            names_list = ', '.join(sorted(new_groups[count]))
                            f.write(
                                f"  {count} time{'s' if count > 1 else ''}: {names_list}\n"
                            )
                    else:
                        f.write("  No meetings recorded\n")

                    # Write ALL iterations meetings
                    f.write("  \n  ALL iterations:\n")
                    if all_meeting_counts:
                        sorted_all_meetings = sorted(
                            all_meeting_counts.items(),
                            key=lambda x: (-x[1], x[0]))
                        all_groups = {}
                        for other_name, count in sorted_all_meetings:
                            if count not in all_groups:
                                all_groups[count] = []
                            all_groups[count].append(other_name)

                        for count in sorted(all_groups.keys(), reverse=True):
                            names_list = ', '.join(sorted(all_groups[count]))
                            children_count = len(all_groups[count])
                            f.write(
                                f"  {count} time{'s' if count > 1 else ''} ({children_count}/24): {names_list}\n"
                            )
                    else:
                        f.write("  No meetings recorded\n")

                    f.write("\n")  # Empty line between children

                # Add quartets and triplets analysis
                self._write_quartets_triplets_analysis(f, all_iterations)

                # Meeting statistics
                f.write("\nMEETING STATISTICS FOR NEW ITERATIONS\n")
                f.write("-" * 20 + "\n")

                # Create list of (child_name, meeting_count) and sort by count (desc) then name
                meeting_stats = [
                    (child_name, len(meetings))
                    for child_name, meetings in meeting_matrix.items()
                ]
                meeting_stats.sort(key=lambda x: (-x[1], x[0]))

                for name, meeting_count in meeting_stats:
                    f.write(
                        f"{name:<20} meet {meeting_count:>2} different children\n"
                    )

                # Overall meeting stats
                meeting_counts = [
                    len(meetings) for meetings in meeting_matrix.values()
                ]
                if meeting_counts:
                    f.write(f"\nMeeting Statistics:\n")
                    f.write(
                        f"  Min: {min(meeting_counts)}, Max: {max(meeting_counts)}, Avg: {sum(meeting_counts)/len(meeting_counts):.1f}\n\n"
                    )
                else:
                    f.write(f"\nNo meetings recorded in new iterations.\n\n")

                # Write iteration details
                f.write("ITERATION DETAILS\n")
                f.write("-" * 20 + "\n")
                for iteration_num, groups in enumerate(all_iterations, 1):
                    absolute_iteration_num = past_iteration_count + iteration_num
                    f.write(f"\nIteration {absolute_iteration_num}:\n")
                    for group_num, group in enumerate(groups, 1):
                        boys = len(group.get_boys())
                        girls = len(group.get_girls())
                        host_name = group.host.name if group.host else "None"

                        f.write(f"  Group {group_num}: Host={host_name:<12} "
                                f"({boys}B, {girls}G) ")

                        names = [child.name for child in group.children]
                        f.write(f"Members: {', '.join(names)}\n")

                # Write warnings
                if warnings:
                    f.write("\nWARNINGS AND CONSTRAINT VIOLATIONS\n")
                    f.write("-" * 40 + "\n")
                    for warning in warnings:
                        f.write(f"• {warning}\n")
                else:
                    f.write(
                        "\nNo warnings or constraint violations detected.\n")

                f.write(f"\n" + "=" * 50 + "\n")
                f.write("End of Summary Report\n")

            print(f"Summary file written: {filepath}")

            # Write debug log if provided
            if debug_log:
                debug_filepath = filepath.replace('Summary_',
                                                  'debug_log_').replace(
                                                      '.txt', '.txt')
                debug_log.write_debug_log(debug_filepath)
                print(f"Debug file written: {debug_filepath}")

        except Exception as e:
            raise Exception(f"Error writing summary file: {e}")

    def _write_quartets_triplets_analysis(self, f, all_iterations):
        """Write analysis of recurring quartets and triplets in NEW iterations."""
        from itertools import combinations

        # Collect all quartets (full groups) from new iterations
        quartets = []
        triplets_count = {}
        quartets_count = {}
        triplets_iterations = {
        }  # Track which iterations each triplet appeared in
        quartets_iterations = {
        }  # Track which iterations each quartet appeared in

        for iteration_idx, iteration_groups in enumerate(all_iterations):
            iteration_num = iteration_idx + 1  # 1-based iteration numbering
            for group in iteration_groups:
                # Get sorted names for consistent comparison
                group_names = sorted([child.name for child in group.children])

                # Store quartet (full group of 4)
                quartet_key = tuple(group_names)
                quartets_count[quartet_key] = quartets_count.get(
                    quartet_key, 0) + 1
                if quartet_key not in quartets_iterations:
                    quartets_iterations[quartet_key] = []
                quartets_iterations[quartet_key].append(iteration_num)

                # Generate all triplet combinations from this group
                for triplet in combinations(group_names, 3):
                    triplet_key = tuple(sorted(triplet))
                    triplets_count[triplet_key] = triplets_count.get(
                        triplet_key, 0) + 1
                    if triplet_key not in triplets_iterations:
                        triplets_iterations[triplet_key] = []
                    triplets_iterations[triplet_key].append(iteration_num)

        # Find recurring quartets (appear more than once)
        recurring_quartets = {k: v for k, v in quartets_count.items() if v > 1}

        # Find recurring triplets (appear more than once)
        recurring_triplets = {k: v for k, v in triplets_count.items() if v > 1}

        # Write quartets section
        f.write("\nRECURRING QUARTETS FOR NEW ITERATIONS\n")
        f.write("-" * 20 + "\n")
        f.write(
            "Shows complete 4-person groups that met together multiple times:\n\n"
        )

        if recurring_quartets:
            # Sort by frequency (descending), then alphabetically
            sorted_quartets = sorted(recurring_quartets.items(),
                                     key=lambda x: (-x[1], x[0]))

            for quartet, count in sorted_quartets:
                names = ', '.join(quartet)
                iterations = ', '.join(
                    map(str, sorted(quartets_iterations[quartet])))
                f.write(
                    f"  {count} times: {names} (iterations {iterations})\n")
        else:
            f.write("  No recurring quartets found.\n")

        # Write triplets section
        f.write("\nRECURRING TRIPLETS FOR NEW ITERATIONS\n")
        f.write("-" * 20 + "\n")
        f.write(
            "Shows 3-person subgroups that met together multiple times:\n\n")

        if recurring_triplets:
            # Sort by frequency (descending), then alphabetically
            sorted_triplets = sorted(recurring_triplets.items(),
                                     key=lambda x: (-x[1], x[0]))

            for triplet, count in sorted_triplets:
                names = ', '.join(triplet)
                iterations = ', '.join(
                    map(str, sorted(triplets_iterations[triplet])))
                f.write(
                    f"  {count} times: {names} (iterations {iterations})\n")
        else:
            f.write("  No recurring triplets found.\n")

        f.write("\n")
