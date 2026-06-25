"""
Command Line Interface for Topology Validation System
"""

import argparse
import os
import sys
import logging

from src.logger import get_logger, setup_logging

logger = get_logger(__name__)


def parse_args():
    """
    Parse command-line arguments

    Returns:
        tuple: (command, args_dict) where command is str and args_dict is dict of arguments
    """
    parser = argparse.ArgumentParser(
        description='Topology Validation System for ArcGIS Desktop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  flatten    Flatten GDB structure (move non-empty feature classes to single dataset)
  restore    Restore original GDB structure from flattened GDB (adds empty FCs from template)
  validate   Create and validate topology from configuration
  dedupe     Remove duplicate features from geodatabase
  enumerate  Display comprehensive GDB structure summary

Examples:
  python main.py flatten
  python main.py restore
  python main.py validate
  python main.py dedupe
  python main.py enumerate
        """
    )

    parser.add_argument(
        'command',
        choices=['flatten', 'restore', 'validate', 'dedupe', 'enumerate'],
        help='Command to execute'
    )

    parser.add_argument(
        '--gdb',
        help='Path to input GDB (for flatten/validate)'
    )

    parser.add_argument(
        '--output',
        help='Path to output GDB (for flatten)'
    )

    parser.add_argument(
        '--dataset',
        default='TKMDS',
        help='Dataset name for topology operations (default: TKMDS)'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration file (default: topology.config.toml)'
    )

    parser.add_argument(
        '--template',
        help='Template GDB path for empty feature classes (for restore command)'
    )

    parser.add_argument(
        '--feature-class',
        help='Specific feature class to process (for dedupe command)'
    )

    parser.add_argument(
        '--fields',
        help='Comma-separated list of fields to check for duplicates (for dedupe command)'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Report duplicates without removing them (for dedupe command)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Convert to dict for easier handling
    args_dict = {
        'gdb': args.gdb,
        'output': args.output,
        'dataset': args.dataset,
        'config': args.config,
        'template': args.template,
        'feature_class': args.feature_class,
        'fields': args.fields,
        'report_only': args.report_only,
        'verbose': args.verbose
    }

    return args.command, args_dict


def validate_args(command, args_dict):
    """
    Validate arguments based on command

    Args:
        command: Command name
        args_dict: Dictionary of arguments

    Returns:
        dict: Validated and normalized arguments

    Raises:
        ValueError: If arguments are invalid
    """
    validated = args_dict.copy()

    # Setup logging level
    if validated['verbose']:
        setup_logging(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Set default config path
    if not validated['config']:
        validated['config'] = get_default_config_path()

    # Command-specific validation
    if command == 'flatten':
        if not validated['gdb']:
            raise ValueError("--gdb argument required for flatten command")
        if not validated['output']:
            # Generate default output path
            validated['output'] = generate_flattened_name(validated['gdb'])
            logger.info("No output specified, using: {}".format(validated['output']))

    elif command == 'restore':
        # Restore works on flattened GDB
        if not validated['gdb']:
            raise ValueError("--gdb argument required for restore command")
        if not validated['gdb'].endswith('_flattened.gdb'):
            logger.warning("Restore command expects flattened GDB (ending with _flattened.gdb)")

    elif command == 'validate':
        if not validated['gdb']:
            raise ValueError("--gdb argument required for validate command")

        # Validate config file exists
        if not os.path.exists(validated['config']):
            raise ValueError("Config file not found: {}".format(validated['config']))

    elif command == 'dedupe':
        if not validated['gdb']:
            raise ValueError("--gdb argument required for dedupe command")

        # Parse fields if provided
        if validated['fields']:
            validated['fields'] = [f.strip() for f in validated['fields'].split(',')]
            logger.debug("Fields for duplicate checking: {}".format(validated['fields']))

    elif command == 'enumerate':
        if not validated['gdb']:
            raise ValueError("--gdb argument required for enumerate command")

    return validated


def get_default_config_path():
    """
    Get default configuration file path

    Returns:
        str: Path to topology.config.toml
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'topology.config.toml')
    logger.debug("Default config path: {}".format(config_path))
    return os.path.abspath(config_path)


def generate_flattened_name(gdb_path):
    """
    Generate flattened GDB name from input GDB path

    Args:
        gdb_path: Path to input GDB

    Returns:
        str: Path to flattened GDB
    """
    if gdb_path.endswith('.gdb'):
        base = gdb_path[:-4]
        return base + '_flattened.gdb'
    else:
        return gdb_path + '_flattened.gdb'


def print_usage():
    """Print usage information"""
    print("Topology Validation System")
    print("")
    print("Usage: python main.py <command> [options]")
    print("")
    print("Commands:")
    print("  flatten    Flatten GDB structure (non-empty FCs only)")
    print("  restore    Restore original GDB structure (adds empty FCs from template)")
    print("  validate   Create and validate topology")
    print("  dedupe     Remove duplicate features")
    print("  enumerate  Display GDB structure summary")
    print("")
    print("Options:")
    print("  --gdb PATH          Input GDB path")
    print("  --output PATH       Output GDB path (for flatten)")
    print("  --dataset NAME      Dataset name (default: TKMDS)")
    print("  --config PATH       Config file path (default: topology.config.toml)")
    print("  --template PATH     Template GDB path (for restore)")
    print("  --feature-class     Specific feature class (for dedupe)")
    print("  --fields            Comma-separated field list (for dedupe)")
    print("  --report-only       Report without removing (for dedupe)")
    print("  --verbose           Enable verbose logging")
    print("")
    print("Examples:")
    print("  python main.py flatten --gdb input.gdb --output output_flattened.gdb")
    print("  python main.py restore --gdb output_flattened.gdb --template template.gdb")
    print("  python main.py validate --gdb input.gdb --config topology.config.toml")
    print("  python main.py dedupe --gdb input.gdb --dataset TKMDS")
    print("  python main.py enumerate --gdb input.gdb")


def parse_command_line():
    """
    Main entry point for CLI parsing

    Returns:
        tuple: (command, validated_args_dict)
    """
    try:
        command, args = parse_args()
        validated_args = validate_args(command, args)
        return command, validated_args
    except ValueError as e:
        logger.error("Argument validation error: {}".format(str(e)))
        print_usage()
        sys.exit(1)
    except Exception as e:
        logger.error("Error parsing arguments: {}".format(str(e)))
        print_usage()
        sys.exit(1)