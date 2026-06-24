"""
Geodatabase operations for Topology Management System
Handles flatten and restore operations
"""

import os
import arcpy
import json

from src.logger import get_logger
from src.utils import (
    validate_gdb_path, list_featureclasses, list_datasets,
    get_spatial_reference, handle_arcpy_error, create_dataset_if_not_exists
)

logger = get_logger(__name__)


class GDBStructure(object):
    """Stores GDB structure information for restore operations"""

    def __init__(self, gdb_path):
        self.gdb_path = gdb_path
        self.datasets = {}  # dataset_name -> [feature_classes]
        self.standalone_fcs = []

    def add_dataset(self, dataset_name, feature_classes):
        """Add dataset and its feature classes"""
        self.datasets[dataset_name] = feature_classes

    def add_standalone_fc(self, fc_name):
        """Add standalone feature class"""
        self.standalone_fcs.append(fc_name)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'gdb_path': self.gdb_path,
            'datasets': self.datasets,
            'standalone_fcs': self.standalone_fcs
        }

    @classmethod
    def from_dict(cls, data):
        """Create GDBStructure from dictionary"""
        obj = cls(data['gdb_path'])
        obj.datasets = data['datasets']
        obj.standalone_fcs = data['standalone_fcs']
        return obj

    def __repr__(self):
        return "GDBStructure(datasets={}, standalone_fcs={})".format(
            len(self.datasets), len(self.standalone_fcs))


@handle_arcpy_error
def flatten_gdb(input_gdb, output_gdb, dataset_name="Infrastructure"):
    """
    Flatten GDB structure by moving all feature classes to single dataset

    Args:
        input_gdb: Path to input GDB
        output_gdb: Path to output flattened GDB
        dataset_name: Name of target dataset (default: Infrastructure)

    Returns:
        GDBStructure: Original structure for restore operations
    """
    logger.info("Flattening GDB: {} -> {}".format(input_gdb, output_gdb))

    # Validate input
    validate_gdb_path(input_gdb)

    # Capture original structure
    original_structure = capture_gdb_structure(input_gdb)

    # Create output GDB
    create_output_gdb(input_gdb, output_gdb)

    # Get spatial reference from first feature class
    arcpy.env.workspace = input_gdb
    all_fcs = list_featureclasses(input_gdb)

    if not all_fcs:
        logger.warning("No feature classes found in input GDB")
        return original_structure

    spatial_ref = get_spatial_reference(os.path.join(input_gdb, all_fcs[0]))
    logger.info("Using spatial reference: {}".format(spatial_ref.name))

    # Create target dataset
    target_dataset = create_dataset_if_not_exists(output_gdb, dataset_name, spatial_ref)

    # Move all feature classes to target dataset
    moved_count = 0
    failed_count = 0
    empty_count = 0
    total_features = 0
    failed_fcs = []

    for fc_info in all_fcs:
        try:
            fc_path = os.path.join(input_gdb, fc_info)
            fc_name = os.path.basename(fc_info)
            target_fc = os.path.join(target_dataset, fc_name)

            # Check if feature class is empty
            fc_count = int(arcpy.GetCount_management(fc_path).getOutput(0))
            total_features += fc_count

            if fc_count == 0:
                empty_count += 1
                logger.debug("Empty feature class: {}".format(fc_info))

            logger.info("Moving feature class: {} ({} features)".format(fc_info, fc_count))
            arcpy.FeatureClassToFeatureClass_conversion(fc_path, target_dataset, fc_name)
            moved_count += 1

        except arcpy.ExecuteError as e:
            failed_count += 1
            failed_fcs.append(fc_info)
            logger.error("Error moving feature class {}: {}".format(fc_info, str(e)))

    # Print comprehensive summary
    print("\n" + "="*50)
    print("FLATTEN OPERATION SUMMARY")
    print("="*50)
    print("Original datasets: {}".format(len(original_structure.datasets)))
    print("Total feature classes found: {}".format(len(all_fcs)))
    print("Successfully moved: {}".format(moved_count))
    print("Failed: {}".format(failed_count))
    print("Empty feature classes: {}".format(empty_count))
    print("Total features copied: {}".format(total_features))

    if failed_count > 0:
        print("\nFailed feature classes:")
        for failed_fc in failed_fcs:
            print("  - {}".format(failed_fc))

    print("="*50)

    logger.info("Flatten complete. Moved {} feature classes to {}".format(moved_count, dataset_name))

    # Save structure metadata to output GDB
    save_structure_metadata(output_gdb, original_structure)

    return original_structure


@handle_arcpy_error
def restore_gdb(flattened_gdb, output_gdb=None):
    """
    Restore original GDB structure from flattened GDB

    Args:
        flattened_gdb: Path to flattened GDB
        output_gdb: Path to output restored GDB (optional, defaults to original name)

    Returns:
        str: Path to restored GDB
    """
    logger.info("Restoring GDB structure from: {}".format(flattened_gdb))

    # Validate input
    validate_gdb_path(flattened_gdb)

    # Load structure metadata
    original_structure = load_structure_metadata(flattened_gdb)

    if not original_structure:
        raise ValueError("No structure metadata found in flattened GDB")

    # Determine output path
    if not output_gdb:
        output_gdb = original_structure.gdb_path
        if output_gdb == flattened_gdb:
            output_gdb = flattened_gdb.replace('_flattened.gdb', '_restored.gdb')

    logger.info("Restoring to: {}".format(output_gdb))

    # Create output GDB
    create_output_gdb(flattened_gdb, output_gdb)

    # Restore structure
    arcpy.env.workspace = flattened_gdb
    total_fcs = sum(len(fcs) for fcs in original_structure.datasets.values())
    total_fcs += len(original_structure.standalone_fcs)

    restored_count = 0
    failed_count = 0
    total_features = 0
    failed_fcs = []

    # Restore datasets and their feature classes
    for dataset_name, fc_list in original_structure.datasets.items():
        if dataset_name:  # Skip empty dataset names (standalone)
            try:
                # Create dataset
                logger.info("Creating dataset: {}".format(dataset_name))
                arcpy.env.workspace = flattened_gdb
                fc_in_dataset = fc_list[0] if fc_list else None

                if fc_in_dataset:
                    fc_path = os.path.join('Infrastructure', fc_in_dataset)
                    spatial_ref = get_spatial_reference(fc_path)
                    create_dataset_if_not_exists(output_gdb, dataset_name, spatial_ref)
                else:
                    create_dataset_if_not_exists(output_gdb, dataset_name)

                # Move feature classes to dataset
                for fc_name in fc_list:
                    try:
                        source_fc = os.path.join(flattened_gdb, 'Infrastructure', fc_name)
                        target_dataset = os.path.join(output_gdb, dataset_name)

                        # Get feature count
                        fc_count = int(arcpy.GetCount_management(source_fc).getOutput(0))
                        total_features += fc_count

                        logger.info("Restoring feature class: {} to {} ({} features)".format(fc_name, dataset_name, fc_count))
                        arcpy.FeatureClassToFeatureClass_conversion(source_fc, target_dataset, fc_name)
                        restored_count += 1

                    except arcpy.ExecuteError as e:
                        failed_count += 1
                        failed_fcs.append(dataset_name + '\\' + fc_name)
                        logger.error("Error restoring feature class {}: {}".format(fc_name, str(e)))

            except arcpy.ExecuteError as e:
                logger.error("Error restoring dataset {}: {}".format(dataset_name, str(e)))
                raise

    # Restore standalone feature classes
    for fc_name in original_structure.standalone_fcs:
        try:
            source_fc = os.path.join(flattened_gdb, 'Infrastructure', fc_name)
            target_fc = os.path.join(output_gdb, fc_name)

            # Get feature count
            fc_count = int(arcpy.GetCount_management(source_fc).getOutput(0))
            total_features += fc_count

            logger.info("Restoring standalone feature class: {} ({} features)".format(fc_name, fc_count))
            arcpy.FeatureClassToFeatureClass_conversion(source_fc, output_gdb, fc_name)
            restored_count += 1

        except arcpy.ExecuteError as e:
            failed_count += 1
            failed_fcs.append(fc_name)
            logger.error("Error restoring feature class {}: {}".format(fc_name, str(e)))

    # Print comprehensive summary
    print("\n" + "="*50)
    print("RESTORE OPERATION SUMMARY")
    print("="*50)
    print("Datasets to restore: {}".format(len(original_structure.datasets)))
    print("Total feature classes to restore: {}".format(total_fcs))
    print("Successfully restored: {}".format(restored_count))
    print("Failed: {}".format(failed_count))
    print("Total features restored: {}".format(total_features))

    if failed_count > 0:
        print("\nFailed feature classes:")
        for failed_fc in failed_fcs:
            print("  - {}".format(failed_fc))

    print("="*50)

    logger.info("Restore complete. Restored {} feature classes".format(restored_count))
    return output_gdb


def capture_gdb_structure(gdb_path):
    """
    Capture current GDB structure

    Args:
        gdb_path: Path to geodatabase

    Returns:
        GDBStructure: GDB structure object
    """
    logger.info("Capturing GDB structure: {}".format(gdb_path))

    structure = GDBStructure(gdb_path)

    arcpy.env.workspace = gdb_path

    # Get datasets
    datasets = list_datasets(gdb_path)

    # Get feature classes in each dataset
    for dataset in datasets:
        arcpy.env.workspace = os.path.join(gdb_path, dataset)
        dataset_fcs = arcpy.ListFeatureClasses()
        if dataset_fcs:
            structure.add_dataset(dataset, dataset_fcs)

    # Get standalone feature classes
    arcpy.env.workspace = gdb_path
    standalone_fcs = arcpy.ListFeatureClasses()
    for fc in standalone_fcs:
        structure.add_standalone_fc(fc)

    logger.info("Captured structure: {} datasets, {} standalone feature classes".format(
        len(structure.datasets), len(structure.standalone_fcs)))

    return structure


def create_output_gdb(input_gdb, output_gdb):
    """
    Create output GDB with same spatial reference as input

    Args:
        input_gdb: Path to input GDB
        output_gdb: Path to output GDB to create
    """
    if arcpy.Exists(output_gdb):
        error_msg = "Output GDB already exists: {}\nPlease manually delete the existing file before proceeding.".format(output_gdb)
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Get folder path
    output_folder = os.path.dirname(output_gdb)
    output_name = os.path.basename(output_gdb).replace('.gdb', '')

    logger.info("Creating output GDB: {}".format(output_gdb))
    arcpy.CreateFileGDB_management(output_folder, output_name)


def save_structure_metadata(gdb_path, structure):
    """
    Save structure metadata to GDB

    Args:
        gdb_path: Path to GDB
        structure: GDBStructure object
    """
    # Create a table in GDB to store structure metadata
    table_name = "_structure_metadata"

    # Delete existing table if present
    table_path = os.path.join(gdb_path, table_name)
    if arcpy.Exists(table_path):
        arcpy.Delete_management(table_path)

    # Save as JSON file in GDB folder (as fallback)
    gdb_folder = gdb_path
    metadata_file = os.path.join(gdb_folder, "_structure_metadata.json")

    with open(metadata_file, 'w') as f:
        json.dump(structure.to_dict(), f, indent=2)

    logger.info("Saved structure metadata to: {}".format(metadata_file))


def load_structure_metadata(gdb_path):
    """
    Load structure metadata from GDB

    Args:
        gdb_path: Path to GDB

    Returns:
        GDBStructure: GDB structure object or None if not found
    """
    # Try to load from JSON file
    metadata_file = os.path.join(gdb_path, "_structure_metadata.json")

    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            logger.info("Loaded structure metadata from: {}".format(metadata_file))
            return GDBStructure.from_dict(data)
        except Exception as e:
            logger.error("Error loading structure metadata: {}".format(str(e)))
            return None

    logger.warning("No structure metadata found")
    return None


def get_flattened_dataset_path(gdb_path, dataset_name="Infrastructure"):
    """
    Get path to flattened dataset

    Args:
        gdb_path: Path to GDB
        dataset_name: Name of dataset

    Returns:
        str: Path to dataset
    """
    return os.path.join(gdb_path, dataset_name)