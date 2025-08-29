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
