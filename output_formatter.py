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
                
                # Write meeting matrix
                f.write("MEETING MATRIX\n")
                f.write("-" * 20 + "\n")
                f.write("Shows how many times each pair of children have been in the same group:\n\n")
                
                # Create meeting matrix
                child_names = [child.name for child in children]
                child_names.sort()
                
                meeting_matrix = {}
                for child in children:
                    meeting_matrix[child.name] = {}
                    for other_name in child_names:
                        if other_name == child.name:
                            meeting_matrix[child.name][other_name] = '-'
                        else:
                            count = 0
                            for meeting_name in child.meetings:
                                if meeting_name == other_name:
                                    count += 1
                            meeting_matrix[child.name][other_name] = str(count)
                
                # Write matrix header
                f.write("Child".ljust(15))
                for name in child_names:
                    f.write(f"{name[:8]:>8}")
                f.write("\n")
                
                # Write matrix rows
                for child_name in child_names:
                    f.write(f"{child_name[:14]:<15}")
                    for other_name in child_names:
                        f.write(f"{meeting_matrix[child_name][other_name]:>8}")
                    f.write("\n")
                
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
