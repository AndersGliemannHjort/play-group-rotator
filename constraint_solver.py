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
        """Generate a candidate solution using host-first construction."""
        from group_optimizer import Group
        
        # Step 1: Select 6 hosts fairly based on hosting counts
        all_children = boys + girls
        hosts = self._select_hosts(all_children, 6)
        
        if len(hosts) != 6:
            return None  # Failed to select hosts
        
        # Step 2: Build groups around each host
        groups = []
        remaining_children = [child for child in all_children if child not in hosts]
        
        for host in hosts:
            # Build a group around this host
            group = self._build_group_around_host(host, remaining_children)
            if not group:
                return None  # Failed to build valid group
            
            groups.append(group)
            # Remove assigned children from remaining pool
            for child in group.children[1:]:  # Skip host (first child)
                if child in remaining_children:
                    remaining_children.remove(child)
        
        return groups
    
    def _select_hosts(self, all_children, num_hosts):
        """Select hosts fairly based on hosting counts."""
        # Sort children by hosting count (ascending), then by name for consistency
        candidates = sorted(all_children, key=lambda child: (child.hosting_count, child.name))
        
        # Find the minimum hosting count
        min_hosting = candidates[0].hosting_count
        
        # Get all children with the minimum hosting count
        min_hosting_children = [child for child in candidates if child.hosting_count == min_hosting]
        
        # If we have enough children with minimum hosting, select from them
        if len(min_hosting_children) >= num_hosts:
            random.shuffle(min_hosting_children)
            return min_hosting_children[:num_hosts]
        
        # If not enough with minimum, take all min hosting children and select more
        selected_hosts = min_hosting_children.copy()
        remaining_needed = num_hosts - len(selected_hosts)
        
        # Get candidates with next lowest hosting count
        next_hosting_candidates = [child for child in candidates 
                                 if child.hosting_count == min_hosting + 1 
                                 and child not in selected_hosts]
        
        if len(next_hosting_candidates) >= remaining_needed:
            random.shuffle(next_hosting_candidates)
            selected_hosts.extend(next_hosting_candidates[:remaining_needed])
        else:
            # Keep expanding until we have enough hosts
            remaining_candidates = [child for child in candidates if child not in selected_hosts]
            random.shuffle(remaining_candidates)
            selected_hosts.extend(remaining_candidates[:remaining_needed])
        
        return selected_hosts
    
    def _build_group_around_host(self, host, available_children):
        """Build a 2B+2G group around the given host."""
        from group_optimizer import Group
        
        # Start with the host
        group_children = [host]
        
        # Determine what we need based on host gender
        if host.is_boy:
            boys_needed = 1  # Already have 1 boy (host)
            girls_needed = 2
        else:
            boys_needed = 2
            girls_needed = 1  # Already have 1 girl (host)
        
        # Get available boys and girls
        available_boys = [child for child in available_children if child.is_boy]
        available_girls = [child for child in available_children if child.is_girl]
        
        # Shuffle for randomization
        random.shuffle(available_boys)
        random.shuffle(available_girls)
        
        # Add boys
        for _ in range(min(boys_needed, len(available_boys))):
            group_children.append(available_boys.pop(0))
        
        # Add girls
        for _ in range(min(girls_needed, len(available_girls))):
            group_children.append(available_girls.pop(0))
        
        # Fill remaining spots if needed (should not happen with 12B+12G)
        while len(group_children) < 4:
            if available_boys:
                group_children.append(available_boys.pop(0))
            elif available_girls:
                group_children.append(available_girls.pop(0))
            else:
                break  # No more children available
        
        # Verify we have exactly 4 children
        if len(group_children) != 4:
            return None
        
        return Group(group_children)
    
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
        
        # 4. Host fairness with sharp penalty for hosting gaps >= 2
        hosting_counts = {}
        for group in groups:
            if group.host:
                hosting_counts[group.host.name] = group.host.hosting_count + 1
        
        if hosting_counts:
            max_hosting = max(hosting_counts.values())
            min_hosting = min(hosting_counts.values())
            hosting_gap = max_hosting - min_hosting
            
            if hosting_gap >= 2:
                # Apply severe penalty for hosting inequality >= 2
                penalty = -self.weights['host_fairness'] * hosting_gap * 10
                score += penalty
            else:
                # Small reward for good hosting distribution
                fairness = 1 - hosting_gap
                score += self.weights['host_fairness'] * fairness
        
        # 5. Hosting break balance (minimize consecutive hosting)
        if iteration_num > 1:
            break_balance_score = self._calculate_hosting_break_balance(groups, iteration_num, previous_iterations)
            score += self.weights['hosting_break_balance'] * break_balance_score
        
        # 6. Meeting fairness
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
    
    def _calculate_hosting_break_balance(self, groups, iteration_num, previous_iterations):
        """Calculate hosting break balance score using squared deviation penalty."""
        if iteration_num <= 1:
            return 0.0
        
        # Get current hosts in this iteration
        current_hosts = []
        for group in groups:
            if group.host:
                current_hosts.append(group.host)
        
        if not current_hosts:
            return 0.0
        
        # Calculate hosting breaks for children who have hosted multiple times
        all_hosting_breaks = []
        
        # Build complete hosting history for all children
        all_children_hosting = {}
        
        # Add previous iterations hosting
        for iter_idx, iteration in enumerate(previous_iterations, 1):
            for group in iteration:
                if group.host:
                    child_name = group.host.name
                    if child_name not in all_children_hosting:
                        all_children_hosting[child_name] = []
                    all_children_hosting[child_name].append(iter_idx)
        
        # Add current iteration hosting
        for host in current_hosts:
            if host.name not in all_children_hosting:
                all_children_hosting[host.name] = []
            all_children_hosting[host.name].append(iteration_num)
        
        # Calculate breaks for children with multiple hostings
        for child_name, hosting_iterations in all_children_hosting.items():
            if len(hosting_iterations) > 1:
                sorted_iterations = sorted(hosting_iterations)
                for i in range(1, len(sorted_iterations)):
                    break_length = sorted_iterations[i] - sorted_iterations[i-1] - 1
                    all_hosting_breaks.append(break_length)
        
        if not all_hosting_breaks:
            return 0.0  # No breaks to evaluate yet
        
        # Calculate average break length
        average_break = sum(all_hosting_breaks) / len(all_hosting_breaks)
        
        # Calculate penalty for current hosts' new breaks
        total_penalty = 0.0
        for host in current_hosts:
            host_iterations = all_children_hosting.get(host.name, [])
            if len(host_iterations) > 1:
                # Get the most recent break (which includes this iteration)
                sorted_iterations = sorted(host_iterations)
                latest_break = sorted_iterations[-1] - sorted_iterations[-2] - 1
                
                # Apply squared deviation penalty
                deviation = latest_break - average_break
                penalty = -(deviation ** 2)
                total_penalty += penalty
        
        # Normalize by number of current hosts
        return total_penalty / len(current_hosts) if current_hosts else 0.0
    
    def _get_perfect_score(self):
        """Calculate the theoretical perfect score."""
        return (self.weights['gender_balance'] * 6 +     # Perfect gender balance
                self.weights['hosting_break_balance'] +   # Perfect break balance
                self.weights['host_rotation'] +           # Perfect host rotation
                self.weights['group_diversity'] +         # Perfect diversity
                self.weights['host_fairness'] +           # Perfect host fairness
                self.weights['meeting_fairness'])         # Perfect meeting fairness
