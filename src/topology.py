"""
Topology management for Topology Validation System
Handles topology creation and validation
"""

import os
import arcpy

from src.logger import get_logger
from src.config import TopologyConfig, TopologyRule, validate_config
from src.utils import validate_gdb_path, validate_featureclass, handle_arcpy_error

logger = get_logger(__name__)


# Topology rule constants
RULE_MUST_NOT_OVERLAP = "MUST_NOT_OVERLAP"
RULE_MUST_NOT_OVERLAP_WITH = "MUST_NOT_OVERLAP_WITH"
RULE_MUST_NOT_HAVE_GAPS = "MUST_NOT_HAVE_GAPS"
RULE_MUST_BE_INSIDE = "MUST_BE_INSIDE"
RULE_MUST_BE_COVERED_BY = "MUST_BE_COVERED_BY"
RULE_MUST_NOT_INTERSECT = "MUST_NOT_INTERSECT"
RULE_MUST_NOT_HAVE_DANGLES = "MUST_NOT_HAVE_DANGLES"
RULE_MUST_BE_SINGLE_PART = "MUST_BE_SINGLE_PART"


@handle_arcpy_error
def create_topology(config):
    """
    Create topology from configuration

    Args:
        config: TopologyConfig object

    Returns:
        str: Path to created topology
    """
    logger.info("Creating topology: {}".format(config.topology_name))

    # Validate configuration
    validate_config(config)
    validate_gdb_path(config.gdb_path)

    # Construct dataset path
    dataset_path = os.path.join(config.gdb_path, config.dataset_name)

    if not arcpy.Exists(dataset_path):
        raise ValueError("Dataset does not exist: {}".format(dataset_path))

    # Delete existing topology if present
    topology_path = os.path.join(dataset_path, config.topology_name)
    if arcpy.Exists(topology_path):
        logger.warning("Topology already exists, deleting: {}".format(topology_path))
        arcpy.Delete_management(topology_path)

    # Create topology
    logger.info("Creating topology in dataset: {}".format(config.dataset_name))
    arcpy.CreateTopology_management(dataset_path, config.topology_name)
    logger.info("Created topology: {}".format(topology_path))

    # Add feature classes to topology
    added_fcs = add_feature_classes_to_topology(topology_path, config)
    logger.info("Added {} feature classes to topology".format(added_fcs))

    # Add rules to topology
    added_rules = add_topology_rules(topology_path, config.rules)
    logger.info("Added {} rules to topology".format(added_rules))

    # Validate topology
    validate_topology_rules(topology_path)

    return topology_path


@handle_arcpy_error
def validate_topology(config):
    """
    Validate existing topology

    Args:
        config: TopologyConfig object

    Returns:
        dict: Validation results
    """
    logger.info("Validating topology: {}".format(config.topology_name))

    # Validate configuration
    validate_config(config)
    validate_gdb_path(config.gdb_path)

    # Construct topology path
    topology_path = os.path.join(config.gdb_path, config.dataset_name, config.topology_name)

    if not arcpy.Exists(topology_path):
        raise ValueError("Topology does not exist: {}".format(topology_path))

    # Validate topology rules
    return validate_topology_rules(topology_path)


def add_feature_classes_to_topology(topology_path, config):
    """
    Add feature classes to topology

    Args:
        topology_path: Path to topology
        config: TopologyConfig object

    Returns:
        int: Number of feature classes added
    """
    added_count = 0
    feature_classes = set()

    # Collect unique feature classes from rules
    for rule in config.rules:
        feature_classes.add(rule.origin_fc)
        if rule.destination_fc:
            feature_classes.add(rule.destination_fc)

    # Add each feature class to topology
    for fc_name in feature_classes:
        try:
            # Feature class is in the same dataset as topology
            fc_path = os.path.join(os.path.dirname(topology_path), fc_name)

            if not arcpy.Exists(fc_path):
                logger.warning("Feature class does not exist: {}".format(fc_path))
                continue

            logger.info("Adding feature class to topology: {}".format(fc_name))
            arcpy.AddFeatureClassToTopology_management(topology_path, fc_path)
            added_count += 1

        except arcpy.ExecuteError as e:
            logger.error("Error adding feature class {}: {}".format(fc_name, str(e)))
            raise

    return added_count


def add_topology_rules(topology_path, rules):
    """
    Add rules to topology

    Args:
        topology_path: Path to topology
        rules: List of TopologyRule objects

    Returns:
        int: Number of rules added
    """
    added_count = 0
    failed_count = 0
    skipped_count = 0
    failed_rules = []
    skipped_rules = []

    for rule in rules:
        try:
            add_rule(topology_path, rule)
            added_count += 1
            logger.info("Added rule: {} on {}".format(rule.rule_type, rule.origin_fc))

        except ValueError as e:
            # Feature class doesn't exist, skip this rule
            skipped_count += 1
            skipped_rules.append("{} ({})".format(rule.origin_fc, rule.rule_type))
            logger.info("Skipped rule for {} ({}): {}".format(rule.origin_fc, rule.rule_type, str(e)))

        except arcpy.ExecuteError as e:
            failed_count += 1
            failed_rules.append("{} ({})".format(rule.origin_fc, rule.rule_type))
            logger.warning("Failed to add rule for {} ({}): {}".format(rule.origin_fc, rule.rule_type, str(e)))

    if skipped_count > 0:
        logger.info("Skipped {}/{} rules due to missing feature classes: {}".format(skipped_count, len(rules), skipped_rules))

    if failed_count > 0:
        logger.warning("Failed to add {}/{} rules. Failed rules: {}".format(failed_count, len(rules), failed_rules))

    logger.info("Topology rule summary: {} added, {} skipped, {} failed".format(added_count, skipped_count, failed_count))

    return added_count


def add_rule(topology_path, rule):
    """
    Add single rule to topology

    Args:
        topology_path: Path to topology
        rule: TopologyRule object
    """
    # Get feature class paths
    dataset_path = os.path.dirname(topology_path)
    origin_fc = os.path.join(dataset_path, rule.origin_fc)

    # Check if origin feature class exists
    if not arcpy.Exists(origin_fc):
        logger.warning("Skipping rule for {} (feature class does not exist)".format(rule.origin_fc))
        raise ValueError("Feature class {} does not exist".format(rule.origin_fc))

    # For cross-layer rules, check if destination feature class exists
    if rule.destination_fc:
        destination_fc = os.path.join(dataset_path, rule.destination_fc)
        if not arcpy.Exists(destination_fc):
            logger.warning("Skipping cross-layer rule {} -> {} (destination feature class does not exist)".format(
                rule.origin_fc, rule.destination_fc))
            raise ValueError("Destination feature class {} does not exist".format(rule.destination_fc))

    if rule.rule_type == RULE_MUST_NOT_OVERLAP:
        arcpy.AddRuleToTopology_management(topology_path, "Must Not Overlap (Area)", origin_fc)

    elif rule.rule_type == RULE_MUST_NOT_HAVE_GAPS:
        arcpy.AddRuleToTopology_management(topology_path, "Must Not Have Gaps (Area)", origin_fc)

    elif rule.rule_type == RULE_MUST_BE_INSIDE:
        if not rule.destination_fc:
            raise ValueError("MUST_BE_INSIDE rule requires destination_fc")
        destination_fc = os.path.join(dataset_path, rule.destination_fc)
        arcpy.AddRuleToTopology_management(topology_path, "Must Be Inside (Area-Area)", origin_fc, destination_fc)

    elif rule.rule_type == RULE_MUST_BE_COVERED_BY:
        if not rule.destination_fc:
            raise ValueError("MUST_BE_COVERED_BY rule requires destination_fc")
        destination_fc = os.path.join(dataset_path, rule.destination_fc)
        arcpy.AddRuleToTopology_management(topology_path, "Must Be Covered By (Area-Area)", origin_fc, destination_fc)

    elif rule.rule_type == RULE_MUST_NOT_INTERSECT:
        arcpy.AddRuleToTopology_management(topology_path, "Must Not Intersect (Line)", origin_fc)

    elif rule.rule_type == RULE_MUST_NOT_HAVE_DANGLES:
        arcpy.AddRuleToTopology_management(topology_path, "Must Not Have Dangles (Line)", origin_fc)

    elif rule.rule_type == RULE_MUST_BE_SINGLE_PART:
        arcpy.AddRuleToTopology_management(topology_path, "Must Be Single Part (Line)", origin_fc)

    elif rule.rule_type == RULE_MUST_NOT_OVERLAP_WITH:
        if not rule.destination_fc:
            raise ValueError("MUST_NOT_OVERLAP_WITH rule requires destination_fc")
        destination_fc = os.path.join(dataset_path, rule.destination_fc)
        arcpy.AddRuleToTopology_management(topology_path, "Must Not Overlap With (Area-Area)", origin_fc, destination_fc)

    else:
        raise ValueError("Unknown rule type: {}".format(rule.rule_type))


@handle_arcpy_error
def validate_topology_rules(topology_path):
    """
    Validate topology rules

    Args:
        topology_path: Path to topology

    Returns:
        dict: Validation results with error counts
    """
    logger.info("Validating topology: {}".format(topology_path))

    # Get topology properties
    desc = arcpy.Describe(topology_path)
    original_cluster_tolerance = desc.clusterTolerance

    # Validate topology
    logger.info("Running topology validation...")
    arcpy.ValidateTopology_management(topology_path)

    # Get error counts
    error_counts = get_topology_error_counts(topology_path)

    logger.info("Topology validation complete")
    logger.info("Total topology errors: {}".format(error_counts['total']))

    return error_counts


def get_topology_error_counts(topology_path):
    """
    Get topology error counts

    Args:
        topology_path: Path to topology

    Returns:
        dict: Error counts by type
    """
    # Get topology as a feature class to access error features
    try:
        # Export topology errors
        error_fc_name = "topology_errors"
        error_fc = os.path.join(os.path.dirname(topology_path), error_fc_name)
        if arcpy.Exists(error_fc):
            arcpy.Delete_management(error_fc)

        arcpy.ExportTopologyErrors_management(topology_path, os.path.dirname(topology_path), error_fc_name)

        # Count errors
        if arcpy.Exists(error_fc):
            count = int(arcpy.GetCount_management(error_fc).getOutput(0))
            logger.info("Exported {} topology errors to {}".format(count, error_fc))
            return {'total': count, 'exported': error_fc}
        else:
            return {'total': 0}

    except arcpy.ExecuteError as e:
        logger.error("Error exporting topology errors: {}".format(str(e)))
        return {'total': -1, 'error': str(e)}


def get_topology_properties(topology_path):
    """
    Get topology properties

    Args:
        topology_path: Path to topology

    Returns:
        dict: Topology properties
    """
    desc = arcpy.Describe(topology_path)

    return {
        'name': desc.baseName,
        'cluster_tolerance': desc.clusterTolerance,
        'z_cluster_tolerance': desc.ZClusterTolerance,
        'feature_class_count': len(desc.featureClasses),
        'rules_count': len(desc.rules)
    }


def list_topologies(gdb_path, dataset_name=None):
    """
    List topologies in GDB

    Args:
        gdb_path: Path to geodatabase
        dataset_name: Optional dataset name to filter

    Returns:
        list: List of topology names
    """
    arcpy.env.workspace = gdb_path

    if dataset_name:
        arcpy.env.workspace = os.path.join(gdb_path, dataset_name)

    topologies = []

    # Look for topologies
    for ds in arcpy.ListDatasets():
        if dataset_name and ds != dataset_name:
            continue

        arcpy.env.workspace = os.path.join(gdb_path, ds)
        for item in arcpy.ListDatasets():
            if "Topology" in str(arcpy.Describe(item).dataType):
                topologies.append(item)

    return topologies


def delete_topology(config):
    """
    Delete topology from configuration

    Args:
        config: TopologyConfig object

    Returns:
        bool: True if deleted successfully
    """
    logger.info("Deleting topology: {}".format(config.topology_name))

    topology_path = os.path.join(config.gdb_path, config.dataset_name, config.topology_name)

    if arcpy.Exists(topology_path):
        arcpy.Delete_management(topology_path)
        logger.info("Deleted topology: {}".format(topology_path))
        return True
    else:
        logger.warning("Topology does not exist: {}".format(topology_path))
        return False