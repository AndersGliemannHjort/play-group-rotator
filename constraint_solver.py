"""
Constraint Solver Module
Implements backtracking algorithm with weighted constraint satisfaction.
"""

import random
from itertools import combinations


class ConstraintSolver:
    """Implements constraint satisfaction with backtracking for group optimization."""
    
    def __init__(self, config):
        self.config = config
        self.weights = config['weights']
        self.constraints = config['constraints']
        self.algorithm = config['algorithm']
    
    def solve(self, children, iteration_num, previous_iterations):
        """Solve the constraint satisfaction problem to create optimal groups."""
        boys = [child for child in children if child.is_boy]
        girls = [child for child in children if child.is_girl]
        
        best_solution = None
        best_score = float('-inf')
        attempts = 0
        
        # Try multiple times to find the best solution
        while attempts < self.algorithm['max_attempts']:
            attempts += 1
            
            # Generate a candidate solution
            solution = self._generate_candidate_solution(boys, girls, iteration_num, previous_iterations)
            
            if solution:
                score = self._evaluate_solution(solution, iteration_num, previous_iterations)
                
                if score > best_score:
                    best_score = score
                    best_solution = solution
                
                # If we found a solution that meets the threshold, we can stop early
                if score >= self.algorithm['backtrack_threshold'] * self._get_perfect_score():
                    break
        
        return best_solution
    
    def _generate_candidate_solution(self, boys, girls, iteration_num, previous_iterations):
        """Generate a candidate solution using greedy assignment with randomization."""
        from group_optimizer import Group
        
        # Create copies to avoid modifying original lists
        available_boys = boys.copy()
        available_girls = girls.copy()
        
        # Shuffle for randomization
        random.shuffle(available_boys)
        random.shuffle(available_girls)
        
        groups = []
        
        for group_num in range(6):
            group_children = []
            
            # Try to assign 2 boys and 2 girls to each group
            boys_needed = 2
            girls_needed = 2
            
            # Adjust if we don't have enough of one gender
            remaining_boys = len(available_boys)
            remaining_girls = len(available_girls)
            remaining_groups = 6 - group_num
            
            if remaining_boys < boys_needed * remaining_groups:
                boys_needed = max(0, remaining_boys - (remaining_groups - 1))
            if remaining_girls < girls_needed * remaining_groups:
                girls_needed = max(0, remaining_girls - (remaining_groups - 1))
            
            # Ensure we have exactly 4 children per group
            total_needed = 4
            if boys_needed + girls_needed > total_needed:
                if boys_needed > girls_needed:
                    boys_needed = total_needed - girls_needed
                else:
                    girls_needed = total_needed - boys_needed
            elif boys_needed + girls_needed < total_needed:
                shortage = total_needed - boys_needed - girls_needed
                if remaining_boys > boys_needed:
                    boys_needed += shortage
                elif remaining_girls > girls_needed:
                    girls_needed += shortage
            
            # Assign boys
            for _ in range(min(boys_needed, len(available_boys))):
                group_children.append(available_boys.pop(0))
            
            # Assign girls
            for _ in range(min(girls_needed, len(available_girls))):
                group_children.append(available_girls.pop(0))
            
            # If we still need more children, assign from remaining
            while len(group_children) < 4 and (available_boys or available_girls):
                if available_boys:
                    group_children.append(available_boys.pop(0))
                elif available_girls:
                    group_children.append(available_girls.pop(0))
            
            if len(group_children) != 4:
                return None  # Invalid solution
            
            # Assign host (first child in group)
            groups.append(Group(group_children))
        
        return groups
    
    def _evaluate_solution(self, groups, iteration_num, previous_iterations):
        """Evaluate the quality of a solution using weighted scoring."""
        score = 0
        
        # 1. Gender balance (highest priority)
        for group in groups:
            boys = len(group.get_boys())
            girls = len(group.get_girls())
            
            # Perfect score for 2-2 balance
            if boys == 2 and girls == 2:
                score += self.weights['gender_balance']
            else:
                # Penalty for imbalance
                imbalance = abs(boys - 2) + abs(girls - 2)
                score += self.weights['gender_balance'] * (1 - imbalance * 0.5)
        
        # 2. Host rotation constraint
        if iteration_num > 1:
            previous_hosts = set()
            for prev_iteration in previous_iterations:
                for group in prev_iteration:
                    if group.host:
                        previous_hosts.add(group.host.name)
            
            current_hosts = set()
            for group in groups:
                if group.host:
                    current_hosts.add(group.host.name)
            
            # Reward for not repeating hosts
            non_repeat_hosts = len(current_hosts - previous_hosts)
            score += self.weights['host_rotation'] * (non_repeat_hosts / 6)
        
        # 3. Group diversity (avoiding same children together)
        if iteration_num > 1:
            diversity_score = self._calculate_diversity_score(groups, previous_iterations)
            score += self.weights['group_diversity'] * diversity_score
        
        # 4. Host fairness
        hosting_counts = {}
        for group in groups:
            if group.host:
                hosting_counts[group.host.name] = group.host.hosting_count + 1
        
        if hosting_counts:
            max_hosting = max(hosting_counts.values())
            min_hosting = min(hosting_counts.values())
            fairness = 1 - (max_hosting - min_hosting) / max(max_hosting, 1)
            score += self.weights['host_fairness'] * fairness
        
        # 5. Meeting fairness
        meeting_fairness = self._calculate_meeting_fairness(groups)
        score += self.weights['meeting_fairness'] * meeting_fairness
        
        return score
    
    def _calculate_diversity_score(self, groups, previous_iterations):
        """Calculate how well groups avoid repeating previous combinations."""
        total_pairs = 0
        diverse_pairs = 0
        
        # Get all pairs from previous iterations
        previous_pairs = set()
        for prev_iteration in previous_iterations:
            for group in prev_iteration:
                for i in range(len(group.children)):
                    for j in range(i + 1, len(group.children)):
                        pair = tuple(sorted([group.children[i].name, group.children[j].name]))
                        previous_pairs.add(pair)
        
        # Check current pairs
        for group in groups:
            for i in range(len(group.children)):
                for j in range(i + 1, len(group.children)):
                    pair = tuple(sorted([group.children[i].name, group.children[j].name]))
                    total_pairs += 1
                    if pair not in previous_pairs:
                        diverse_pairs += 1
        
        return diverse_pairs / max(total_pairs, 1)
    
    def _calculate_meeting_fairness(self, groups):
        """Calculate fairness of meeting distribution."""
        meeting_counts = {}
        
        for group in groups:
            for child in group.children:
                if child.name not in meeting_counts:
                    meeting_counts[child.name] = len(child.meetings)
                
                # Count new meetings in this group
                for other_child in group.children:
                    if child != other_child and other_child.name not in child.meetings:
                        meeting_counts[child.name] += 1
        
        if not meeting_counts:
            return 1.0
        
        max_meetings = max(meeting_counts.values())
        min_meetings = min(meeting_counts.values())
        
        return 1 - (max_meetings - min_meetings) / max(max_meetings, 1)
    
    def _get_perfect_score(self):
        """Calculate the theoretical perfect score."""
        return (self.weights['gender_balance'] * 6 +  # Perfect gender balance
                self.weights['host_rotation'] +        # Perfect host rotation
                self.weights['group_diversity'] +      # Perfect diversity
                self.weights['host_fairness'] +        # Perfect host fairness
                self.weights['meeting_fairness'])      # Perfect meeting fairness
