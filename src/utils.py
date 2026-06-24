"""
Core utilities for Topology Management System
"""

import os
import arcpy
import functools

from src.logger import get_logger

logger = get_logger(__name__)


def check_arcgis_license():
    """
    Check if ArcGIS license is available

    Returns:
        bool: True if license is available

    Raises:
        RuntimeError: If no ArcGIS license is available
    """
    try:
        if arcpy.CheckProduct("ArcInfo") == "Available":
            logger.info("ArcGIS Advanced (ArcInfo) license available")
            return True
        elif arcpy.CheckProduct("ArcEditor") == "Available":
            logger.warning("ArcGIS Standard license available (some features may be limited)")
            return True
        elif arcpy.CheckProduct("ArcView") == "Available":
            logger.warning("ArcGIS Basic license available (topology features limited)")
            return True
        else:
            raise RuntimeError("No ArcGIS license available")
    except Exception as e:
        logger.error("Error checking ArcGIS license: {}".format(str(e)))
        raise


def validate_gdb_path(gdb_path):
    """
    Validate that GDB exists and is accessible

    Args:
        gdb_path: Path to geodatabase

    Returns:
        str: Validated GDB path

    Raises:
        ValueError: If GDB doesn't exist or is invalid
    """
    if not gdb_path:
        raise ValueError("GDB path cannot be empty")

    if not os.path.exists(gdb_path):
        raise ValueError("GDB does not exist: {}".format(gdb_path))

    # Check if it's a valid geodatabase
    try:
        arcpy.env.workspace = gdb_path
        desc = arcpy.Describe(gdb_path)
        if desc.dataType != "Workspace":
            raise ValueError("Path is not a valid geodatabase: {}".format(gdb_path))
    except arcpy.ExecuteError as e:
        raise ValueError("Invalid geodatabase: {}".format(str(e)))
    finally:
        arcpy.env.workspace = ""

    logger.info("Validated GDB: {}".format(gdb_path))
    return gdb_path


def validate_featureclass(gdb_path, fc_name):
    """
    Validate that feature class exists in GDB

    Args:
        gdb_path: Path to geodatabase
        fc_name: Name of feature class

    Returns:
        str: Full path to feature class

    Raises:
        ValueError: If feature class doesn't exist
    """
    arcpy.env.workspace = gdb_path
    try:
        if not arcpy.Exists(fc_name):
            raise ValueError("Feature class does not exist: {}".format(fc_name))
        return os.path.join(gdb_path, fc_name)
    except arcpy.ExecuteError as e:
        raise ValueError("Error validating feature class: {}".format(str(e)))
    finally:
        arcpy.env.workspace = ""


def create_dataset_if_not_exists(gdb_path, dataset_name, spatial_reference=None):
    """
    Create feature dataset if it doesn't exist

    Args:
        gdb_path: Path to geodatabase
        dataset_name: Name of feature dataset
        spatial_reference: Spatial reference object (optional)

    Returns:
        str: Path to feature dataset
    """
    dataset_path = os.path.join(gdb_path, dataset_name)

    if arcpy.Exists(dataset_path):
        logger.info("Dataset already exists: {}".format(dataset_name))
        return dataset_path

    try:
        arcpy.CreateFeatureDataset_management(gdb_path, dataset_name, spatial_reference)
        logger.info("Created dataset: {}".format(dataset_name))
        return dataset_path
    except arcpy.ExecuteError as e:
        logger.error("Error creating dataset: {}".format(str(e)))
        raise


def get_featureclass_type(fc_path):
    """
    Get the geometry type of a feature class

    Args:
        fc_path: Path to feature class

    Returns:
        str: Geometry type (POINT, LINE, POLYGON, etc.)
    """
    try:
        desc = arcpy.Describe(fc_path)
        return desc.shapeType
    except arcpy.ExecuteError as e:
        logger.error("Error getting feature class type: {}".format(str(e)))
        raise


def get_spatial_reference(fc_path):
    """
    Get the spatial reference of a feature class

    Args:
        fc_path: Path to feature class

    Returns:
        SpatialReference object
    """
    try:
        desc = arcpy.Describe(fc_path)
        return desc.spatialReference
    except arcpy.ExecuteError as e:
        logger.error("Error getting spatial reference: {}".format(str(e)))
        raise


def handle_arcpy_error(func):
    """
    Decorator for handling ArcPy errors gracefully

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except arcpy.ExecuteError as e:
            logger.error("ArcPy error in {}: {}".format(func.__name__, str(e)))
            raise
        except Exception as e:
            logger.error("Error in {}: {}".format(func.__name__, str(e)))
            raise
    return wrapper


def progress_callback(current, total):
    """
    Progress reporting callback

    Args:
        current: Current item number
        total: Total number of items
    """
    if total > 0:
        percent = int((current / total) * 100)
        logger.debug("Progress: {}/{} ({}%)".format(current, total, percent))


def list_featureclasses(gdb_path):
    """
    List all feature classes in a GDB (including those in datasets)

    Args:
        gdb_path: Path to geodatabase

    Returns:
        list: List of feature class names
    """
    arcpy.env.workspace = gdb_path
    try:
        # Get feature classes in root
        fcs = []
        datasets = arcpy.ListDatasets()

        # Add feature classes from datasets
        for dataset in datasets:
            arcpy.env.workspace = os.path.join(gdb_path, dataset)
            dataset_fcs = arcpy.ListFeatureClasses()
            for fc in dataset_fcs:
                fcs.append(os.path.join(dataset, fc))

        # Add standalone feature classes
        arcpy.env.workspace = gdb_path
        standalone_fcs = arcpy.ListFeatureClasses()
        fcs.extend(standandalone_fcs)

        logger.info("Found {} feature classes".format(len(fcs)))
        return fcs
    except arcpy.ExecuteError as e:
        logger.error("Error listing feature classes: {}".format(str(e)))
        raise
    finally:
        arcpy.env.workspace = ""


def list_datasets(gdb_path):
    """
    List all feature datasets in a GDB

    Args:
        gdb_path: Path to geodatabase

    Returns:
        list: List of dataset names
    """
    arcpy.env.workspace = gdb_path
    try:
        datasets = arcpy.ListDatasets()
        logger.info("Found {} datasets".format(len(datasets)))
        return datasets if datasets else []
    except arcpy.ExecuteError as e:
        logger.error("Error listing datasets: {}".format(str(e)))
        raise
    finally:
        arcpy.env.workspace = ""


def get_gdb_structure(gdb_path):
    """
    Get the structure of a GDB (datasets and their feature classes)

    Args:
        gdb_path: Path to geodatabase

    Returns:
        dict: Structure mapping datasets to lists of feature classes
    """
    arcpy.env.workspace = gdb_path
    structure = {}

    try:
        # Get standalone feature classes
        arcpy.env.workspace = gdb_path
        standalone_fcs = arcpy.ListFeatureClasses()
        if standalone_fcs:
            structure[""] = standalone_fcs  # Empty string for root level

        # Get feature datasets and their feature classes
        datasets = arcpy.ListDatasets()
        for dataset in datasets:
            dataset_path = os.path.join(gdb_path, dataset)
            arcpy.env.workspace = dataset_path
            dataset_fcs = arcpy.ListFeatureClasses()
            if dataset_fcs:
                structure[dataset] = dataset_fcs

        logger.info("GDB structure: {} datasets, {} total feature classes".format(
            len(structure), sum(len(fcs) for fcs in structure.values())))
        return structure
    except arcpy.ExecuteError as e:
        logger.error("Error getting GDB structure: {}".format(str(e)))
        raise
    finally:
        arcpy.env.workspace = ""