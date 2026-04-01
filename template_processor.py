#!/usr/bin/env python3
"""
Template Processor - Replaces tags in template files with actual values.
Tags format: <<TAGNAME>>
"""

import argparse
import sys
import json


def load_substitutions_from_file(config_file):
    """Load tag substitutions from a JSON configuration file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        sys.exit(1)


def process_template(template_file, output_file, substitutions):
    """
    Read template file, substitute tags, and write output file.
    """
    try:
        # Read the template file
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Perform substitutions
        for tag, value in substitutions.items():
            # Ensure tag is in the correct format <<TAG>>
            tag_formatted = tag if tag.startswith('<<') else f"<<{tag}>>"
            content = content.replace(tag_formatted, str(value))
        
        # Write the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Template processed successfully!")
        print(f"  Input:  {template_file}")
        print(f"  Output: {output_file}")
        print(f"  Substitutions made: {len(substitutions)}")
        
    except FileNotFoundError:
        print(f"Error: Template file '{template_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: Could not read/write file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Process template files by replacing tags with values.'
    )
    
    parser.add_argument('template', help='Input template file')
    parser.add_argument('output', help='Output file')
    parser.add_argument('-c', '--config', help='JSON configuration file with tag substitutions')
    parser.add_argument('-s', '--substitute', nargs='+', metavar='TAG=VALUE',
                        help='Tag substitutions (format: TAG=VALUE)')
    
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
            tag = tag.strip()
            substitutions[tag] = value
    
    if not substitutions:
        print("Warning: No substitutions provided.", file=sys.stderr)
    
    # Process the template
    process_template(args.template, args.output, substitutions)


if __name__ == '__main__':
    main()