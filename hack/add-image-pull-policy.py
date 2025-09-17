#!/usr/bin/env python3

"""
Script to add imagePullPolicy: IfNotPresent to spec.stepTemplate in Tekton Task YAML files
Usage: ./add-image-pull-policy.py [directory]
If no directory is provided, it will process the current directory
"""

import os
import sys
import argparse
from pathlib import Path
import re

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
except ImportError:
    print("Error: ruamel.yaml is not installed. Please install it with: pip install ruamel.yaml")
    sys.exit(1)


def should_skip_file(file_path):
    """Check if file should be skipped based on directory patterns."""
    file_path_str = str(file_path)

    # Skip files in directories ending with -ta or -remote
    if re.search(r'/([^/]+-ta|.*-remote)/', file_path_str):
        return True, "directory ends with -ta or -remote"

    # Skip files in clair-scan or clamav-scan directories
    if re.search(r'/(clair-scan|clamav-scan)/', file_path_str):
        return True, "excluded directory"

    return False, None


def add_image_pull_policy_to_file(file_path):
    """Add imagePullPolicy to stepTemplate using ruamel.yaml."""
    # Configure ruamel.yaml for best formatting preservation
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # Prevent line wrapping
    yaml.indent(mapping=2, sequence=2, offset=0)

    # Read and parse the YAML file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    # Add imagePullPolicy to stepTemplate
    if 'stepTemplate' not in data['spec']:
        data['spec']['stepTemplate'] = CommentedMap()

    data['spec']['stepTemplate']['imagePullPolicy'] = 'IfNotPresent'

    # Write back with ruamel.yaml, preserving formatting
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

    return True, "added imagePullPolicy: IfNotPresent to stepTemplate"


def process_yaml_file(file_path):
    """Process a single YAML file to add imagePullPolicy to stepTemplate."""
    try:
        # First validate it's a valid YAML and Tekton Task
        yaml = YAML()
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)

        # Check if it's a Tekton Task
        if not isinstance(data, dict) or data.get('kind') != 'Task':
            return False, "not a Tekton Task"

        # Check if spec exists
        if 'spec' not in data:
            return False, "no spec section"

        # Use ruamel.yaml approach to preserve formatting
        return add_image_pull_policy_to_file(file_path)

    except Exception as e:
        return False, f"error: {e}"


def main():
    parser = argparse.ArgumentParser(description='Add imagePullPolicy to Tekton Task stepTemplate')
    parser.add_argument('path', nargs='?', default='.',
                       help='Directory or file to process (default: current directory)')
    args = parser.parse_args()

    target_path = Path(args.path)

    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)

    # Find YAML files - if it's a file, use it directly; if it's a directory, find all YAML files
    if target_path.is_file():
        yaml_files = [target_path] if target_path.suffix == '.yaml' else []
    else:
        yaml_files = list(target_path.rglob('*.yaml'))

    if not yaml_files:
        print("No YAML files found")
        return

    processed_count = 0
    skipped_count = 0

    for file_path in yaml_files:
        # Check if file should be skipped
        should_skip, skip_reason = should_skip_file(file_path)
        if should_skip:
            print(f"Skipping: {file_path} ({skip_reason})")
            skipped_count += 1
            continue

        print(f"Processing: {file_path}")

        # Process the file
        success, message = process_yaml_file(file_path)

        if success:
            print(f"  - {message}")
            processed_count += 1
        else:
            print(f"  - {message}")
            skipped_count += 1

    print(f"\nProcessing complete!")
    print(f"Processed: {processed_count} files")
    print(f"Skipped: {skipped_count} files")


if __name__ == '__main__':
    main()
