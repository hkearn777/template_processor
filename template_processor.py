#!/usr/bin/env python3
"""
Template Processor - Replaces tags in template files with actual values.
Tags format: <<TAGNAME>>
"""

import argparse
import sys
import json
import re
import os


TAG_PATTERN = re.compile(r"<<([A-Za-z0-9_\-\.]+)>>")


def load_substitutions_from_file(config_file):
    """Load tag substitutions from a JSON configuration file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print("Error: Configuration JSON must be an object of TAG:VALUE pairs.", file=sys.stderr)
            sys.exit(1)

        return data
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_tag_name(tag):
    """Normalize tag input to a raw tag name without << >> wrappers."""
    tag = tag.strip()
    if tag.startswith('<<') and tag.endswith('>>'):
        return tag[2:-2].strip()
    return tag


def apply_substitutions(content, substitutions):
    """Return content with substitutions applied."""
    for tag, value in substitutions.items():
        tag_name = normalize_tag_name(str(tag))
        if not tag_name:
            continue
        tag_formatted = f"<<{tag_name}>>"
        content = content.replace(tag_formatted, str(value))
    return content


def find_unreplaced_tags(content):
    """Find unreplaced tags still present in content."""
    return sorted(set(TAG_PATTERN.findall(content)))


def process_template(template_file, output_file, substitutions, fail_on_unreplaced=False):
    """
    Read template file, substitute tags, and write output file.
    """
    try:
        # Read the template file
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Perform substitutions
        content = apply_substitutions(content, substitutions)

        unreplaced_tags = find_unreplaced_tags(content)
        if unreplaced_tags:
            print(
                "Warning: Unreplaced tags found: " + ", ".join(unreplaced_tags),
                file=sys.stderr,
            )
            if fail_on_unreplaced:
                print("Error: Failing because --fail-on-unreplaced was set.", file=sys.stderr)
                sys.exit(1)
        
        # Write the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Template processed successfully!")
        print(f"  Input:  {template_file}")
        print(f"  Output: {output_file}")
        print(f"  Substitutions made: {len(substitutions)}")
        if unreplaced_tags:
            print(f"  Unreplaced tags: {len(unreplaced_tags)}")
        return unreplaced_tags
        
    except FileNotFoundError:
        print(f"Error: Template file '{template_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: Could not read/write file: {e}", file=sys.stderr)
        sys.exit(1)


def process_template_folder(input_folder, output_folder, substitutions, fail_on_unreplaced=False):
    """Process all files in a folder and write results to output folder."""
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        os.makedirs(output_folder, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output folder '{output_folder}': {e}", file=sys.stderr)
        sys.exit(1)

    template_files = []
    for name in sorted(os.listdir(input_folder)):
        file_path = os.path.join(input_folder, name)
        if os.path.isfile(file_path):
            template_files.append(name)

    if not template_files:
        print(f"Error: No files found in input folder '{input_folder}'.", file=sys.stderr)
        sys.exit(1)

    processed_count = 0
    unreplaced_file_count = 0

    for filename in template_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        unreplaced_tags = process_template(
            input_path,
            output_path,
            substitutions,
            fail_on_unreplaced=False,
        )
        processed_count += 1
        if unreplaced_tags:
            unreplaced_file_count += 1

    print("Batch processing complete!")
    print(f"  Input folder:  {input_folder}")
    print(f"  Output folder: {output_folder}")
    print(f"  Files processed: {processed_count}")
    print(f"  Files with unreplaced tags: {unreplaced_file_count}")

    if fail_on_unreplaced and unreplaced_file_count > 0:
        print("Error: Failing because --fail-on-unreplaced was set.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Process template files by replacing tags with values.'
    )
    
    parser.add_argument('template', help='Input template file (or input folder with --batch)')
    parser.add_argument('output', help='Output file (or output folder with --batch)')
    parser.add_argument('-c', '--config', help='JSON configuration file with tag substitutions')
    parser.add_argument('-s', '--substitute', nargs='+', metavar='TAG=VALUE',
                        help='Tag substitutions (format: TAG=VALUE)')
    parser.add_argument('--fail-on-unreplaced', action='store_true',
                        help='Exit with error if any tags remain unreplaced in output')
    parser.add_argument('--batch', action='store_true',
                        help='Process all files in input folder to output folder')
    
    args = parser.parse_args()
    
    # Build substitutions dictionary
    substitutions = {}
    
    # Load from config file if provided
    if args.config:
        substitutions = load_substitutions_from_file(args.config)
    
    # Parse command line substitutions (these override config file)
    if args.substitute:
        for sub in args.substitute:
            if '=' not in sub:
                print(f"Error: Invalid substitution format '{sub}'. Use TAG=VALUE", file=sys.stderr)
                sys.exit(1)
            tag, value = sub.split('=', 1)
            tag = normalize_tag_name(tag)
            if not tag:
                print("Error: Tag name cannot be empty.", file=sys.stderr)
                sys.exit(1)
            substitutions[tag] = value
    
    if not substitutions:
        print("Warning: No substitutions provided.", file=sys.stderr)
    
    if args.batch:
        process_template_folder(
            args.template,
            args.output,
            substitutions,
            fail_on_unreplaced=args.fail_on_unreplaced,
        )
    else:
        # Process a single template file
        process_template(
            args.template,
            args.output,
            substitutions,
            fail_on_unreplaced=args.fail_on_unreplaced,
        )


if __name__ == '__main__':
    main()