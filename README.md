# Topology Management System

A command-line tool for managing ArcGIS Desktop geodatabase topology operations using Python 2.7 and ArcPy.

## Features

- **Flatten**: Consolidate all feature classes from multiple datasets into a single dataset
- **Dedupe**: Remove duplicate features from geodatabases
- **Validate**: Create and validate topology rules from configuration files
- **Restore**: Restore original geodatabase structure from a flattened GDB

## Requirements

- ArcGIS Desktop 10.8 (with Advanced license for topology features)
- Python 2.7 (included with ArcGIS Desktop)
- ArcPy

## Installation

1. Clone this repository
2. Run `env.bat` to set up the ArcGIS Python environment
3. Install TOML library if needed: `pip install toml`

## Usage

### Basic Commands

```bash
# Step 1: Flatten GDB structure
python main.py flatten --gdb input.gdb --output input_flattened.gdb

# Step 2: Remove duplicate features from flattened GDB
python main.py dedupe --gdb input_flattened.gdb --dataset TKMDS
python main.py dedupe --gdb input_flattened.gdb --feature-class BuildingFootprint --report-only

# Step 3: Create and validate topology on cleaned data
python main.py validate --gdb input_flattened.gdb --config topology.config.toml

# Step 4: Restore original structure from cleaned, validated data
python main.py restore --gdb input_flattened.gdb
```

### Command Options

- `--gdb PATH`: Input geodatabase path
- `--output PATH`: Output geodatabase path (for flatten command)
- `--dataset NAME`: Dataset name (default: TKMDS)
- `--config PATH`: Configuration file path (default: topology.config.toml)
- `--feature-class`: Specific feature class to process (for dedupe command)
- `--fields`: Comma-separated list of fields to check for duplicates (for dedupe command)
- `--report-only`: Report duplicates without removing them (for dedupe command)
- `--verbose`: Enable verbose logging

## Configuration

The system uses TOML configuration files to define topology rules:

```toml
dataset_name = "TKMDS"
topology_name = "tkm_topology"

# Mandatory RoadCarriageway Rules
[[rules]]
fc1 = "RoadCarriageway"
rule = "MUST_NOT_OVERLAP"

[[rules]]
fc1 = "RoadCarriageway"
rule = "MUST_NOT_OVERLAP_WITH"
fc2 = "RoadDivider"

# Mandatory Woodland Rules
[[rules]]
fc1 = "Woodland"
rule = "MUST_NOT_OVERLAP"

[[rules]]
fc1 = "Woodland"
rule = "MUST_NOT_OVERLAP_WITH"
fc2 = "Cultivation"

# Mandatory BuildingFootprint Rules
[[rules]]
fc1 = "BuildingFootprint"
rule = "MUST_NOT_OVERLAP"

[[rules]]
fc1 = "BuildingFootprint"
rule = "MUST_NOT_OVERLAP_WITH"
fc2 = "BuiltUp"

# Additional Quality Rules
[[rules]]
fc1 = "RoadCenterline"
rule = "MUST_NOT_HAVE_DANGLES"

[[rules]]
fc1 = "Powerline"
rule = "MUST_NOT_HAVE_DANGLES"
```

### Supported Rule Types

**Single-Layer Rules:**
- `MUST_NOT_OVERLAP`: Features cannot overlap within the same feature class
- `MUST_NOT_HAVE_GAPS`: No gaps between features (polygon only)
- `MUST_NOT_HAVE_DANGLES`: Lines must not have dangling endpoints
- `MUST_BE_SINGLE_PART`: Lines must be single part (no multipart features)

**Cross-Layer Rules (require fc2):**
- `MUST_NOT_OVERLAP_WITH`: Features in fc1 must not overlap with features in fc2
- `MUST_BE_COVERED_BY`: Features must be covered by another feature class
- `MUST_BE_INSIDE`: Features must be inside another feature class
- `MUST_NOT_INTERSECT`: Features cannot intersect

### Mandatory Topology Rules

The system includes mandatory topology rules that must be present for data quality validation:

**RoadCarriageway Rules:**
- RoadCarriageway → MUST_NOT_OVERLAP (single layer)
- RoadCarriageway → MUST_NOT_OVERLAP_WITH RoadDivider (cross-layer)
- RoadCarriageway → MUST_NOT_OVERLAP_WITH RoadIsland (cross-layer)
- RoadCarriageway → MUST_NOT_OVERLAP_WITH RoadMedian (cross-layer)
- RoadCarriageway → MUST_NOT_OVERLAP_WITH RoadRotary (cross-layer)

**Woodland Rules:**
- Woodland → MUST_NOT_OVERLAP (single layer)
- Woodland → MUST_NOT_OVERLAP_WITH Cultivation (cross-layer)
- Woodland → MUST_NOT_OVERLAP_WITH Plantation (cross-layer)
- Woodland → MUST_NOT_OVERLAP_WITH BuiltUp (cross-layer)

**BuildingFootprint Rules:**
- BuildingFootprint → MUST_NOT_OVERLAP (single layer)
- BuildingFootprint → MUST_NOT_OVERLAP_WITH BuiltUp (cross-layer)
- BuildingFootprint → MUST_NOT_OVERLAP_WITH Cultivation (cross-layer)
- BuildingFootprint → MUST_NOT_OVERLAP_WITH Plantation (cross-layer)
- BuildingFootprint → MUST_NOT_OVERLAP_WITH RoadCarriageway (cross-layer)

These rules ensure logical spatial relationships between related feature classes and maintain data quality standards.

## Project Structure

```
topology_arcpy/
├── main.py              # Main entry point
├── topology.config.toml # Configuration file
├── scripts/             # Utility and testing scripts
│   ├── check_fcs.py          # Feature class comparison utility
│   ├── test_copy_fcs.py      # Feature class copy testing
│   ├── test_fresh_flatten.py # Fresh flatten operation testing
│   └── list_datasets.py      # Dataset listing utility
├── src/                 # Source modules
│   ├── cli.py          # CLI argument parsing
│   ├── config.py       # Configuration management
│   ├── gdbops.py       # GDB operations
│   ├── topology.py     # Topology management
│   ├── dedupe.py       # Duplicate removal
│   ├── utils.py        # Common utilities
│   └── logger.py       # Logging setup
└── env.bat            # Environment setup
```

## Examples

### Complete Workflow (Recommended Order)

```bash
# Step 1: Flatten GDB structure
C:\Python27\ArcGIS10.8\python.exe main.py flatten --gdb D:\GDBs\C44B13F20.gdb

# Step 2: Remove duplicates from flattened GDB
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20_flattened.gdb --dataset TKMDS

# Step 3: Create and validate topology on cleaned data
C:\Python27\ArcGIS10.8\python.exe main.py validate --gdb D:\GDBs\C44B13F20_flattened.gdb

# Step 4: Restore original structure with cleaned, validated data
C:\Python27\ArcGIS10.8\python.exe main.py restore --gdb D:\GDBs\C44B13F20_flattened.gdb
```

### Individual Commands

#### Flatten a Geodatabase

```bash
C:\Python27\ArcGIS10.8\python.exe main.py flatten --gdb D:\GDBs\C44B13F20.gdb
```

This creates `C44B13F20_flattened.gdb` with all 165 feature classes in the "TKMDS" dataset.

#### Remove Duplicate Features

```bash
# Remove duplicates from all feature classes in TKMDS dataset
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20_flattened.gdb --dataset TKMDS

# Remove duplicates from a specific feature class
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20_flattened.gdb --feature-class BuildingFootprint

# Report duplicates without removing them (safe preview)
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20_flattened.gdb --feature-class Tower --report-only

# Remove duplicates based on attribute fields instead of geometry
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20_flattened.gdb --feature-class Canal --fields "NAME,TYPE"
```

#### Validate Topology

```bash
C:\Python27\ArcGIS10.8\python.exe main.py validate --gdb D:\GDBs\C44B13F20_flattened.gdb
```

This creates topology rules from the configuration and validates them against the cleaned data.

#### Restore Original Structure

```bash
C:\Python27\ArcGIS10.8\python.exe main.py restore --gdb D:\GDBs\C44B13F20_flattened.gdb
```

This restores the original geodatabase structure with the cleaned and validated data.

# Remove duplicates based on specific attribute fields
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20.gdb --feature-class Parcels --fields "PARCEL_ID,OWNER"
```

By default, the dedupe command identifies duplicates based on geometry (identical shapes). You can specify attribute fields to check for duplicates instead.

## Error Handling

The system includes comprehensive error handling for:

- Missing or invalid geodatabases
- Missing feature classes
- Insufficient ArcGIS licenses
- Invalid configuration files
- Workspace locks and concurrent access issues

## License

Apache License 2.0