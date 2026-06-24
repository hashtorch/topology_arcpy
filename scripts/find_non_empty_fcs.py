import arcpy
import sys
sys.path.insert(0, 'src')

# Check feature classes in TKMDS dataset
arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened.gdb\TKMDS'
fcs = arcpy.ListFeatureClasses()

print("Non-empty feature classes:")
non_empty_fcs = []
for fc in fcs:
    fc_path = r'D:\GDBs\C44B13F20_flattened.gdb\TKMDS\\' + fc
    count = int(arcpy.GetCount_management(fc_path).getOutput(0))
    if count > 0:
        print(fc, ':', count, 'features')
        non_empty_fcs.append((fc, count))
    else:
        print(fc, ': EMPTY')

print("\nTotal non-empty feature classes:", len(non_empty_fcs))
print("\nRecommended for topology (with features):")
for fc, count in non_empty_fcs:
    print(fc, ':', count, 'features')
