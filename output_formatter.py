"""
Output Formatter Module
Handles formatting and writing of output files.
"""

import os
from datetime import datetime


class OutputFormatter:
    """Formats and writes output files for group iterations and summaries."""
    
    def write_groups_file(self, all_iterations, filepath):
        """Write groups output file with tab-delimited format."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for iteration_num, groups in enumerate(all_iterations, 1):
                    f.write(f"=== ITERATION {iteration_num} ===\n")
                    
                    for group_num, group in enumerate(groups, 1):
                        # Write children names separated by tabs
                        names = [child.name for child in group.children]
                        f.write('\t'.join(names) + '\n')
                    
                    f.write('\n')  # Empty line between iterations
            
            print(f"Groups file written: {filepath}")
            
        except Exception as e:
            raise Exception(f"Error writing groups file: {e}")
    
    def write_summary_file(self, children, all_iterations, filepath, warnings):
        """Write detailed summary report."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("CHILD GROUP ROTATION SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Iterations: {len(all_iterations)}\n")
                f.write(f"Total Children: {len(children)}\n\n")
                
                # Write hosting statistics
                f.write("HOSTING COUNTS\n")
                f.write("-" * 20 + "\n")
                hosting_counts = {}
                for child in children:
                    hosting_counts[child.name] = child.hosting_count
                
                # Sort by hosting count (descending) then by name
                sorted_hosting = sorted(hosting_counts.items(), 
                                      key=lambda x: (-x[1], x[0]))
                
                for name, count in sorted_hosting:
                    f.write(f"{name:<20} {count:>3} times\n")
                
                # Hosting statistics
                counts = list(hosting_counts.values())
                f.write(f"\nHosting Statistics:\n")
                f.write(f"  Min: {min(counts)}, Max: {max(counts)}, Avg: {sum(counts)/len(counts):.1f}\n\n")
                
                # Write hosting proximity section
                f.write("HOSTING PROXIMITY\n")
                f.write("-" * 17 + "\n")
                f.write("Shows minimum iterations between hosting periods (children who host multiple times):\n\n")
                
                # Calculate hosting proximity for children with multiple hostings
                proximity_data = []
                for child in children:
                    if hasattr(child, 'hosting_iterations') and len(child.hosting_iterations) > 1:
                        # Calculate all breaks between hosting periods
                        sorted_iterations = sorted(child.hosting_iterations)
                        breaks = []
                        for i in range(1, len(sorted_iterations)):
                            break_length = sorted_iterations[i] - sorted_iterations[i-1] - 1
                            breaks.append(break_length)
                        
                        # Get minimum break
                        min_break = min(breaks)
                        proximity_data.append((child.name, min_break, sorted_iterations))
                
                # Sort by minimum break (ascending), then by name (alphabetical)
                proximity_data.sort(key=lambda x: (x[1], x[0]))
                
                if proximity_data:
                    for name, min_break, iterations in proximity_data:
                        iteration_list = ", ".join(map(str, iterations))
                        break_text = "iteration" if min_break == 1 else "iterations"
                        f.write(f"{name:<20} {min_break} {break_text} (hosted in: {iteration_list})\n")
                else:
                    f.write("No children hosted multiple times.\n")
                
                f.write("\n")
                
                # Write meeting details in vertical list format
                f.write("MEETING DETAILS\n")
                f.write("-" * 20 + "\n")
                f.write("Shows how many times each child has been grouped with others:\n\n")
                
                # Sort children by name for consistent output
                sorted_children = sorted(children, key=lambda x: x.name)
                
                for child in sorted_children:
                    f.write(f"{child.name}:\n")
                    
                    # Create a list of meetings with counts
                    meeting_counts = {}
                    for other_child in children:
                        if other_child.name != child.name:
                            # Count how many times they were grouped together
                            count = 0
                            for meeting_name in child.meetings:
                                if meeting_name == other_child.name:
                                    count += 1
                            if count > 0:
                                meeting_counts[other_child.name] = count
                    
                    # Sort meetings by count (descending) then by name
                    if meeting_counts:
                        sorted_meetings = sorted(meeting_counts.items(), 
                                               key=lambda x: (-x[1], x[0]))
                        
                        # Group by count for better readability
                        current_count = None
                        meeting_list = []
                        
                        for other_name, count in sorted_meetings:
                            if count != current_count:
                                if meeting_list and current_count is not None:
                                    f.write(f"  {current_count} time{'s' if current_count > 1 else ''}: {', '.join(meeting_list)}\n")
                                current_count = count
                                meeting_list = [other_name]
                            else:
                                meeting_list.append(other_name)
                        
                        # Write the last group
                        if meeting_list and current_count is not None:
                            f.write(f"  {current_count} time{'s' if current_count > 1 else ''}: {', '.join(meeting_list)}\n")
                    else:
                        f.write("  No meetings recorded\n")
                    
                    f.write("\n")  # Empty line between children
                
                # Meeting statistics
                f.write("\nMEETING STATISTICS\n")
                f.write("-" * 20 + "\n")
                for child in children:
                    meeting_count = len(child.meetings)
                    f.write(f"{child.name:<20} met {meeting_count:>2} different children\n")
                
                # Overall meeting stats
                meeting_counts = [len(child.meetings) for child in children]
                f.write(f"\nMeeting Statistics:\n")
                f.write(f"  Min: {min(meeting_counts)}, Max: {max(meeting_counts)}, Avg: {sum(meeting_counts)/len(meeting_counts):.1f}\n\n")
                
                # Write iteration details
                f.write("ITERATION DETAILS\n")
                f.write("-" * 20 + "\n")
                for iteration_num, groups in enumerate(all_iterations, 1):
                    f.write(f"\nIteration {iteration_num}:\n")
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
                    f.write("\nNo warnings or constraint violations detected.\n")
                
                f.write(f"\n" + "=" * 50 + "\n")
                f.write("End of Summary Report\n")
            
            print(f"Summary file written: {filepath}")
            
        except Exception as e:
            raise Exception(f"Error writing summary file: {e}")
