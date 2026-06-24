"""
Main entry point for Topology Management System
Provides three commands: flatten, restore, validate
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import get_logger, setup_logging
from src.cli import parse_command_line
from src.config import load_config, validate_config
from src.gdbops import flatten_gdb, restore_gdb
from src.topology import create_topology, validate_topology
from src.dedupe import remove_duplicates, report_duplicates
from src.utils import check_arcgis_license

logger = get_logger(__name__)


def main():
    """
    Main entry point for CLI application
    """
    try:
        # Parse command line arguments
        command, args = parse_command_line()

        logger.info("Topology Management System started")
        logger.info("Command: {}".format(command))

        # Check ArcGIS license
        check_arcgis_license()

        # Route to appropriate command
        if command == 'flatten':
            return handle_flatten(args)
        elif command == 'restore':
            return handle_restore(args)
        elif command == 'validate':
            return handle_validate(args)
        elif command == 'dedupe':
            return handle_dedupe(args)
        else:
            logger.error("Unknown command: {}".format(command))
            return 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error("Unexpected error: {}".format(str(e)))
        import traceback
        logger.error(traceback.format_exc())
        return 1


def handle_flatten(args):
    """
    Handle flatten command

    Args:
        args: Parsed arguments dictionary

    Returns:
        int: Exit code (0 for success)
    """
    logger.info("Executing flatten command")
    logger.info("Input GDB: {}".format(args['gdb']))
    logger.info("Output GDB: {}".format(args['output']))
    logger.info("Dataset: {}".format(args['dataset']))

    # Execute flatten operation
    structure = flatten_gdb(args['gdb'], args['output'], args['dataset'])

    logger.info("Flatten completed successfully")
    logger.info("Original structure preserved with {} datasets".format(len(structure.datasets)))

    return 0


def handle_restore(args):
    """
    Handle restore command

    Args:
        args: Parsed arguments dictionary

    Returns:
        int: Exit code (0 for success)
    """
    logger.info("Executing restore command")
    logger.info("Flattened GDB: {}".format(args['gdb']))

    # Execute restore operation
    restored_path = restore_gdb(args['gdb'])

    logger.info("Restore completed successfully")
    logger.info("Restored GDB: {}".format(restored_path))

    return 0


def handle_validate(args):
    """
    Handle validate command

    Args:
        args: Parsed arguments dictionary

    Returns:
        int: Exit code (0 for success)
    """
    logger.info("Executing validate command")
    logger.info("GDB: {}".format(args['gdb']))
    logger.info("Config: {}".format(args['config']))
    logger.info("Dataset: {}".format(args['dataset']))

    # Load configuration
    config = load_config(args['config'])
    validate_config(config)

    # Override config path with args if provided
    if args['gdb']:
        config.gdb_path = args['gdb']
    if args['dataset']:
        config.dataset_name = args['dataset']

    logger.info("Topology: {}".format(config.topology_name))
    logger.info("Rules: {}".format(len(config.rules)))

    # Execute topology validation
    results = validate_topology(config)

    logger.info("Validation completed successfully")
    if 'total' in results:
        logger.info("Topology errors found: {}".format(results['total']))

    return 0


def handle_dedupe(args):
    """
    Handle dedupe command

    Args:
        args: Parsed arguments dictionary

    Returns:
        int: Exit code (0 for success)
    """
    logger.info("Executing dedupe command")
    logger.info("GDB: {}".format(args['gdb']))
    logger.info("Dataset: {}".format(args['dataset']))
    logger.info("Feature class: {}".format(args['feature_class']))
    logger.info("Fields: {}".format(args['fields']))
    logger.info("Report only: {}".format(args['report_only']))

    # Execute duplicate removal or reporting
    if args['report_only']:
        results = report_duplicates(
            args['gdb'],
            dataset_name=args['dataset'],
            feature_class=args['feature_class'],
            fields=args['fields']
        )
        logger.info("Duplicate report complete")
        logger.info("Total duplicates found: {}".format(results['total_duplicates']))

        # Print detailed report
        for fc_name, fc_report in results['feature_classes'].items():
            logger.info("  {}: {} duplicates".format(fc_name, fc_report['count']))
    else:
        results = remove_duplicates(
            args['gdb'],
            dataset_name=args['dataset'],
            feature_class=args['feature_class'],
            fields=args['fields']
        )
        logger.info("Duplicate removal complete")
        logger.info("Feature classes processed: {}".format(results['feature_classes_processed']))
        logger.info("Total duplicates found: {}".format(results['duplicates_found']))
        logger.info("Total duplicates removed: {}".format(results['duplicates_removed']))

        if results['errors']:
            logger.warning("Errors encountered: {}".format(len(results['errors'])))
            for error in results['errors']:
                logger.warning("  - {}".format(error))

    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)