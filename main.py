#!/usr/bin/env python3
"""
Child Group Rotation Optimizer
A Python command-line tool for optimizing child group rotations using weighted constraint satisfaction.

Usage: python main.py <number_of_iterations>
"""

import sys
import os
import argparse
from datetime import datetime
from child_manager import ChildManager
from group_optimizer import GroupOptimizer
from output_formatter import OutputFormatter


def validate_input_files():
    """Validate that input directory contains required names_gender.txt and optional past_iterations.txt."""
    input_dir = "input"
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
    
    # Check for required names_gender.txt
    names_file = os.path.join(input_dir, "names_gender.txt")
    if not os.path.exists(names_file):
        print(f"Error: Required file 'input/names_gender.txt' not found.")
        sys.exit(1)
    
    # Check for optional past_iterations.txt
    past_iterations_file = os.path.join(input_dir, "past_iterations.txt")
    has_past_iterations = os.path.exists(past_iterations_file)
    
    # Check for unexpected files
    expected_files = {"names_gender.txt", "past_iterations.txt"}
    actual_files = set(f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)))
    unexpected_files = actual_files - expected_files
    
    if unexpected_files:
        print(f"Error: Unexpected files in input directory: {', '.join(unexpected_files)}")
        print(f"Expected only: names_gender.txt and optionally past_iterations.txt")
        sys.exit(1)
    
    return names_file, past_iterations_file if has_past_iterations else None

def validate_output_directory():
    """Validate and create output directory if needed."""
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error: Cannot create output directory '{output_dir}': {e}")
            sys.exit(1)
    
    return output_dir

def validate_iterations(number_of_iterations):
    """Validate number of iterations."""
    if number_of_iterations < 1 or number_of_iterations > 12:
        print("Error: Number of iterations must be between 1 and 12.")
        sys.exit(1)


def main():
    """Main function to orchestrate the group optimization process."""
    parser = argparse.ArgumentParser(
        description="Optimize child group rotations using weighted constraint satisfaction"
    )
    parser.add_argument("number_of_iterations", type=int, help="Number of iterations (1-12)")
    
    args = parser.parse_args()
    
    # Validate arguments
    validate_iterations(args.number_of_iterations)
    names_file, past_iterations_file = validate_input_files()
    output_directory = validate_output_directory()
    
    try:
        # Initialize child manager and load children
        child_manager = ChildManager()
        children = child_manager.load_children_from_file(names_file)
        
        # Validate children data
        child_manager.validate_children(children)
        
        # Load past iterations if they exist
        past_iterations = []
        past_iteration_count = 0
        if past_iterations_file:
            past_iterations = child_manager.load_past_iterations(past_iterations_file, children)
            past_iteration_count = len(past_iterations)
            print(f"Loaded {past_iteration_count} past iteration(s) from {past_iterations_file}")
            
            # Update child statistics based on past iterations
            optimizer = GroupOptimizer()
            optimizer.process_past_iterations(children, past_iterations)
        else:
            optimizer = GroupOptimizer()
        
        # Generate new iterations
        if past_iteration_count > 0:
            print(f"Generating {args.number_of_iterations} new iteration(s) (continuing from {past_iteration_count} past iterations)...")
        else:
            print(f"Generating {args.number_of_iterations} iteration(s)...")
        
        all_iterations = []
        
        for new_iteration_num in range(1, args.number_of_iterations + 1):
            # Calculate absolute iteration number
            absolute_iteration_num = past_iteration_count + new_iteration_num
            print(f"Creating iteration {absolute_iteration_num}...")
            
            # Generate groups for this iteration (pass past + current iterations)
            all_past_and_current = past_iterations + all_iterations
            groups = optimizer.create_iteration(children, absolute_iteration_num, all_past_and_current)
            
            if not groups:
                print(f"Error: Could not create valid groups for iteration {absolute_iteration_num}")
                sys.exit(1)
            
            all_iterations.append(groups)
            print(f"Iteration {absolute_iteration_num} completed successfully.")
        
        # Generate output files
        formatter = OutputFormatter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate group output file
        group_filename = f"Play_groups_{args.number_of_iterations}_{timestamp}.txt"
        group_filepath = os.path.join(output_directory, group_filename)
        formatter.write_groups_file(all_iterations, group_filepath, past_iteration_count)
        
        # Generate summary report
        summary_filename = f"Summary_{args.number_of_iterations}_{timestamp}.txt"
        summary_filepath = os.path.join(output_directory, summary_filename)
        formatter.write_summary_file(children, all_iterations, summary_filepath, optimizer.warnings, optimizer.solver, past_iteration_count, optimizer)
        
        print(f"\nOutput files generated:")
        print(f"  Groups: {group_filepath}")
        print(f"  Summary: {summary_filepath}")
        
        if optimizer.warnings:
            print(f"\nWarnings: {len(optimizer.warnings)} constraint violations detected. See summary file for details.")
        
        print("Process completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
