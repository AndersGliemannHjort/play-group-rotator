# Child Group Rotation Optimizer

## Overview

A Python command-line tool that optimizes child group rotations using weighted constraint satisfaction algorithms. The system takes a tab-delimited file of exactly 24 children (12 boys, 12 girls) with their names and genders, then generates optimal group arrangements across multiple iterations (1-12) while balancing various constraints like gender balance, host rotation fairness, and meeting diversity.

**Command Line Usage:** `python main.py <number_of_iterations>`

**File Structure:**
- `input/` directory must contain exactly one tab-delimited file with 24 children
- `output/` directory will be created automatically for output files

**Output Files:**
- `Play_groups_[count]_[YYYYMMDD_HHMMSS].txt` - Group arrangements with iteration separation
- `Summary_[count]_[YYYYMMDD_HHMMSS].txt` - Detailed hosting and meeting statistics matrix

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**Modular Design Pattern**: The application follows a clear separation of concerns with dedicated modules for each responsibility:

- **Child Management (`child_manager.py`)**: Handles data loading and validation from tab-delimited input files. Uses a `Child` class to represent individual children with gender information and tracking data for optimization metrics.

- **Constraint Solver (`constraint_solver.py`)**: Implements a backtracking algorithm with weighted constraint satisfaction. Uses multiple attempts to find optimal solutions and evaluates candidates against configurable scoring thresholds.

- **Group Optimizer (`group_optimizer.py`)**: Main orchestration component that coordinates the constraint solving process. Manages the `Group` class representing collections of children and integrates with the constraint solver.

- **Output Formatter (`output_formatter.py`)**: Dedicated component for generating formatted output files including group arrangements and detailed summary reports with hosting statistics.

**Configuration-Driven Approach**: The system uses JSON-based configuration (`weights_config.json`) to define:
- Constraint weights (gender balance, host rotation, group diversity, etc.)
- Algorithm parameters (max attempts, backtrack thresholds)
- Target group composition rules

**Constraint Satisfaction Algorithm**: Implements a weighted scoring system that optimizes for:
- Gender balance within groups
- Fair host rotation across iterations with minimum break threshold (≥2 iterations)
- Meeting diversity (avoiding repeated pairings) 
- Equal hosting opportunities
- Balanced meeting frequencies

**Minimum Break Threshold Approach**: Host selection excludes children with break lengths <2 (consecutive hosting) while treating breaks ≥2 equally with randomization. This prevents unfair consecutive hosting while maximizing flexibility for improved meeting diversity.

**File-Based I/O Architecture**: 
- Input: Tab-delimited text files with child name and gender columns
- Output: Multiple files including group arrangements and detailed analytics
- Error handling with comprehensive validation

### Design Decisions

**Backtracking with Multiple Attempts**: Chose iterative improvement over single-pass algorithms to handle the complex multi-constraint optimization problem, allowing the system to find better solutions within computational limits.

**Weighted Scoring System**: Selected a flexible weighting approach rather than hard constraints to allow for graceful degradation when perfect solutions aren't possible, making the system robust for various input sizes and compositions.

**Stateful Child Objects**: Children maintain tracking data (hosting counts, meeting history) to enable sophisticated fairness calculations across iterations while keeping the data model simple and comprehensible.

## External Dependencies

The application is designed to be self-contained with minimal external dependencies:

- **Python Standard Library Only**: Uses built-in modules (`os`, `sys`, `json`, `datetime`, `argparse`, `random`, `itertools`) to avoid external package management complexity
- **File System**: Relies on local file system for input/output operations
- **No Database**: Uses in-memory data structures with file-based persistence for simplicity and portability
- **No Web Services**: Operates as a standalone command-line application without network dependencies