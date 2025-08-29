"""
Constraint Solver Module
Implements backtracking algorithm with weighted constraint satisfaction.
"""

import random
import os
from datetime import datetime
from itertools import combinations


class ConstraintSolver:
    """Implements constraint satisfaction with backtracking for group optimization."""
    
    def __init__(self, config):
        self.config = config
        self.weights = config['weights']
        self.constraints = config['constraints']
        self.algorithm = config['algorithm']
        
        # Setup debug logging
        self.debug_log = []
        self.log_debug("=== ConstraintSolver Debug Log Started ===")
        self.log_debug(f"Weights: {self.weights}")
        self.log_debug(f"Constraints: {self.constraints}")
    
    def log_debug(self, message):
        """Add a debug message to the log."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self.debug_log.append(f"[{timestamp}] {message}")
    
    def write_debug_log(self, filepath):
        """Write the debug log to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("CONSTRAINT SOLVER DEBUG LOG\n")
                f.write("=" * 50 + "\n\n")
                for entry in self.debug_log:
                    f.write(entry + "\n")
        except Exception as e:
            print(f"Warning: Could not write debug log: {e}")
    
    def solve(self, children, iteration_num, previous_iterations):
        """Solve the constraint satisfaction problem to create optimal groups."""
        self.current_iteration = iteration_num  # Store for use in other methods
        self.log_debug(f"\n=== SOLVING ITERATION {iteration_num} ===")
        self.log_debug(f"Children: {[child.name for child in children]}")
        self.log_debug(f"Previous iterations: {len(previous_iterations)}")
        
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
        
        # Step 3: Comprehensive validation before returning solution
        validation_result = self._validate_iteration_integrity(groups, all_children)
        if not validation_result["valid"]:
            self.log_debug(f"Validation failed: {validation_result['errors']}")
            return None  # Invalid solution, reject it
        
        return groups
    
    def _select_hosts(self, all_children, num_hosts):
        """Select hosts fairly based on hosting counts and break lengths."""
        self.log_debug(f"\n--- Selecting {num_hosts} hosts ---")
        
        # Calculate break lengths for all children
        self.log_debug(f"\n--- Calculating break lengths for iteration {self.current_iteration} ---")
        children_with_breaks = []
        for child in all_children:
            break_length = self._calculate_break_length(child)
            children_with_breaks.append((child, break_length))
            if child.hosting_count == 0:
                self.log_debug(f"  {child.name}: never hosted, break length = {break_length}")
            else:
                last_hosting = max(child.hosting_iterations) if child.hosting_iterations else 0
                self.log_debug(f"  {child.name}: last hosted in iteration {last_hosting}, break length = {break_length}")
        
        # Sort children by (hosting_count, -break_length, name) 
        # -break_length so longer breaks come first (higher priority)
        candidates = sorted(children_with_breaks, 
                          key=lambda x: (x[0].hosting_count, -x[1], x[0].name))
        
        # Log the complete sorting criteria
        self.log_debug(f"\n--- Children sorted by (hosting_count, break_length, name) ---")
        for child, break_length in candidates:
            self.log_debug(f"  {child.name}: hosting={child.hosting_count}, break={break_length}")
        
        # Log hosting counts for reference
        hosting_info = [(child.name, child.hosting_count) for child, _ in candidates]
        self.log_debug(f"\nChildren by hosting count: {hosting_info}")
        
        # Find the minimum hosting count
        min_hosting = candidates[0][0].hosting_count
        self.log_debug(f"Minimum hosting count: {min_hosting}")
        
        # Get all children with the minimum hosting count
        min_hosting_children = [(child, break_len) for child, break_len in candidates 
                               if child.hosting_count == min_hosting]
        self.log_debug(f"Children with min hosting: {[child.name for child, _ in min_hosting_children]}")
        
        # Select hosts with detailed reasoning
        self.log_debug(f"\n--- Host selection with reasoning ---")
        selected_hosts = []
        
        if len(min_hosting_children) >= num_hosts:
            # Take the first num_hosts from sorted list (best break lengths)
            for i, (child, break_len) in enumerate(min_hosting_children):
                if i < num_hosts:
                    selected_hosts.append(child)
                    consecutive = break_len == 0 and child.hosting_count > 0
                    reason = f"hosting={child.hosting_count}, break={break_len}"
                    if consecutive:
                        reason += " (consecutive hosting)"
                    self.log_debug(f"  ✓ {child.name}: {reason}")
                else:
                    self.log_debug(f"  ✗ {child.name}: hosting={child.hosting_count}, break={break_len} (not needed)")
        else:
            # Take all min hosting children
            for child, break_len in min_hosting_children:
                selected_hosts.append(child)
                consecutive = break_len == 0 and child.hosting_count > 0
                reason = f"hosting={child.hosting_count}, break={break_len}"
                if consecutive:
                    reason += " (consecutive hosting)"
                self.log_debug(f"  ✓ {child.name}: {reason}")
            
            remaining_needed = num_hosts - len(selected_hosts)
            self.log_debug(f"\nNeed {remaining_needed} more hosts from higher hosting counts:")
            
            # Get remaining candidates sorted by break length
            remaining_candidates = [(child, break_len) for child, break_len in candidates 
                                  if child not in selected_hosts]
            
            for i, (child, break_len) in enumerate(remaining_candidates):
                if i < remaining_needed:
                    selected_hosts.append(child)
                    consecutive = break_len == 0 and child.hosting_count > 0
                    reason = f"hosting={child.hosting_count}, break={break_len}"
                    if consecutive:
                        reason += " (consecutive hosting)"
                    self.log_debug(f"  ✓ {child.name}: {reason}")
                elif i < remaining_needed + 3:  # Show a few rejected for context
                    self.log_debug(f"  ✗ {child.name}: hosting={child.hosting_count}, break={break_len} (not needed)")
        
        # Log consecutive hosting prevention summary
        consecutive_count = sum(1 for host in selected_hosts 
                              if self._calculate_break_length(host) == 0 and host.hosting_count > 0)
        
        self.log_debug(f"\n--- Consecutive hosting summary ---")
        if consecutive_count == 0:
            self.log_debug("  No consecutive hosting detected ✓")
        else:
            self.log_debug(f"  {consecutive_count} consecutive hosting cases detected")
            for host in selected_hosts:
                if self._calculate_break_length(host) == 0 and host.hosting_count > 0:
                    last_hosting = max(host.hosting_iterations)
                    self.log_debug(f"    {host.name}: hosted in iteration {last_hosting}, now iteration {self.current_iteration}")
        
        # Log break distribution in final selection
        break_lengths = [self._calculate_break_length(host) for host in selected_hosts]
        break_lengths_filtered = [b for b in break_lengths if b < 999]  # Exclude first-time hosters
        
        self.log_debug(f"\n--- Selected hosts break summary ---")
        if break_lengths_filtered:
            avg_break = sum(break_lengths_filtered) / len(break_lengths_filtered)
            min_break = min(break_lengths_filtered)
            max_break = max(break_lengths_filtered) if max(break_lengths_filtered) < 999 else "N/A (first-time)"
            self.log_debug(f"  Average break length: {avg_break:.1f} iterations")
            self.log_debug(f"  Minimum break length: {min_break} iterations")
            self.log_debug(f"  Maximum break length: {max_break}")
        
        first_time_count = sum(1 for b in break_lengths if b >= 999)
        if first_time_count > 0:
            self.log_debug(f"  First-time hosts: {first_time_count}")
        
        self.log_debug(f"\nFinal selected hosts: {[host.name for host in selected_hosts]}")
        return selected_hosts
    
    def _calculate_break_length(self, child):
        """Calculate the number of iterations since the child last hosted."""
        if not child.hosting_iterations:
            return 999  # High value for children who have never hosted
        
        last_hosting_iteration = max(child.hosting_iterations)
        return self.current_iteration - last_hosting_iteration - 1
    
    def _validate_iteration_integrity(self, groups, original_children):
        """Comprehensive validation to ensure all children appear exactly once per iteration."""
        self.log_debug(f"\n--- Comprehensive iteration validation ---")
        
        errors = []
        warnings = []
        
        # Basic structure validation
        if not groups:
            errors.append("No groups generated")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        if len(groups) != 6:
            errors.append(f"Expected 6 groups, got {len(groups)}")
        
        # Collect all children from all groups
        all_assigned_children = []
        group_sizes = []
        
        for i, group in enumerate(groups):
            if not group or not hasattr(group, 'children'):
                errors.append(f"Group {i+1} is invalid or has no children attribute")
                continue
            
            group_children = group.children if hasattr(group, 'children') else []
            group_sizes.append(len(group_children))
            all_assigned_children.extend(group_children)
            
            # Validate individual group size
            if len(group_children) != 4:
                errors.append(f"Group {i+1} has {len(group_children)} children, expected 4")
            
            # Validate group gender balance
            boys_in_group = sum(1 for child in group_children if child.is_boy)
            girls_in_group = sum(1 for child in group_children if child.is_girl)
            
            if boys_in_group != 2 or girls_in_group != 2:
                warnings.append(f"Group {i+1} has {boys_in_group}B+{girls_in_group}G (expected 2B+2G)")
        
        # Check total children count
        total_assigned = len(all_assigned_children)
        expected_total = len(original_children)
        
        self.log_debug(f"  Total children assigned: {total_assigned}")
        self.log_debug(f"  Expected total children: {expected_total}")
        
        if total_assigned != expected_total:
            errors.append(f"Total assigned children ({total_assigned}) != expected ({expected_total})")
        
        # Check for duplicate children within iteration
        assigned_names = [child.name for child in all_assigned_children]
        unique_names = set(assigned_names)
        
        if len(assigned_names) != len(unique_names):
            duplicates = [name for name in assigned_names if assigned_names.count(name) > 1]
            errors.append(f"Duplicate children in iteration: {set(duplicates)}")
            self.log_debug(f"  Duplicate children detected: {set(duplicates)}")
        
        # Check for missing children
        original_names = set(child.name for child in original_children)
        assigned_names_set = set(assigned_names)
        
        missing_children = original_names - assigned_names_set
        extra_children = assigned_names_set - original_names
        
        if missing_children:
            errors.append(f"Missing children: {missing_children}")
            self.log_debug(f"  Missing children: {missing_children}")
        
        if extra_children:
            errors.append(f"Unknown children assigned: {extra_children}")
            self.log_debug(f"  Unknown children: {extra_children}")
        
        # Check group size distribution
        if group_sizes:
            min_size = min(group_sizes)
            max_size = max(group_sizes)
            avg_size = sum(group_sizes) / len(group_sizes)
            
            self.log_debug(f"  Group sizes: {group_sizes}")
            self.log_debug(f"  Size range: {min_size}-{max_size}, average: {avg_size:.1f}")
            
            if min_size != 4 or max_size != 4:
                warnings.append(f"Inconsistent group sizes: {group_sizes}")
        
        # Summary logging
        if errors:
            self.log_debug(f"  ✗ Validation FAILED: {len(errors)} error(s)")
            for error in errors:
                self.log_debug(f"    - {error}")
        else:
            self.log_debug(f"  ✓ Validation PASSED: All children assigned correctly")
        
        if warnings:
            self.log_debug(f"  ⚠ Warnings: {len(warnings)}")
            for warning in warnings:
                self.log_debug(f"    - {warning}")
        
        # Detailed assignment verification (when successful)
        if not errors:
            self.log_debug(f"  Children assignment verification:")
            for i, group in enumerate(groups):
                child_names = [child.name for child in group.children]
                self.log_debug(f"    Group {i+1}: {child_names}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_assigned": total_assigned,
            "group_sizes": group_sizes
        }
    
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
        
        # 3. Progressive meeting diversity penalty (exponentially punishes repeated pairings)
        self.log_debug(f"\n=== PROGRESSIVE PENALTY CALCULATION (Iteration {iteration_num}) ===")
        progressive_penalty = self._calculate_progressive_meeting_penalty(groups)
        self.log_debug(f"Progressive penalty calculated: {progressive_penalty:.2f}")
        score -= progressive_penalty  # Subtract penalty from score
        self.log_debug(f"Score after penalty deduction: {score:.2f}")
        
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
        break_balance_contribution = 0
        if iteration_num > 1:
            break_balance_score = self._calculate_hosting_break_balance(groups, iteration_num, previous_iterations)
            break_balance_contribution = self.weights['hosting_break_balance'] * break_balance_score
            score += break_balance_contribution
        
        # 6. Meeting fairness
        meeting_fairness = self._calculate_meeting_fairness(groups)
        meeting_contribution = self.weights['meeting_fairness'] * meeting_fairness
        score += meeting_contribution
        
        # Log final score breakdown for this solution
        current_host_names = [group.host.name for group in groups if group.host]
        self.log_debug(f"\n=== FINAL SOLUTION SCORE BREAKDOWN ===")
        self.log_debug(f"Solution for hosts: {current_host_names}")
        self.log_debug(f"  Gender balance contribution: {score - (-progressive_penalty) - break_balance_contribution - meeting_contribution + progressive_penalty:.2f}")
        self.log_debug(f"  Progressive meeting penalty: -{progressive_penalty:.2f}")
        self.log_debug(f"  Break balance contribution: {break_balance_contribution:.2f}")
        self.log_debug(f"  Meeting fairness contribution: {meeting_contribution:.2f}")
        self.log_debug(f"  TOTAL FINAL SCORE: {score:.2f}")
        self.log_debug(f"=" * 50)
        
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
    
    def _calculate_progressive_meeting_penalty(self, groups):
        """Calculate progressive penalty based on how many times children have already met."""
        total_penalty = 0
        
        self.log_debug(f"📊 PROGRESSIVE PENALTY METHOD CALLED")
        self.log_debug(f"   Number of groups to evaluate: {len(groups)}")
        
        # Get meeting diversity configuration
        meeting_config = self.config.get('meeting_diversity', {
            'base_weight': 50,
            'penalty_exponent': 2.5,
            'max_penalty_cap': 5000,
            'same_gender_meeting_penalty_multiplier': 3.0
        })
        
        base_weight = meeting_config['base_weight']
        exponent = meeting_config['penalty_exponent']
        max_cap = meeting_config['max_penalty_cap']
        same_gender_multiplier = meeting_config['same_gender_meeting_penalty_multiplier']
        
        self.log_debug(f"📋 Configuration loaded:")
        self.log_debug(f"   base_weight={base_weight}, exponent={exponent}, max_cap={max_cap}")
        self.log_debug(f"   same_gender_multiplier={same_gender_multiplier}")
        self.log_debug(f"   Full config object: {meeting_config}")
        
        penalty_details = []
        pair_count = 0
        penalties_applied = 0
        same_gender_penalties = 0
        cross_gender_penalties = 0
        same_gender_penalty_total = 0
        cross_gender_penalty_total = 0
        
        # Calculate penalty for each pair in current groups
        for group_idx, group in enumerate(groups):
            group_children = [child.name for child in group.children]
            self.log_debug(f"📦 Evaluating Group {group_idx + 1}: {group_children}")
            
            for i in range(len(group.children)):
                for j in range(i + 1, len(group.children)):
                    child1 = group.children[i]
                    child2 = group.children[j]
                    pair_count += 1
                    
                    # Get current meeting count between these two children
                    meeting_count = 0
                    if child2.name in child1.meetings:
                        meeting_count = child1.meetings[child2.name]
                    
                    # Determine if this is a same-gender pairing
                    same_gender = (child1.is_boy and child2.is_boy) or (child1.is_girl and child2.is_girl)
                    gender_type = "same-gender" if same_gender else "cross-gender"
                    gender_emoji = "👦👦" if (child1.is_boy and child2.is_boy) else "👧👧" if (child1.is_girl and child2.is_girl) else "👦👧"
                        
                    # Always log the pair, even if no previous meetings
                    if meeting_count == 0:
                        self.log_debug(f"   👥 {child1.name}-{child2.name} ({gender_emoji} {gender_type}): No previous meetings (penalty: 0)")
                    else:
                        # Calculate base penalty: base_weight * (meeting_count ^ exponent)
                        base_penalty = base_weight * (meeting_count ** exponent)
                        
                        # Apply gender multiplier if same-gender
                        if same_gender:
                            penalty = base_penalty * same_gender_multiplier
                            same_gender_penalties += 1
                            same_gender_penalty_total += penalty
                            multiplier_text = f" × {same_gender_multiplier} (same-gender)"
                        else:
                            penalty = base_penalty
                            cross_gender_penalties += 1
                            cross_gender_penalty_total += penalty
                            multiplier_text = " (cross-gender)"
                        
                        # Apply cap if specified
                        original_penalty = penalty
                        if max_cap and penalty > max_cap:
                            penalty = max_cap
                            self.log_debug(f"   ⚠️  Penalty capped: {original_penalty:.1f} → {penalty:.1f}")
                        
                        total_penalty += penalty
                        penalties_applied += 1
                        penalty_details.append((child1.name, child2.name, meeting_count, penalty, same_gender))
                        
                        formula = f"{base_weight} × {meeting_count}^{exponent}{multiplier_text} = {penalty:.1f}"
                        self.log_debug(f"   🚨 {child1.name}-{child2.name} ({gender_emoji} {gender_type}): {meeting_count} meetings → {formula}")
        
        # Summary logging
        self.log_debug(f"📈 PENALTY CALCULATION SUMMARY:")
        self.log_debug(f"   Total pairs evaluated: {pair_count}")
        self.log_debug(f"   Pairs with penalties: {penalties_applied}")
        self.log_debug(f"   Pairs without penalties: {pair_count - penalties_applied}")
        self.log_debug(f"   Same-gender penalties: {same_gender_penalties} (total: {same_gender_penalty_total:.1f})")
        self.log_debug(f"   Cross-gender penalties: {cross_gender_penalties} (total: {cross_gender_penalty_total:.1f})")
        
        if penalty_details:
            # Sort by penalty for better readability
            penalty_details.sort(key=lambda x: x[3], reverse=True)
            self.log_debug(f"🔥 TOP PENALTIES (sorted by severity):")
            for child1, child2, count, penalty, is_same_gender in penalty_details[:10]:  # Show top 10
                gender_type = "same-gender" if is_same_gender else "cross-gender"
                multiplier_part = f" × {same_gender_multiplier}" if is_same_gender else ""
                formula = f"{base_weight} × {count}^{exponent}{multiplier_part} = {penalty:.1f}"
                self.log_debug(f"   {child1}-{child2} ({gender_type}): {count} meetings → {formula}")
        else:
            self.log_debug("✅ No previous meetings found, no penalties applied")
        
        self.log_debug(f"💰 TOTAL PROGRESSIVE MEETING PENALTY: {total_penalty:.1f}")
        self.log_debug(f"📊 PROGRESSIVE PENALTY CALCULATION COMPLETE")
        
        return total_penalty
    
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
        self.log_debug(f"\n--- Calculating hosting break balance for iteration {iteration_num} ---")
        
        if iteration_num <= 1:
            self.log_debug("Skipping break balance for iteration 1")
            return 0.0
        
        # Get current hosts in this iteration
        current_hosts = []
        for group in groups:
            if group.host:
                current_hosts.append(group.host)
        
        self.log_debug(f"Current hosts: {[host.name for host in current_hosts]}")
        
        if not current_hosts:
            self.log_debug("No hosts found, returning 0.0")
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
        
        self.log_debug(f"Complete hosting history: {all_children_hosting}")
        
        # Calculate breaks for children with multiple hostings
        for child_name, hosting_iterations in all_children_hosting.items():
            if len(hosting_iterations) > 1:
                sorted_iterations = sorted(hosting_iterations)
                for i in range(1, len(sorted_iterations)):
                    break_length = sorted_iterations[i] - sorted_iterations[i-1] - 1
                    all_hosting_breaks.append(break_length)
        
        if not all_hosting_breaks:
            self.log_debug("No hosting breaks to evaluate yet")
            return 0.0  # No breaks to evaluate yet
        
        # Calculate average break length
        average_break = sum(all_hosting_breaks) / len(all_hosting_breaks)
        self.log_debug(f"All hosting breaks: {all_hosting_breaks}")
        self.log_debug(f"Average break length: {average_break:.2f}")
        
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
                
                self.log_debug(f"Host {host.name}: iterations {sorted_iterations}, latest break={latest_break}, deviation={deviation:.2f}, penalty={penalty:.2f}")
            else:
                self.log_debug(f"Host {host.name}: only hosted once, no penalty")
        
        final_score = total_penalty / len(current_hosts) if current_hosts else 0.0
        self.log_debug(f"Total penalty: {total_penalty:.2f}, Final break balance score: {final_score:.2f}")
        
        # Normalize by number of current hosts
        return final_score
    
    def _get_perfect_score(self):
        """Calculate the theoretical perfect score."""
        return (self.weights['gender_balance'] * 6 +     # Perfect gender balance
                self.weights['hosting_break_balance'] +   # Perfect break balance
                self.weights['host_rotation'] +           # Perfect host rotation
                self.weights['group_diversity'] +         # Perfect diversity
                self.weights['host_fairness'] +           # Perfect host fairness
                self.weights['meeting_fairness'])         # Perfect meeting fairness
