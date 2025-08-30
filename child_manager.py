"""
Child Manager Module
Handles loading, validation, and management of child data.
"""

import os


class Child:
    """Represents a child with name and gender information."""
    
    def __init__(self, name, is_girl):
        self.name = name.strip()
        self.is_girl = bool(int(is_girl))
        self.is_boy = not self.is_girl
        
        # Tracking data for optimization
        self.hosting_count = 0
        self.hosting_iterations = []  # List of iteration numbers when this child hosted
        self.meetings = {}  # Dictionary of child names to meeting counts
    
    def __str__(self):
        return f"{self.name} ({'Girl' if self.is_girl else 'Boy'})"
    
    def __repr__(self):
        return self.__str__()


class ChildManager:
    """Manages child data loading and validation."""
    
    def load_children_from_file(self, filepath):
        """Load children from tab-delimited file."""
        children = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            if not lines:
                raise ValueError("Input file is empty")
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) != 2:
                    raise ValueError(f"Line {line_num}: Expected 2 tab-separated columns, found {len(parts)}")
                
                name, is_girl_str = parts
                
                if not name.strip():
                    raise ValueError(f"Line {line_num}: Child name cannot be empty")
                
                try:
                    is_girl = int(is_girl_str.strip())
                    if is_girl not in [0, 1]:
                        raise ValueError(f"Line {line_num}: Gender value must be 0 or 1, found '{is_girl_str}'")
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValueError(f"Line {line_num}: Gender value must be 0 or 1, found '{is_girl_str}'")
                    raise
                
                child = Child(name, is_girl)
                children.append(child)
        
        except FileNotFoundError:
            raise ValueError(f"File not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
        
        return children
    
    def validate_children(self, children):
        """Validate that we have exactly 24 children with 12 boys and 12 girls."""
        if len(children) != 24:
            raise ValueError(f"Expected exactly 24 children, found {len(children)}")
        
        # Check for duplicate names
        names = [child.name for child in children]
        if len(set(names)) != len(names):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate child names found: {set(duplicates)}")
        
        # Count boys and girls
        girls = sum(1 for child in children if child.is_girl)
        boys = sum(1 for child in children if child.is_boy)
        
        if girls != 12 or boys != 12:
            raise ValueError(f"Expected exactly 12 boys and 12 girls, found {boys} boys and {girls} girls")
        
        print(f"Validated: {len(children)} children ({boys} boys, {girls} girls)")
        
        return True
    
    def load_past_iterations(self, filepath, children):
        """Load past iterations from comma-separated file with strict format validation."""
        from group_optimizer import Group  # Import here to avoid circular imports
        
        # Create name-to-child mapping for quick lookups
        child_by_name = {child.name: child for child in children}
        
        past_iterations = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            if not lines:
                raise ValueError("Past iterations file is empty")
            
            current_iteration_groups = []
            current_iteration_num = None
            line_num = 0
            
            for line in lines:
                line_num += 1
                line = line.strip()
                
                if not line:
                    # Empty line - end of iteration if we have groups
                    if current_iteration_groups:
                        past_iterations.append(current_iteration_groups)
                        current_iteration_groups = []
                        current_iteration_num = None
                    continue
                
                # Check for iteration header
                if line.startswith("=== ITERATION ") and line.endswith(" ==="):
                    # Extract iteration number and validate
                    try:
                        iter_str = line[14:-4].strip()  # Remove "=== ITERATION " and " ==="
                        iter_num = int(iter_str)
                        expected_iter = len(past_iterations) + 1
                        if iter_num != expected_iter:
                            raise ValueError(f"Line {line_num}: Expected iteration {expected_iter}, found {iter_num}")
                        current_iteration_num = iter_num
                    except ValueError as e:
                        if "invalid literal" in str(e):
                            raise ValueError(f"Line {line_num}: Invalid iteration header format: '{line}'")
                        raise
                    continue
                
                # This should be a group line
                if current_iteration_num is None:
                    raise ValueError(f"Line {line_num}: Group data found before iteration header")
                
                # Parse group line - must be exactly comma-and-space separated format
                if ', ' not in line:
                    raise ValueError(f"Line {line_num}: Groups must use comma-and-space format (e.g., 'Name1, Name2, Name3, Name4'), found: '{line}'")
                
                names = [name.strip() for name in line.split(', ')]
                
                # Validate group size
                if len(names) != 4:
                    raise ValueError(f"Line {line_num}: Expected exactly 4 children per group, found {len(names)}: {names}")
                
                # Validate all names exist in children list
                group_children = []
                for name in names:
                    if name not in child_by_name:
                        raise ValueError(f"Line {line_num}: Child '{name}' not found in names_gender.txt")
                    group_children.append(child_by_name[name])
                
                # Create group (first child is host)
                group = Group(group_children)
                current_iteration_groups.append(group)
            
            # Handle final iteration if file doesn't end with empty line
            if current_iteration_groups:
                past_iterations.append(current_iteration_groups)
            
            # Validate each iteration has exactly 6 groups
            for iter_num, iteration_groups in enumerate(past_iterations, 1):
                if len(iteration_groups) != 6:
                    raise ValueError(f"Iteration {iter_num}: Expected exactly 6 groups, found {len(iteration_groups)}")
                
                # Validate all 24 children are accounted for
                children_in_iteration = set()
                for group in iteration_groups:
                    for child in group.children:
                        if child.name in children_in_iteration:
                            raise ValueError(f"Iteration {iter_num}: Child '{child.name}' appears in multiple groups")
                        children_in_iteration.add(child.name)
                
                if len(children_in_iteration) != 24:
                    raise ValueError(f"Iteration {iter_num}: Expected 24 children, found {len(children_in_iteration)}")
                    
                missing_children = set(child.name for child in children) - children_in_iteration
                if missing_children:
                    raise ValueError(f"Iteration {iter_num}: Missing children: {missing_children}")
        
        except FileNotFoundError:
            raise ValueError(f"Past iterations file not found: {filepath}")
        except Exception as e:
            if "Line" in str(e):
                raise  # Re-raise detailed line-specific errors
            raise ValueError(f"Error reading past iterations file: {e}")
        
        return past_iterations
