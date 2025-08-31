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
        
        # Centralized triplet history tracking
        self.triplet_history = {}  # {triplet_key: [iteration_numbers]}
        
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
    
    def add_triplet_to_history(self, children, iteration_num):
        """Add all triplets from groups to centralized history."""
        from itertools import combinations
        
        # Generate all possible triplets from the group (4 choose 3 = 4 triplets)
        for triplet_children in combinations(children, 3):
            triplet_names = [child.name for child in triplet_children]
            triplet_key = tuple(sorted(triplet_names))
            
            # Add this iteration to the centralized triplet history
            if triplet_key not in self.triplet_history:
                self.triplet_history[triplet_key] = []
            self.triplet_history[triplet_key].append(iteration_num)
    
    def get_triplet_iterations(self, triplet_key):
        """Get all iteration numbers where a triplet has met."""
        return self.triplet_history.get(triplet_key, [])
    
    def solve(self, children, iteration_num, previous_iterations):
        """Solve the constraint satisfaction problem to create optimal groups using comprehensive search."""
        self.current_iteration = iteration_num  # Store for use in other methods
        self.log_debug(f"\n=== SOLVING ITERATION {iteration_num} ===")
        self.log_debug(f"Children: {[child.name for child in children]}")
        self.log_debug(f"Previous iterations: {len(previous_iterations)}")
        
        # Get search intensity parameter
        search_intensity = self.algorithm.get('solution_search_intensity', 1000)
        progress_interval = self.algorithm.get('progress_reporting_interval', 100)
        console_progress_interval = 5000  # Update console every 5,000 attempts
        
        self.log_debug(f"🔍 COMPREHENSIVE SEARCH MODE: {search_intensity} solution attempts")
        self.log_debug(f"📊 Progress reporting every {progress_interval} attempts")
        
        boys = [child for child in children if child.is_boy]
        girls = [child for child in children if child.is_girl]
        
        best_solution = None
        best_score = float('-inf')
        valid_solutions_found = 0
        attempts = 0
        
        # Enhanced tracking for logging analysis
        top_solutions = []  # Track top 5 solutions
        termination_reason = "max_attempts_reached"
        score_improvements = 0
        
        # Comprehensive search: try many solutions and pick the absolute best
        while attempts < search_intensity:
            attempts += 1
            
            # Generate a candidate solution
            solution = self._generate_candidate_solution(boys, girls, iteration_num, previous_iterations)
            
            if solution:
                valid_solutions_found += 1
                score = self._evaluate_solution(solution, iteration_num, previous_iterations)
                
                if score > best_score:
                    best_score = score
                    best_solution = solution
                    score_improvements += 1
                    self.log_debug(f"🏆 NEW BEST SOLUTION found at attempt {attempts}: score={score:.2f}")
                    
                    # Track top solutions for analysis
                    top_solutions.append({
                        'attempt': attempts,
                        'score': score,
                        'solution': solution
                    })
                    # Keep only top 5
                    top_solutions.sort(key=lambda x: x['score'], reverse=True)
                    if len(top_solutions) > 5:
                        top_solutions = top_solutions[:5]
                
                # Progress reporting
                if attempts % progress_interval == 0:
                    self.log_debug(f"📈 Progress: {attempts}/{search_intensity} attempts, {valid_solutions_found} valid solutions, best score: {best_score:.2f}")
                
                # Console progress reporting (every 5,000 attempts)
                if attempts % console_progress_interval == 0:
                    percentage = (attempts / search_intensity) * 100
                    print(f"\r  Creating iteration {iteration_num}... ({percentage:.0f}% complete - {attempts:,}/{search_intensity:,} attempts)", end='', flush=True)
            
            # No early termination - run all attempts to find truly optimal solutions
        
        # Enhanced search analysis and logging
        self.log_debug(f"\n=== COMPREHENSIVE SEARCH COMPLETED ===")
        self.log_debug(f"🔍 SEARCH STATISTICS:")
        self.log_debug(f"   Total attempts: {attempts}/{search_intensity}")
        self.log_debug(f"   Valid solutions found: {valid_solutions_found}")
        self.log_debug(f"   Success rate: {(valid_solutions_found/attempts)*100:.1f}%")
        self.log_debug(f"   Score improvements: {score_improvements}")
        self.log_debug(f"   Termination reason: {termination_reason}")
        self.log_debug(f"   Best score achieved: {best_score:.2f}")
        
        if best_solution:
            perfect_score = self._get_perfect_score()
            quality_percentage = (best_score / perfect_score) * 100
            self.log_debug(f"   Solution quality: {quality_percentage:.1f}% of theoretical perfect score")
            
            # Enhanced perfect score breakdown
            self._log_perfect_score_breakdown(perfect_score)
            
            # Top solutions analysis
            self._log_top_solutions_analysis(top_solutions)
            
            # Meeting distribution analysis for best solution
            self._log_meeting_distribution_analysis(best_solution)
            
            # Penalty effectiveness analysis
            self._log_penalty_effectiveness_analysis(best_solution, iteration_num, previous_iterations)
        
        # Final search outcome logging
        self.log_debug(f"\n⏰ SEARCH OUTCOME: Completed all {search_intensity} attempts")
        
        # Clear the progress line and show completion
        print(f"\r  Creating iteration {iteration_num}... (100% complete - {search_intensity:,}/{search_intensity:,} attempts)")
            
        return best_solution
    
    def _generate_candidate_solution(self, boys, girls, iteration_num, previous_iterations):
        """Generate a candidate solution using host-first construction."""
        from group_optimizer import Group
        
        # Step 1: Randomize child order to eliminate systematic bias
        all_children = boys + girls
        random.shuffle(all_children)  # Randomize the complete child list
        self.log_debug(f"🎲 Randomized complete child order for solution generation")
        
        # Step 2: Select 6 hosts fairly based on hosting counts
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
        """Select hosts based purely on hosting count fairness - break constraints evaluated in solution scoring."""
        self.log_debug(f"\n--- Selecting {num_hosts} hosts (hosting count fairness only) ---")
        
        # STEP 1: Randomize the order of children to eliminate alphabetical bias
        randomized_children = all_children.copy()
        random.shuffle(randomized_children)
        
        original_order = [child.name for child in all_children]
        randomized_order = [child.name for child in randomized_children]
        self.log_debug(f"\n🎲 RANDOMIZATION APPLIED:")
        self.log_debug(f"   Original order: {original_order[:6]}... (first 6)")
        self.log_debug(f"   Randomized order: {randomized_order[:6]}... (first 6)")
        
        # Sort children by hosting count only (no break filtering)
        candidates = sorted(randomized_children, key=lambda x: x.hosting_count)
        
        # Log the complete sorting criteria
        self.log_debug(f"\n--- Children sorted by hosting count only (break evaluation moved to solution scoring) ---")
        for child in candidates:
            break_length = self._calculate_break_length(child)
            self.log_debug(f"  {child.name}: hosting={child.hosting_count}, break={break_length} (will be evaluated in solution scoring)")
        
        # Log hosting counts for reference
        hosting_info = [(child.name, child.hosting_count) for child in candidates]
        self.log_debug(f"\nChildren by hosting count: {hosting_info}")
        
        # Find the minimum hosting count
        min_hosting = candidates[0].hosting_count
        self.log_debug(f"Minimum hosting count: {min_hosting}")
        
        # Get all children with the minimum hosting count
        min_hosting_children = [child for child in candidates if child.hosting_count == min_hosting]
        self.log_debug(f"Children with min hosting: {[child.name for child in min_hosting_children]}")
        
        # OPTIMIZATION: Filter out children with terrible break lengths (0-1 iterations) 
        # if we have enough good alternatives. This prevents wasting time on guaranteed losers.
        self.log_debug(f"\n--- Intelligent break filtering to avoid wasted simulations ---")
        
        # Categorize children by break quality
        excellent_breaks = []  # 3+ iterations
        acceptable_breaks = []  # 2 iterations 
        poor_breaks = []       # 0-1 iterations
        
        for child in min_hosting_children:
            break_length = self._calculate_break_length(child)
            if break_length >= 3:
                excellent_breaks.append(child)
            elif break_length == 2:
                acceptable_breaks.append(child)
            else:  # 0-1 iterations
                poor_breaks.append(child)
        
        self.log_debug(f"Break quality distribution:")
        self.log_debug(f"  Excellent (3+ breaks): {len(excellent_breaks)} children")
        self.log_debug(f"  Acceptable (2 breaks): {len(acceptable_breaks)} children")
        self.log_debug(f"  Poor (0-1 breaks): {len(poor_breaks)} children")
        
        # Smart selection: Use poor breaks only if absolutely necessary
        available_good_hosts = excellent_breaks + acceptable_breaks
        
        if len(available_good_hosts) >= num_hosts:
            # We have enough good hosts - ignore poor break hosts entirely
            self.log_debug(f"✓ Using only good break hosts ({len(available_good_hosts)} available, {num_hosts} needed)")
            candidate_pool = available_good_hosts
        else:
            # Need some poor break hosts, but minimize them
            needed_poor = num_hosts - len(available_good_hosts)
            self.log_debug(f"⚠️ Need {needed_poor} poor break hosts (insufficient good alternatives)")
            candidate_pool = available_good_hosts + poor_breaks[:needed_poor]
        
        # Select hosts with detailed reasoning
        self.log_debug(f"\n--- Host selection with break optimization ---")
        selected_hosts = []
        
        if len(candidate_pool) >= num_hosts:
            # Sufficient candidates after filtering - randomize selection
            random.shuffle(candidate_pool)
            selected_hosts = candidate_pool[:num_hosts]
            
            self.log_debug(f"✓ Selected {num_hosts} hosts using break-optimized selection")
            for i, host in enumerate(selected_hosts):
                break_length = self._calculate_break_length(host)
                break_quality = "excellent" if break_length >= 3 else "acceptable" if break_length == 2 else "poor"
                self.log_debug(f"  ✓ {host.name}: hosting={host.hosting_count}, break={break_length} ({break_quality})")
                
            # Show a few rejected for context
            remaining_candidates = [c for c in candidate_pool if c not in selected_hosts]
            for child in remaining_candidates[:3]:  # Show first 3 rejected
                break_length = self._calculate_break_length(child)
                break_quality = "excellent" if break_length >= 3 else "acceptable" if break_length == 2 else "poor"
                self.log_debug(f"  ✗ {child.name}: hosting={child.hosting_count}, break={break_length} ({break_quality}) - not selected")
                
            # Show any poor break hosts that were completely filtered out
            if len(available_good_hosts) >= num_hosts and poor_breaks:
                self.log_debug(f"  Filtered out {len(poor_breaks)} poor break hosts: {[c.name for c in poor_breaks][:5]}...")
        else:
            # Use all available candidates (should not happen with proper filtering)
            selected_hosts = candidate_pool.copy()
            self.log_debug(f"Using all {len(candidate_pool)} available candidates")
            
            for host in selected_hosts:
                break_length = self._calculate_break_length(host)
                break_quality = "excellent" if break_length >= 3 else "acceptable" if break_length == 2 else "poor"
                self.log_debug(f"  ✓ {host.name}: hosting={host.hosting_count}, break={break_length} ({break_quality})")
            
            remaining_needed = num_hosts - len(selected_hosts)
            if remaining_needed > 0:
                self.log_debug(f"\nNeed {remaining_needed} more hosts from next hosting count level:")
                
                # Get children from next hosting count level with same break optimization
                remaining_candidates = [child for child in candidates if child not in selected_hosts]
                
                # Apply same break filtering to remaining candidates
                remaining_good = []
                remaining_poor = []
                for child in remaining_candidates:
                    break_length = self._calculate_break_length(child)
                    if break_length >= 2:
                        remaining_good.append(child)
                    else:
                        remaining_poor.append(child)
                
                # Prefer good breaks, use poor only if necessary
                additional_hosts = remaining_good[:remaining_needed]
                if len(additional_hosts) < remaining_needed:
                    additional_hosts.extend(remaining_poor[:remaining_needed - len(additional_hosts)])
                
                random.shuffle(additional_hosts)
                selected_hosts.extend(additional_hosts)
                
                for child in additional_hosts:
                    break_length = self._calculate_break_length(child)
                    break_quality = "excellent" if break_length >= 3 else "acceptable" if break_length == 2 else "poor"
                    self.log_debug(f"  ✓ {child.name}: hosting={child.hosting_count}, break={break_length} ({break_quality}) - from next level")
        
        self.log_debug(f"\nFinal selected hosts: {[host.name for host in selected_hosts]}")
        self.log_debug(f"Break constraints will be evaluated during solution scoring phase")
        return selected_hosts
    
    def _calculate_break_length(self, child):
        """Calculate the number of iterations since the child last hosted."""
        if not child.hosting_iterations:
            return 999  # High value for children who have never hosted
        
        last_hosting_iteration = max(child.hosting_iterations)
        return self.current_iteration - last_hosting_iteration - 1
    
    def _evaluate_break_constraint(self, break_length, evaluation_type='penalty'):
        """Centralized break constraint evaluation - single source of truth for all break logic.
        
        Args:
            break_length: Number of iterations since last hosting
            evaluation_type: 'penalty' for selection scoring, 'balance' for fairness scoring, 'acceptable' for validation
        
        Returns:
            penalty score (negative values), balance score (0-1), or boolean acceptability
        """
        break_config = self.config.get('hosting_break_penalties', {
            'break_0_penalty': -1000,
            'break_1_penalty': -500,
            'break_2_penalty': -50,
            'break_3_plus_penalty': 0
        })
        
        if evaluation_type == 'penalty':
            # For host selection and solution scoring
            if break_length == 0:
                return break_config['break_0_penalty']
            elif break_length == 1:
                return break_config['break_1_penalty']
            elif break_length == 2:
                return break_config['break_2_penalty']
            else:  # break_length >= 3
                return break_config['break_3_plus_penalty']
                
        elif evaluation_type == 'balance':
            # For break balance fairness calculation (0 = worst, 1 = best)
            if break_length == 0:
                return 0.0  # Consecutive hosting = worst balance
            elif break_length == 1:
                return 0.2  # Very poor balance
            elif break_length == 2:
                return 0.8  # Good balance
            else:  # break_length >= 3
                return 1.0  # Perfect balance
                
        elif evaluation_type == 'acceptable':
            # For validation - determines if break is acceptable at all
            return break_length >= 0  # All breaks are acceptable now (penalties handle preference)
            
        else:
            raise ValueError(f"Unknown evaluation_type: {evaluation_type}")
    
    def _calculate_break_penalty(self, break_length):
        """Legacy compatibility function - redirects to centralized evaluation."""
        return self._evaluate_break_constraint(break_length, 'penalty')
    
    def _calculate_solution_break_penalty(self, groups):
        """Calculate break constraint penalties for all hosts in the solution."""
        total_penalty = 0
        
        self.log_debug("Evaluating break constraints for current solution:")
        
        for group_idx, group in enumerate(groups):
            if group.host:
                break_length = self._calculate_break_length(group.host)
                break_penalty = self._evaluate_break_constraint(break_length, 'penalty')
                total_penalty += break_penalty
                
                if break_penalty < 0:  # Only log penalties (negative values)
                    self.log_debug(f"  Group {group_idx + 1} - {group.host.name}: break={break_length}, penalty={break_penalty}")
                else:
                    self.log_debug(f"  Group {group_idx + 1} - {group.host.name}: break={break_length}, no penalty")
        
        self.log_debug(f"Total break constraint penalty: {total_penalty}")
        return total_penalty
    
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
        self.log_debug(f"Progressive pair penalty calculated: {progressive_penalty:.2f}")
        score -= progressive_penalty  # Subtract penalty from score
        
        # 3.5. Triplet diversity penalty (heavily punish repeated triplet formations)
        self.log_debug(f"\n=== TRIPLET PENALTY CALCULATION (Iteration {iteration_num}) ===")
        triplet_penalty = self._calculate_triplet_penalty(groups)
        self.log_debug(f"Triplet penalty calculated: {triplet_penalty:.2f}")
        score -= triplet_penalty  # Subtract triplet penalty from score
        
        # 3.6. Break constraint penalty (evaluate hosting break violations)
        self.log_debug(f"\n=== BREAK CONSTRAINT PENALTY CALCULATION (Iteration {iteration_num}) ===")
        break_penalty = self._calculate_solution_break_penalty(groups)
        self.log_debug(f"Break constraint penalty calculated: {break_penalty:.2f}")
        score += break_penalty  # Add penalty (already negative values) to score
        
        self.log_debug(f"Score after all penalties: {score:.2f}")
        
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
        self.log_debug(f"  Gender balance contribution: {score - (-progressive_penalty) - (-triplet_penalty) - break_balance_contribution - meeting_contribution + progressive_penalty + triplet_penalty:.2f}")
        self.log_debug(f"  Progressive pair penalty: -{progressive_penalty:.2f}")
        self.log_debug(f"  Triplet penalty: -{triplet_penalty:.2f}")
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
            'progression_type': 'gentle_linear',
            'progression_multiplier': 0.2,
            'same_gender_meeting_penalty_multiplier': 3.0
        })
        
        base_weight = meeting_config['base_weight']
        progression_type = meeting_config.get('progression_type', 'gentle_linear')
        progression_multiplier = meeting_config.get('progression_multiplier', 0.2)
        same_gender_multiplier = meeting_config['same_gender_meeting_penalty_multiplier']
        
        self.log_debug(f"📋 Configuration loaded:")
        self.log_debug(f"   base_weight={base_weight}, progression_type={progression_type}, progression_multiplier={progression_multiplier}")
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
                        # Calculate base penalty using gentle linear progression: base_weight * meeting_count * (1 + meeting_count * progression_multiplier)
                        base_penalty = base_weight * meeting_count * (1 + meeting_count * progression_multiplier)
                        
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
                        
                        total_penalty += penalty
                        penalties_applied += 1
                        penalty_details.append((child1.name, child2.name, meeting_count, penalty, same_gender))
                        
                        linear_factor = 1 + meeting_count * progression_multiplier
                        formula = f"{base_weight} × {meeting_count} × {linear_factor:.1f}{multiplier_text} = {penalty:.1f}"
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
                linear_factor = 1 + count * progression_multiplier
                formula = f"{base_weight} × {count} × {linear_factor:.1f}{multiplier_part} = {penalty:.1f}"
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
        
        # Calculate balance score using centralized break evaluation
        total_balance_score = 0.0
        for host in current_hosts:
            host_iterations = all_children_hosting.get(host.name, [])
            if len(host_iterations) > 1:
                # Get the most recent break (which includes this iteration)
                sorted_iterations = sorted(host_iterations)
                latest_break = sorted_iterations[-1] - sorted_iterations[-2] - 1
                
                # Use centralized break evaluation for balance scoring
                balance_score = self._evaluate_break_constraint(latest_break, 'balance')
                total_balance_score += balance_score
                
                self.log_debug(f"Host {host.name}: iterations {sorted_iterations}, latest break={latest_break}, balance_score={balance_score:.2f}")
            else:
                # First time hosting gets perfect balance score
                total_balance_score += 1.0
                self.log_debug(f"Host {host.name}: first time hosting, balance_score=1.0")
        
        final_score = total_balance_score / len(current_hosts) if current_hosts else 0.0
        self.log_debug(f"Total balance score: {total_balance_score:.2f}, Final break balance score: {final_score:.2f}")
        
        # Normalize by number of current hosts
        return final_score
    
    def _calculate_triplet_penalty(self, groups):
        """Calculate progressive penalty for repeated triplet combinations with proximity-based adjustments."""
        from itertools import combinations
        
        total_penalty = 0
        
        # Get triplet diversity configuration
        triplet_config = self.config.get('triplet_diversity', {
            'base_weight': 500,
            'penalty_exponent': 3.5,
            'max_penalty_cap': 20000,
            'triplet_penalty_multiplier': 10.0,
            'proximity_penalties': {
                'gap_0_multiplier': 5.0,
                'gap_1_multiplier': 3.0,
                'gap_2_multiplier': 2.0,
                'gap_3_multiplier': 1.5,
                'gap_4_multiplier': 1.2,
                'gap_5_plus_multiplier': 1.0
            }
        })
        
        base_weight = triplet_config['base_weight']
        exponent = triplet_config['penalty_exponent']
        max_cap = triplet_config['max_penalty_cap']
        multiplier = triplet_config['triplet_penalty_multiplier']
        proximity_penalties = triplet_config['proximity_penalties']
        
        self.log_debug(f"🎯 TRIPLET PENALTY CONFIGURATION:")
        self.log_debug(f"   base_weight={base_weight}, exponent={exponent}, max_cap={max_cap}")
        self.log_debug(f"   triplet_multiplier={multiplier}")
        self.log_debug(f"   proximity_penalties={proximity_penalties}")
        
        triplet_penalties = 0
        triplets_evaluated = 0
        
        # Calculate penalty for each triplet in current groups
        for group_idx, group in enumerate(groups):
            group_children = [child.name for child in group.children]
            self.log_debug(f"🔍 Evaluating triplets in Group {group_idx + 1}: {group_children}")
            
            # Generate all possible triplets from this group (4 choose 3 = 4 triplets)
            for triplet_children in combinations(group.children, 3):
                triplets_evaluated += 1
                
                # Calculate how many times this specific triplet has met before
                triplet_names = [child.name for child in triplet_children]
                triplet_key = tuple(sorted(triplet_names))
                
                # Get triplet meeting history from centralized tracking
                triplet_iterations = self.get_triplet_iterations(triplet_key)
                
                triplet_meeting_count = len(triplet_iterations)
                
                if triplet_meeting_count > 0:
                    # Calculate proximity-based multiplier
                    proximity_multiplier = self._calculate_proximity_multiplier(triplet_iterations, proximity_penalties)
                    
                    # Apply progressive penalty for triplet recurrence with proximity adjustment
                    base_penalty = base_weight * (triplet_meeting_count ** exponent) * multiplier
                    proximity_adjusted_penalty = base_penalty * proximity_multiplier
                    capped_penalty = min(proximity_adjusted_penalty, max_cap)
                    total_penalty += capped_penalty
                    triplet_penalties += 1
                    
                    self.log_debug(f"   🚨 TRIPLET PENALTY: {triplet_key}")
                    self.log_debug(f"      Meeting iterations: {triplet_iterations}")
                    self.log_debug(f"      Meeting count: {triplet_meeting_count}")
                    self.log_debug(f"      Proximity multiplier: {proximity_multiplier:.2f}")
                    self.log_debug(f"      Base penalty: {base_weight} × {triplet_meeting_count}^{exponent} × {multiplier} = {base_penalty:.1f}")
                    self.log_debug(f"      Proximity adjusted: {base_penalty:.1f} × {proximity_multiplier:.2f} = {proximity_adjusted_penalty:.1f}")
                    self.log_debug(f"      Final penalty (capped): {capped_penalty:.1f}")
                else:
                    self.log_debug(f"   ✅ NEW TRIPLET: {triplet_key} (no penalty)")
        
        # Summary logging
        self.log_debug(f"\n🎯 TRIPLET PENALTY SUMMARY:")
        self.log_debug(f"   Total triplets evaluated: {triplets_evaluated}")
        self.log_debug(f"   Triplets with penalties: {triplet_penalties}")
        self.log_debug(f"   Total triplet penalty: {total_penalty:.2f}")
        
        return total_penalty

    def _calculate_proximity_multiplier(self, triplet_iterations, proximity_penalties):
        """Calculate proximity-based penalty multiplier based on iteration gaps."""
        if len(triplet_iterations) < 2:
            return 1.0  # No proximity penalty for single occurrence
        
        # Calculate minimum gap between any two meetings
        sorted_iterations = sorted(triplet_iterations)
        min_gap = float('inf')
        
        for i in range(1, len(sorted_iterations)):
            gap = sorted_iterations[i] - sorted_iterations[i-1] - 1
            min_gap = min(min_gap, gap)
        
        # Apply proximity multiplier based on minimum gap
        if min_gap == 0:
            multiplier = proximity_penalties['gap_0_multiplier']
        elif min_gap == 1:
            multiplier = proximity_penalties['gap_1_multiplier']
        elif min_gap == 2:
            multiplier = proximity_penalties['gap_2_multiplier']
        elif min_gap == 3:
            multiplier = proximity_penalties['gap_3_multiplier']
        elif min_gap == 4:
            multiplier = proximity_penalties['gap_4_multiplier']
        else:  # min_gap >= 5
            multiplier = proximity_penalties['gap_5_plus_multiplier']
        
        self.log_debug(f"      Proximity calculation: min_gap={min_gap}, multiplier={multiplier:.2f}")
        return multiplier

    def _get_perfect_score(self):
        """Calculate the theoretical perfect score."""
        return (self.weights['gender_balance'] * 6 +     # Perfect gender balance
                self.weights['hosting_break_balance'] +   # Perfect break balance
                self.weights['host_rotation'] +           # Perfect host rotation
                self.weights['host_fairness'] +           # Perfect host fairness
                self.weights['meeting_fairness'])         # Perfect meeting fairness
    
    def _log_perfect_score_breakdown(self, perfect_score):
        """Log detailed breakdown of perfect score calculation."""
        self.log_debug(f"\n🎯 PERFECT SCORE BREAKDOWN:")
        self.log_debug(f"   Gender balance contribution: {self.weights['gender_balance'] * 6:,.0f} ({self.weights['gender_balance']:,} × 6 groups)")
        self.log_debug(f"   Break balance contribution: {self.weights['hosting_break_balance']:,.0f}")
        self.log_debug(f"   Host rotation contribution: {self.weights['host_rotation']:,.0f}")
        self.log_debug(f"   Host fairness contribution: {self.weights['host_fairness']:,.0f}")
        self.log_debug(f"   Meeting fairness contribution: {self.weights['meeting_fairness']:,.0f}")
        self.log_debug(f"   TOTAL PERFECT SCORE: {perfect_score:,.2f}")
    
    def _log_top_solutions_analysis(self, top_solutions):
        """Log analysis of top 5 solutions found."""
        self.log_debug(f"\n📊 TOP SOLUTIONS ANALYSIS:")
        if not top_solutions:
            self.log_debug(f"   No valid solutions found")
            return
            
        for i, solution_data in enumerate(top_solutions[:5]):
            rank = i + 1
            attempt = solution_data['attempt']
            score = solution_data['score']
            self.log_debug(f"   #{rank}: Attempt {attempt}, Score {score:.2f}")
            
        if len(top_solutions) > 1:
            best_score = top_solutions[0]['score']
            second_best = top_solutions[1]['score']
            score_gap = best_score - second_best
            self.log_debug(f"   Score gap between #1 and #2: {score_gap:.2f} points")
    
    def _log_meeting_distribution_analysis(self, solution):
        """Analyze and log meeting count distribution in the solution."""
        self.log_debug(f"\n🤝 MEETING DISTRIBUTION ANALYSIS:")
        
        # Count meetings for each pair in this solution
        pair_meetings = {}
        for group in solution:
            for i in range(len(group.children)):
                for j in range(i + 1, len(group.children)):
                    child1 = group.children[i]
                    child2 = group.children[j]
                    
                    # Get historical meeting count
                    meeting_count = 0
                    if child2.name in child1.meetings:
                        meeting_count = child1.meetings[child2.name]
                    meeting_count += 1  # Add current meeting
                    
                    pair_key = tuple(sorted([child1.name, child2.name]))
                    pair_meetings[pair_key] = meeting_count
        
        # Analyze distribution
        meeting_counts = list(pair_meetings.values())
        if meeting_counts:
            min_meetings = min(meeting_counts)
            max_meetings = max(meeting_counts)
            avg_meetings = sum(meeting_counts) / len(meeting_counts)
            
            self.log_debug(f"   Total pairs in solution: {len(meeting_counts)}")
            self.log_debug(f"   Meeting count range: {min_meetings} to {max_meetings} (spread: {max_meetings - min_meetings})")
            self.log_debug(f"   Average meetings per pair: {avg_meetings:.2f}")
            
            # Show worst offenders
            sorted_pairs = sorted(pair_meetings.items(), key=lambda x: x[1], reverse=True)
            self.log_debug(f"   🚨 HIGHEST MEETING COUNTS:")
            for pair, count in sorted_pairs[:5]:
                self.log_debug(f"      {pair[0]}-{pair[1]}: {count} meetings")
    
    def _log_penalty_effectiveness_analysis(self, solution, iteration_num, previous_iterations):
        """Analyze how effective penalties are at preventing poor meeting patterns."""
        self.log_debug(f"\n⚖️ PENALTY EFFECTIVENESS ANALYSIS:")
        
        # Calculate actual penalties for this solution
        progressive_penalty = self._calculate_progressive_meeting_penalty(solution)
        triplet_penalty = self._calculate_triplet_penalty(solution)
        
        # Get meeting diversity configuration
        meeting_config = self.config.get('meeting_diversity', {})
        base_weight = meeting_config.get('base_weight', 50)
        progression_multiplier = meeting_config.get('progression_multiplier', 0.2)
        
        self.log_debug(f"   Progressive meeting penalty: {progressive_penalty:.2f}")
        self.log_debug(f"   Triplet penalty: {triplet_penalty:.2f}")
        self.log_debug(f"   Total penalties: {progressive_penalty + triplet_penalty:.2f}")
        
        # Analyze penalty scale relative to other constraints
        total_score = self._evaluate_solution(solution, iteration_num, previous_iterations)
        penalty_percentage = ((progressive_penalty + triplet_penalty) / abs(total_score)) * 100
        
        self.log_debug(f"   Penalties as % of total score: {penalty_percentage:.3f}%")
        self.log_debug(f"   Penalty configuration: base_weight={base_weight}, progression_multiplier={progression_multiplier}")
        
        # Compare penalty scale to constraint weights
        gender_weight = self.weights.get('gender_balance', 1000000)
        penalty_vs_gender = (progressive_penalty + triplet_penalty) / gender_weight * 100
        self.log_debug(f"   Penalties vs Gender Balance weight: {penalty_vs_gender:.4f}%")
