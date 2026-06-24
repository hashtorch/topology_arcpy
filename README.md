# Topology Management System

A command-line tool for managing ArcGIS Desktop geodatabase topology operations using Python 2.7 and ArcPy.

## Features

- **Flatten**: Consolidate all feature classes from multiple datasets into a single dataset
- **Restore**: Restore original geodatabase structure from a flattened GDB
- **Validate**: Create and validate topology rules from configuration files
- **Dedupe**: Remove duplicate features from geodatabases

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
# Flatten GDB structure
python main.py flatten --gdb input.gdb --output input_flattened.gdb

# Restore original structure
python main.py restore --gdb input_flattened.gdb

# Create and validate topology
python main.py validate --gdb input.gdb --config topology.config.toml

# Remove duplicate features
python main.py dedupe --gdb input.gdb --dataset Infrastructure
python main.py dedupe --gdb input.gdb --feature-class Parcels --report-only
```

### Command Options

- `--gdb PATH`: Input geodatabase path
- `--output PATH`: Output geodatabase path (for flatten command)
- `--dataset NAME`: Dataset name (default: Infrastructure)
- `--config PATH`: Configuration file path (default: topology.config.toml)
- `--feature-class`: Specific feature class to process (for dedupe command)
- `--fields`: Comma-separated list of fields to check for duplicates (for dedupe command)
- `--report-only`: Report duplicates without removing them (for dedupe command)
- `--verbose`: Enable verbose logging

## Configuration

The system uses TOML configuration files to define topology rules:

```toml
gdb_path = "D:/GDBs/C44B13F20.gdb"
dataset_name = "Infrastructure"
topology_name = "Landuse_Topology"

[[rules]]
origin_fc = "Parcels"
rule_type = "MUST_NOT_OVERLAP"

[[rules]]
origin_fc = "Parcels"
rule_type = "MUST_NOT_HAVE_GAPS"

[[rules]]
origin_fc = "Buildings"
rule_type = "MUST_BE_INSIDE"
destination_fc = "Parcels"
```

### Supported Rule Types

- `MUST_NOT_OVERLAP`: Features cannot overlap
- `MUST_NOT_HAVE_GAPS`: No gaps between features
- `MUST_BE_INSIDE`: Features must be inside another feature class
- `MUST_BE_COVERED_BY`: Features must be covered by another feature class
- `MUST_NOT_INTERSECT`: Features cannot intersect

## Project Structure

```
topology_arcpy/
├── main.py              # Main entry point
├── topology.config.toml # Configuration file
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

### Flatten a Geodatabase

```bash
C:\Python27\ArcGIS10.8\python.exe main.py flatten --gdb D:\GDBs\C44B13F20.gdb
```

This creates `C44B13F20_flattened.gdb` with all feature classes in the "Infrastructure" dataset.

### Restore Original Structure

```bash
C:\Python27\ArcGIS10.8\python.exe main.py restore --gdb D:\GDBs\C44B13F20_flattened.gdb
```

This restores the original geodatabase structure.

### Validate Topology

```bash
C:\Python27\ArcGIS10.8\python.exe main.py validate --gdb D:\GDBs\C44B13F20.gdb
```

This creates topology rules from the configuration and validates them.

### Remove Duplicate Features

```bash
# Remove duplicates from all feature classes in a dataset
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20.gdb --dataset Infrastructure

# Remove duplicates from a specific feature class
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20.gdb --feature-class Parcels

# Report duplicates without removing them
C:\Python27\ArcGIS10.8\python.exe main.py dedupe --gdb D:\GDBs\C44B13F20.gdb --feature-class Parcels --report-only

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