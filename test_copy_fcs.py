import arcpy
import os
import sys

# Test which feature classes can be copied
input_gdb = r'D:\GDBs\C44B13F20.gdb'
output_gdb = r'D:\GDBs\C44B13F20_flattened.gdb'
dataset_name = 'Infrastructure'

arcpy.env.workspace = input_gdb
datasets = arcpy.ListDatasets()

# Create target dataset
if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Get spatial reference from first FC
first_fc = None
for ds in datasets:
    arcpy.env.workspace = os.path.join(input_gdb, ds)
    fcs = arcpy.ListFeatureClasses()
    if fcs and not first_fc:
        first_fc = os.path.join(input_gdb, ds, fcs[0])
        break

if first_fc:
    spatial_ref = arcpy.Describe(first_fc).spatialReference
    print('Using spatial reference:', spatial_ref.name)

    # Create target dataset
    target_dataset = os.path.join(output_gdb, dataset_name)
    if not arcpy.Exists(target_dataset):
        arcpy.CreateFeatureDataset_management(output_gdb, dataset_name, spatial_ref)

    # Try to copy each feature class
    success_count = 0
    fail_count = 0
    failed_fcs = []

    for ds in datasets:
        arcpy.env.workspace = os.path.join(input_gdb, ds)
        fcs = arcpy.ListFeatureClasses()

        for fc in fcs:
            fc_path = os.path.join(input_gdb, ds, fc)
            target_fc = os.path.join(target_dataset, fc)

            try:
                print('Copying:', ds + '\\' + fc)
                arcpy.FeatureClassToFeatureClass_conversion(fc_path, target_dataset, fc)
                print('  Success!')
                success_count += 1
            except Exception as e:
                print('  FAILED:', str(e))
                fail_count += 1
                failed_fcs.append(ds + '\\' + fc)

    print('\n=== Results ===')
    print('Successful:', success_count)
    print('Failed:', fail_count)
    if failed_fcs:
        print('\nFailed feature classes:')
        for fc in failed_fcs:
            print(' ', fc)
