"""
Configuration management for Topology Management System
Handles TOML configuration parsing and validation
"""

import os
import sys

# Try to import TOML library compatible with Python 2.7
try:
    import toml
    logger_source = "toml"
except ImportError:
    try:
        import pytoml as toml
        logger_source = "pytoml"
    except ImportError:
        # Fallback: provide simple TOML parser
        toml = None
        logger_source = "simple_parser"

from src.logger import get_logger

logger = get_logger(__name__)


class TopologyRule(object):
    """Represents a single topology rule"""

    def __init__(self, origin_fc, rule_type, destination_fc=None):
        self.origin_fc = origin_fc
        self.rule_type = rule_type
        self.destination_fc = destination_fc

    def __repr__(self):
        if self.destination_fc:
            return "TopologyRule(origin_fc={}, rule_type={}, destination_fc={})".format(
                self.origin_fc, self.rule_type, self.destination_fc)
        else:
            return "TopologyRule(origin_fc={}, rule_type={})".format(
                self.origin_fc, self.rule_type)


class TopologyConfig(object):
    """Represents topology configuration"""

    def __init__(self, gdb_path, dataset_name, topology_name, rules=None):
        self.gdb_path = gdb_path
        self.dataset_name = dataset_name
        self.topology_name = topology_name
        self.rules = rules if rules is not None else []

    def __repr__(self):
        return "TopologyConfig(gdb={}, dataset={}, topology={}, rules={})".format(
            self.gdb_path, self.dataset_name, self.topology_name, len(self.rules))


def load_config(config_path):
    """
    Load and parse TOML configuration file

    Args:
        config_path: Path to configuration file

    Returns:
        TopologyConfig: Parsed configuration object

    Raises:
        ValueError: If config file is invalid
        IOError: If config file cannot be read
    """
    if not os.path.exists(config_path):
        raise IOError("Config file not found: {}".format(config_path))

    try:
        if toml:
            logger.debug("Using {} library for TOML parsing".format(logger_source))
            config_dict = toml.load(config_path)
        else:
            logger.debug("Using simple TOML parser")
            config_dict = parse_simple_toml(config_path)

        logger.info("Loaded config from: {}".format(config_path))
        return parse_config_dict(config_dict)

    except Exception as e:
        raise ValueError("Error parsing config file: {}".format(str(e)))


def parse_simple_toml(config_path):
    """
    Simple TOML parser for basic topology configuration
    Fallback when toml/pytoml libraries are not available

    Args:
        config_path: Path to TOML file

    Returns:
        dict: Parsed configuration dictionary
    """
    config = {}
    rules = []

    with open(config_path, 'r') as f:
        current_rule = {}
        in_rules_section = False

        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Handle rules array start/end
            if line.startswith('[[') and line.endswith(']]'):
                # Save previous rule if exists
                if current_rule:
                    rules.append(current_rule)
                    current_rule = {}
                in_rules_section = True
                continue

            # Handle key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if in_rules_section:
                    current_rule[key] = value
                else:
                    config[key] = value

        # Add last rule
        if current_rule:
            rules.append(current_rule)

    config['rules'] = rules
    return config


def parse_config_dict(config_dict):
    """
    Parse configuration dictionary into TopologyConfig object

    Args:
        config_dict: Configuration dictionary

    Returns:
        TopologyConfig: Parsed configuration object
    """
    # Required fields
    gdb_path = config_dict.get('gdb_path')
    dataset_name = config_dict.get('dataset_name')
    topology_name = config_dict.get('topology_name')

    # gdb_path is optional - will be taken from command line if not in config
    if not gdb_path:
        gdb_path = None
    else:
        # Normalize path separators
        gdb_path = gdb_path.replace('/', '\\')

    if not dataset_name:
        raise ValueError("Missing required field: dataset_name")
    if not topology_name:
        raise ValueError("Missing required field: topology_name")

    # Parse rules
    rules = []
    rules_list = config_dict.get('rules', [])

    for rule_dict in rules_list:
        rule = parse_rule_dict(rule_dict)
        rules.append(rule)

    logger.debug("Parsed config with {} rules".format(len(rules)))

    return TopologyConfig(
        gdb_path=gdb_path,
        dataset_name=dataset_name,
        topology_name=topology_name,
        rules=rules
    )


def parse_rule_dict(rule_dict):
    """
    Parse rule dictionary into TopologyRule object

    Args:
        rule_dict: Rule configuration dictionary

    Returns:
        TopologyRule: Parsed rule object
    """
    # Support both old and new parameter names
    fc1 = rule_dict.get('fc1') or rule_dict.get('origin_fc')
    rule_type = rule_dict.get('rule') or rule_dict.get('rule_type')
    fc2 = rule_dict.get('fc2') or rule_dict.get('destination_fc')

    if not fc1:
        raise ValueError("Rule missing required field: fc1 (origin_fc)")
    if not rule_type:
        raise ValueError("Rule missing required field: rule (rule_type)")

    return TopologyRule(
        origin_fc=fc1,
        rule_type=rule_type,
        destination_fc=fc2
    )


def validate_config(config):
    """
    Validate configuration object

    Args:
        config: TopologyConfig object

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate GDB path format (if provided in config)
    if config.gdb_path and not config.gdb_path.endswith('.gdb'):
        raise ValueError("gdb_path must end with .gdb: {}".format(config.gdb_path))

    # Validate dataset name
    if not config.dataset_name:
        raise ValueError("dataset_name cannot be empty")

    # Validate topology name
    if not config.topology_name:
        raise ValueError("topology_name cannot be empty")

    # Validate rules
    for rule in config.rules:
        validate_rule(rule)

    logger.info("Configuration validated successfully")
    return True


def validate_rule(rule):
    """
    Validate individual rule

    Args:
        rule: TopologyRule object

    Returns:
        bool: True if rule is valid

    Raises:
        ValueError: If rule is invalid
    """
    # Valid rule types
    valid_rule_types = [
        'MUST_NOT_OVERLAP',
        'MUST_NOT_OVERLAP_WITH',
        'MUST_NOT_HAVE_GAPS',
        'MUST_BE_INSIDE',
        'MUST_BE_COVERED_BY',
        'MUST_NOT_INTERSECT',
        'MUST_NOT_HAVE_DANGLES',
        'MUST_BE_SINGLE_PART'
    ]

    if rule.rule_type not in valid_rule_types:
        raise ValueError("Invalid rule_type: {}. Must be one of: {}".format(
            rule.rule_type, ', '.join(valid_rule_types)))

    # Some rule types require destination_fc
    if rule.rule_type in ['MUST_BE_INSIDE', 'MUST_BE_COVERED_BY']:
        if not rule.destination_fc:
            raise ValueError("Rule type {} requires destination_fc".format(rule.rule_type))

    return True


def get_rules(config):
    """
    Get rules from configuration

    Args:
        config: TopologyConfig object

    Returns:
        list: List of TopologyRule objects
    """
    return config.rules


def save_config(config, config_path):
    """
    Save configuration to TOML file

    Args:
        config: TopologyConfig object
        config_path: Path to save configuration
    """
    try:
        if toml:
            config_dict = {
                'gdb_path': config.gdb_path,
                'dataset_name': config.dataset_name,
                'topology_name': config.topology_name,
                'rules': [
                    {
                        'origin_fc': rule.origin_fc,
                        'rule_type': rule.rule_type,
                        'destination_fc': rule.destination_fc
                    }
                    for rule in config.rules
                ]
            }
            with open(config_path, 'w') as f:
                toml.dump(config_dict, f)
        else:
            # Simple TOML output
            with open(config_path, 'w') as f:
                f.write('gdb_path = "{}"\n'.format(config.gdb_path))
                f.write('dataset_name = "{}"\n'.format(config.dataset_name))
                f.write('topology_name = "{}"\n'.format(config.topology_name))
                f.write('\n')
                for rule in config.rules:
                    f.write('[[rules]]\n')
                    f.write('origin_fc = "{}"\n'.format(rule.origin_fc))
                    f.write('rule_type = "{}"\n'.format(rule.rule_type))
                    if rule.destination_fc:
                        f.write('destination_fc = "{}"\n'.format(rule.destination_fc))
                    f.write('\n')

        logger.info("Saved config to: {}".format(config_path))

    except Exception as e:
        raise ValueError("Error saving config file: {}".format(str(e)))