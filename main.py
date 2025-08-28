#!/usr/bin/env python3
"""
Child Group Rotation Optimizer
A Python command-line tool for optimizing child group rotations using weighted constraint satisfaction.

Usage: python main.py <input_file.txt> <output_directory> <number_of_iterations>
"""

import sys
import os
import argparse
from datetime import datetime
from child_manager import ChildManager
from group_optimizer import GroupOptimizer
from output_formatter import OutputFormatter


def validate_arguments(args):
    """Validate command line arguments."""
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Check if output directory exists, create if not
    if not os.path.exists(args.output_directory):
        try:
            os.makedirs(args.output_directory)
            print(f"Created output directory: {args.output_directory}")
        except OSError as e:
            print(f"Error: Cannot create output directory '{args.output_directory}': {e}")
            sys.exit(1)
    
    # Validate number of iterations
    if args.number_of_iterations < 1 or args.number_of_iterations > 12:
        print("Error: Number of iterations must be between 1 and 12.")
        sys.exit(1)


def main():
    """Main function to orchestrate the group optimization process."""
    parser = argparse.ArgumentParser(
        description="Optimize child group rotations using weighted constraint satisfaction"
    )
    parser.add_argument("input_file", help="Tab-delimited file with child names and gender")
    parser.add_argument("output_directory", help="Directory to save output files")
    parser.add_argument("number_of_iterations", type=int, help="Number of iterations (1-12)")
    
    args = parser.parse_args()
    
    # Validate arguments
    validate_arguments(args)
    
    try:
        # Initialize child manager and load children
        child_manager = ChildManager()
        children = child_manager.load_children_from_file(args.input_file)
        
        # Validate children data
        child_manager.validate_children(children)
        
        # Initialize group optimizer
        optimizer = GroupOptimizer()
        
        # Generate iterations
        print(f"Generating {args.number_of_iterations} iteration(s)...")
        all_iterations = []
        
        for iteration_num in range(1, args.number_of_iterations + 1):
            print(f"Creating iteration {iteration_num}...")
            
            # Generate groups for this iteration
            groups = optimizer.create_iteration(children, iteration_num, all_iterations)
            
            if not groups:
                print(f"Error: Could not create valid groups for iteration {iteration_num}")
                sys.exit(1)
            
            all_iterations.append(groups)
            print(f"Iteration {iteration_num} completed successfully.")
        
        # Generate output files
        formatter = OutputFormatter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate group output file
        group_filename = f"Play_groups_{args.number_of_iterations}_{timestamp}.txt"
        group_filepath = os.path.join(args.output_directory, group_filename)
        formatter.write_groups_file(all_iterations, group_filepath)
        
        # Generate summary report
        summary_filename = f"Summary_{args.number_of_iterations}_{timestamp}.txt"
        summary_filepath = os.path.join(args.output_directory, summary_filename)
        formatter.write_summary_file(children, all_iterations, summary_filepath, optimizer.warnings)
        
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
