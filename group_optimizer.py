"""
Group Optimizer Module
Implements the weighted constraint satisfaction algorithm for group optimization.
"""

import json
import os
import random
from constraint_solver import ConstraintSolver


class Group:
    """Represents a group of children."""
    
    def __init__(self, children):
        self.children = children
        self.host = children[0] if children else None
    
    def get_boys(self):
        """Get list of boys in the group."""
        return [child for child in self.children if child.is_boy]
    
    def get_girls(self):
        """Get list of girls in the group."""
        return [child for child in self.children if child.is_girl]
    
    def __str__(self):
        names = [child.name for child in self.children]
        return f"Group(host={self.host.name if self.host else 'None'}, children={names})"


class GroupOptimizer:
    """Optimizes child group arrangements using weighted constraint satisfaction."""
    
    def __init__(self):
        self.config = self._load_config()
        self.solver = ConstraintSolver(self.config)
        self.warnings = []
    
    def _load_config(self):
        """Load configuration from weights_config.json."""
        config_path = os.path.join(os.path.dirname(__file__), 'weights_config.json')
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration if file not found
            return {
                "weights": {
                    "gender_balance": 1000,
                    "host_rotation": 100,
                    "group_diversity": 50,
                    "host_fairness": 25,
                    "meeting_fairness": 10
                },
                "constraints": {
                    "target_boys_per_group": 2,
                    "target_girls_per_group": 2,
                    "max_hosting_difference": 1,
                    "max_meeting_difference": 2
                },
                "algorithm": {
                    "max_attempts": 10000,
                    "backtrack_threshold": 0.7
                }
            }
    
    def create_iteration(self, children, iteration_num, previous_iterations):
        """Create groups for a specific iteration."""
        print(f"  Attempting to create iteration {iteration_num} with constraint satisfaction...")
        
        # Use constraint solver to find optimal grouping
        groups = self.solver.solve(children, iteration_num, previous_iterations)
        
        if not groups:
            self.warnings.append(f"Iteration {iteration_num}: Could not satisfy all constraints")
            return None
        
        # Additional high-level validation
        total_children_in_groups = sum(len(group.children) for group in groups)
        expected_total = len(children)
        
        if total_children_in_groups != expected_total:
            error_msg = f"Critical error: Total children in groups ({total_children_in_groups}) != expected ({expected_total})"
            self.warnings.append(f"Iteration {iteration_num}: {error_msg}")
            print(f"ERROR: {error_msg}")
            return None
        
        # Update child statistics
        self._update_child_statistics(children, groups, iteration_num)
        
        # Validate groups
        if not self._validate_groups(groups, iteration_num):
            return None
        
        return groups
    
    def _update_child_statistics(self, children, groups, iteration_num):
        """Update hosting counts and meeting records for children."""
        from itertools import combinations
        
        for group in groups:
            # Update host count
            if group.host:
                group.host.hosting_count += 1
                group.host.hosting_iterations.append(iteration_num)
            
            # Update meetings - each child meets every other child in their group
            for i, child1 in enumerate(group.children):
                for j, child2 in enumerate(group.children):
                    if i != j:
                        # Increment meeting count for this pair
                        if child2.name in child1.meetings:
                            child1.meetings[child2.name] += 1
                        else:
                            child1.meetings[child2.name] = 1
            
            # Update triplet meetings for each child in the group
            for triplet_children in combinations(group.children, 3):
                triplet_names = [child.name for child in triplet_children]
                triplet_key = tuple(sorted(triplet_names))
                
                # Add this iteration to each child's triplet meeting record
                for child in triplet_children:
                    if triplet_key not in child.triplet_meetings:
                        child.triplet_meetings[triplet_key] = []
                    child.triplet_meetings[triplet_key].append(iteration_num)
    
    def _validate_groups(self, groups, iteration_num):
        """Validate that groups meet basic requirements."""
        if len(groups) != 6:
            self.warnings.append(f"Iteration {iteration_num}: Expected 6 groups, got {len(groups)}")
            return False
        
        total_children = sum(len(group.children) for group in groups)
        if total_children != 24:
            self.warnings.append(f"Iteration {iteration_num}: Expected 24 children total, got {total_children}")
            return False
        
        for i, group in enumerate(groups, 1):
            if len(group.children) != 4:
                self.warnings.append(f"Iteration {iteration_num}, Group {i}: Expected 4 children, got {len(group.children)}")
                return False
            
            boys = len(group.get_boys())
            girls = len(group.get_girls())
            
            # Check gender balance (highest priority constraint)
            if abs(boys - 2) > 1 or abs(girls - 2) > 1:
                self.warnings.append(f"Iteration {iteration_num}, Group {i}: Poor gender balance ({boys}B, {girls}G)")
        
        return True
    
    def process_past_iterations(self, children, past_iterations):
        """Process past iterations to update child statistics and tracking data."""
        for iteration_num, groups in enumerate(past_iterations, 1):
            # Update child statistics for this past iteration
            self._update_child_statistics(children, groups, iteration_num)
    
    def get_statistics(self, children):
        """Get statistics about hosting and meetings for all children."""
        stats = {
            'hosting_counts': {},
            'meeting_matrix': {},
            'total_meetings': {}
        }
        
        for child in children:
            stats['hosting_counts'][child.name] = child.hosting_count
            stats['meeting_matrix'][child.name] = list(child.meetings)
            stats['total_meetings'][child.name] = len(child.meetings)
        
        return stats
    
    def get_new_iterations_statistics(self, new_iterations, past_iteration_count):
        """Get statistics for only the new iterations."""
        stats = {
            'hosting_counts': {},
            'meeting_matrix': {},
            'hosting_iterations': {}
        }
        
        # Initialize all children with zero counts
        all_children = set()
        for groups in new_iterations:
            for group in groups:
                for child in group.children:
                    all_children.add(child.name)
        
        for child_name in all_children:
            stats['hosting_counts'][child_name] = 0
            stats['meeting_matrix'][child_name] = {}
            stats['hosting_iterations'][child_name] = []
        
        # Calculate statistics only from new iterations
        for iteration_num, groups in enumerate(new_iterations, 1):
            absolute_iteration_num = past_iteration_count + iteration_num
            
            for group in groups:
                # Count hosting for first child (host)
                if group.host:
                    stats['hosting_counts'][group.host.name] += 1
                    stats['hosting_iterations'][group.host.name].append(absolute_iteration_num)
                
                # Count meetings between all children in the group
                for i, child1 in enumerate(group.children):
                    for j, child2 in enumerate(group.children):
                        if i != j:
                            child2_name = child2.name
                            if child2_name in stats['meeting_matrix'][child1.name]:
                                stats['meeting_matrix'][child1.name][child2_name] += 1
                            else:
                                stats['meeting_matrix'][child1.name][child2_name] = 1
        
        return stats
