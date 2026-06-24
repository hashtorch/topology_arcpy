"""
Script to create duplicate features for testing the dedupe command
"""
import arcpy
import sys
sys.path.insert(0, 'src')

# Set workspace to flattened GDB
flattened_gdb = r'D:\GDBs\C44B13F20_flattened.gdb'
arcpy.env.workspace = flattened_gdb + '\\TKMDS'

print("Creating duplicate features for testing...")

# Test with BuildingFootprint feature class (it should have some features)
fc_name = 'BuildingFootprint'
fc_path = flattened_gdb + '\\TKMDS\\' + fc_name

if arcpy.Exists(fc_path):
    # Get current feature count
    original_count = int(arcpy.GetCount_management(fc_path).getOutput(0))
    print("Original feature count in {}: {}".format(fc_name, original_count))

    if original_count > 0:
        # Read the first few features and duplicate them
        duplicated_count = 0
        with arcpy.da.SearchCursor(fc_path, ["SHAPE@", "OID@"]) as cursor:
            for i, row in enumerate(cursor):
                if i >= 3:  # Only duplicate first 3 features
                    break

                geometry = row[0]
                original_oid = row[1]

                try:
                    # Insert the duplicate
                    with arcpy.da.InsertCursor(fc_path, ["SHAPE@"]) as insert_cursor:
                        insert_cursor.insertRow([geometry])
                        duplicated_count += 1
                        print("  Duplicated feature OID {}".format(original_oid))

                except Exception as e:
                    print("  Error duplicating feature {}: {}".format(original_oid, str(e)))

        # Get new feature count
        new_count = int(arcpy.GetCount_management(fc_path).getOutput(0))
        print("Created {} duplicate features".format(duplicated_count))
        print("New feature count in {}: {}".format(fc_name, new_count))
        print("Expected duplicates to find: {}".format(duplicated_count))

    else:
        print("No features in {} to duplicate".format(fc_name))

else:
    print("Feature class {} does not exist".format(fc_name))

print("\nDuplicate creation complete!")
print("Now you can test: python main.py dedupe --gdb flattened_gdb --feature-class BuildingFootprint")
