"""
Duplicate feature removal for Topology Validation System
Handles identification and removal of duplicate features
"""

import os
import arcpy

from src.logger import get_logger
from src.utils import validate_gdb_path, handle_arcpy_error

logger = get_logger(__name__)


@handle_arcpy_error
def remove_duplicates(gdb_path, dataset_name=None, feature_class=None, fields=None):
    """
    Remove duplicate features from geodatabase

    Args:
        gdb_path: Path to geodatabase
        dataset_name: Optional dataset name (if None, processes all feature classes)
        feature_class: Optional specific feature class name
        fields: List of fields to check for duplicates (if None, uses geometry)

    Returns:
        dict: Results including counts of duplicates found and removed
    """
    logger.info("Removing duplicates from: {}".format(gdb_path))

    # Validate input
    validate_gdb_path(gdb_path)

    results = {
        'feature_classes_processed': 0,
        'duplicates_found': 0,
        'duplicates_removed': 0,
        'errors': []
    }

    # Determine feature classes to process
    if feature_class:
        feature_classes = [feature_class]
        logger.info("Processing specific feature class: {}".format(feature_class))
    elif dataset_name:
        feature_classes = get_feature_classes_in_dataset(gdb_path, dataset_name)
        logger.info("Processing {} feature classes in dataset: {}".format(len(feature_classes), dataset_name))
    else:
        feature_classes = get_all_feature_classes(gdb_path)
        logger.info("Processing all {} feature classes in GDB".format(len(feature_classes)))

    # Process each feature class
    for fc_name in feature_classes:
        try:
            fc_result = remove_duplicates_from_fc(gdb_path, fc_name, fields)
            results['feature_classes_processed'] += 1
            results['duplicates_found'] += fc_result['found']
            results['duplicates_removed'] += fc_result['removed']
            logger.info("Processed {}: {} duplicates removed".format(fc_name, fc_result['removed']))

        except Exception as e:
            error_msg = "Error processing {}: {}".format(fc_name, str(e))
            logger.error(error_msg)
            results['errors'].append(error_msg)

    logger.info("Duplicate removal complete")
    logger.info("Feature classes processed: {}".format(results['feature_classes_processed']))
    logger.info("Total duplicates found: {}".format(results['duplicates_found']))
    logger.info("Total duplicates removed: {}".format(results['duplicates_removed']))

    if results['errors']:
        logger.warning("Errors encountered: {}".format(len(results['errors'])))

    return results


def remove_duplicates_from_fc(gdb_path, fc_name, fields=None):
    """
    Remove duplicates from a single feature class

    Args:
        gdb_path: Path to geodatabase
        fc_name: Feature class name
        fields: List of fields to check for duplicates (None for geometry only)

    Returns:
        dict: Results for this feature class
    """
    fc_path = os.path.join(gdb_path, fc_name)

    if not arcpy.Exists(fc_path):
        raise ValueError("Feature class does not exist: {}".format(fc_path))

    logger.debug("Processing feature class: {}".format(fc_name))

    # Get total feature count
    total_count = int(arcpy.GetCount_management(fc_path).getOutput(0))
    logger.debug("Total features: {}".format(total_count))

    if total_count == 0:
        return {'found': 0, 'removed': 0}

    # Find duplicates
    duplicate_ids = find_duplicates(fc_path, fields)

    duplicates_found = len(duplicate_ids)
    logger.debug("Duplicates found: {}".format(duplicates_found))

    if duplicates_found == 0:
        return {'found': 0, 'removed': 0}

    # Remove duplicates
    duplicates_removed = delete_features(fc_path, duplicate_ids)
    logger.debug("Duplicates removed: {}".format(duplicates_removed))

    return {'found': duplicates_found, 'removed': duplicates_removed}


def find_duplicates(fc_path, fields=None):
    """
    Find duplicate features in feature class

    Args:
        fc_path: Path to feature class
        fields: List of fields to check (None for geometry only)

    Returns:
        list: List of duplicate feature IDs to remove
    """
    duplicate_ids = []

    # Build SQL expression for finding duplicates
    if fields and len(fields) > 0:
        # Find duplicates based on attribute fields
        return find_attribute_duplicates(fc_path, fields)
    else:
        # Find duplicates based on geometry
        return find_geometry_duplicates(fc_path)


def find_geometry_duplicates(fc_path):
    """
    Find duplicates based on geometry (identical shapes)

    Args:
        fc_path: Path to feature class

    Returns:
        list: List of duplicate feature IDs
    """
    duplicate_ids = []

    try:
        # Simple approach: compare geometries using JSON representation
        seen_geometries = {}
        with arcpy.da.SearchCursor(fc_path, ["OID@", "SHAPE@JSON"]) as cursor:
            for row in cursor:
                fid = row[0]
                geometry_json = row[1]

                if geometry_json in seen_geometries:
                    # This is a duplicate
                    duplicate_ids.append(fid)
                    logger.debug("Found duplicate: OID {} matches OID {}".format(fid, seen_geometries[geometry_json]))
                else:
                    # First occurrence
                    seen_geometries[geometry_json] = fid

        logger.info("Found {} duplicates based on identical geometry".format(len(duplicate_ids)))
        return duplicate_ids

    except Exception as e:
        logger.error("Error finding geometry duplicates: {}".format(str(e)))
        return []

        # Find features that have matches (keep one, remove others)
        if arcpy.Exists(output_fc):
            match_counts = {}
            with arcpy.da.SearchCursor(output_fc, ["TARGET_FID", "JOIN_COUNT"]) as cursor:
                for row in cursor:
                    target_fid = row[0]
                    join_count = row[1]
                    if join_count > 1:
                        if target_fid not in match_counts:
                            match_counts[target_fid] = join_count

            # Get all duplicate IDs (keep first occurrence of each duplicate set)
            seen_geometries = {}
            with arcpy.da.SearchCursor(fc_path, ["OID@", "SHAPE@JSON"]) as cursor:
                for row in cursor:
                    fid = row[0]
                    geometry_json = row[1]

                    if geometry_json in seen_geometries:
                        duplicate_ids.append(fid)
                    else:
                        seen_geometries[geometry_json] = fid

    except Exception as e:
        logger.error("Error finding geometry duplicates: {}".format(str(e)))

    return duplicate_ids


def find_attribute_duplicates(fc_path, fields):
    """
    Find duplicates based on attribute fields

    Args:
        fc_path: Path to feature class
        fields: List of field names to check

    Returns:
        list: List of duplicate feature IDs
    """
    duplicate_ids = []

    try:
        # Build SQL to group by specified fields
        field_names = ["OID@"] + fields

        # Track seen combinations
        seen_combinations = {}
        first_occurrences = {}

        with arcpy.da.SearchCursor(fc_path, field_names) as cursor:
            for row in cursor:
                fid = row[0]
                # Create tuple of field values for comparison
                key = tuple(row[1:])  # Skip OID

                if key in seen_combinations:
                    # This is a duplicate
                    duplicate_ids.append(fid)
                    seen_combinations[key].append(fid)
                else:
                    # First occurrence
                    seen_combinations[key] = [fid]
                    first_occurrences[key] = fid

        # Remove all but first occurrence of each duplicate set
        duplicates_to_remove = []
        for key, ids in seen_combinations.items():
            if len(ids) > 1:
                # Keep first occurrence, mark rest for removal
                duplicates_to_remove.extend(ids[1:])

        return duplicates_to_remove

    except Exception as e:
        logger.error("Error finding attribute duplicates: {}".format(str(e)))
        return []


def delete_features(fc_path, feature_ids):
    """
    Delete features by their IDs

    Args:
        fc_path: Path to feature class
        feature_ids: List of feature IDs to delete

    Returns:
        int: Number of features deleted
    """
    if not feature_ids:
        return 0

    try:
        # Delete features one by one using update cursor
        deleted_count = 0
        with arcpy.da.UpdateCursor(fc_path, ["OID@"]) as cursor:
            for row in cursor:
                if row[0] in feature_ids:
                    cursor.deleteRow()
                    deleted_count += 1

        logger.debug("Deleted {} features".format(deleted_count))
        return deleted_count

    except Exception as e:
        logger.error("Error deleting features: {}".format(str(e)))
        return 0


def create_temporary_fc(fc_path):
    """
    Create temporary copy of feature class for comparison

    Args:
        fc_path: Path to original feature class

    Returns:
        str: Path to temporary feature class or None
    """
    try:
        temp_fc = os.path.join("memory", "temp_compare")
        if arcpy.Exists(temp_fc):
            arcpy.Delete_management(temp_fc)

        arcpy.CopyFeatures_management(fc_path, temp_fc)
        return temp_fc
    except Exception as e:
        logger.warning("Could not create temporary feature class: {}".format(str(e)))
        return None


def get_all_feature_classes(gdb_path):
    """
    Get all feature classes in GDB (including those in datasets)

    Args:
        gdb_path: Path to geodatabase

    Returns:
        list: List of feature class names with full paths
    """
    arcpy.env.workspace = gdb_path
    all_fcs = []

    # Get feature classes from datasets
    datasets = arcpy.ListDatasets()
    for dataset in datasets:
        arcpy.env.workspace = os.path.join(gdb_path, dataset)
        dataset_fcs = arcpy.ListFeatureClasses()
        for fc in dataset_fcs:
            all_fcs.append(os.path.join(dataset, fc))

    # Get standalone feature classes
    arcpy.env.workspace = gdb_path
    standalone_fcs = arcpy.ListFeatureClasses()
    all_fcs.extend(standalone_fcs)

    return all_fcs


def get_feature_classes_in_dataset(gdb_path, dataset_name):
    """
    Get feature classes in a specific dataset

    Args:
        gdb_path: Path to geodatabase
        dataset_name: Dataset name

    Returns:
        list: List of feature class names with dataset prefix
    """
    dataset_path = os.path.join(gdb_path, dataset_name)

    if not arcpy.Exists(dataset_path):
        raise ValueError("Dataset does not exist: {}".format(dataset_name))

    arcpy.env.workspace = dataset_path
    fcs = arcpy.ListFeatureClasses()

    return [os.path.join(dataset_name, fc) for fc in fcs]


def report_duplicates(gdb_path, dataset_name=None, feature_class=None, fields=None):
    """
    Report duplicates without removing them

    Args:
        gdb_path: Path to geodatabase
        dataset_name: Optional dataset name
        feature_class: Optional specific feature class name
        fields: List of fields to check for duplicates

    Returns:
        dict: Report of duplicate findings
    """
    logger.info("Reporting duplicates for: {}".format(gdb_path))

    validate_gdb_path(gdb_path)

    report = {
        'feature_classes': {},
        'total_duplicates': 0
    }

    # Determine feature classes to process
    if feature_class:
        feature_classes = [feature_class]
    elif dataset_name:
        feature_classes = get_feature_classes_in_dataset(gdb_path, dataset_name)
    else:
        feature_classes = get_all_feature_classes(gdb_path)

    # Check each feature class for duplicates
    for fc_name in feature_classes:
        fc_path = os.path.join(gdb_path, fc_name)
        duplicate_ids = find_duplicates(fc_path, fields)

        if duplicate_ids:
            report['feature_classes'][fc_name] = {
                'count': len(duplicate_ids),
                'ids': duplicate_ids
            }
            report['total_duplicates'] += len(duplicate_ids)

            logger.info("Found {} duplicates in {}".format(len(duplicate_ids), fc_name))

    return report