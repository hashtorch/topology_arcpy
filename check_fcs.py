import arcpy
import sys
sys.path.insert(0, 'src')

# Check original GDB
arcpy.env.workspace = r'D:\GDBs\C44B13F20.gdb'
datasets = arcpy.ListDatasets()
print('Original GDB datasets:', len(datasets))

fc_count = 0
fc_names = []
for ds in datasets:
    arcpy.env.workspace = r'D:\GDBs\C44B13F20.gdb' + '\\' + ds
    fcs = arcpy.ListFeatureClasses()
    fc_count += len(fcs)
    print('  {} has {} feature classes'.format(ds, len(fcs)))
    for fc in fcs:
        fc_names.append(ds + '\\' + fc)

print('Total original feature classes:', fc_count)
print('Original feature class names:')
for name in sorted(fc_names):
    print('  ', name)

# Check flattened GDB
print('\n--- Flattened GDB ---')
arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened.gdb'
datasets_flat = arcpy.ListDatasets()
print('Flattened GDB datasets:', len(datasets_flat))

fc_count_flat = 0
fc_names_flat = []
for ds in datasets_flat:
    arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened.gdb' + '\\' + ds
    fcs = arcpy.ListFeatureClasses()
    fc_count_flat += len(fcs)
    print('  {} has {} feature classes'.format(ds, len(fcs)))
    for fc in fcs:
        fc_names_flat.append(ds + '\\' + fc)

print('Total flattened feature classes:', fc_count_flat)
print('Flattened feature class names:')
for name in sorted(fc_names_flat):
    print('  ', name)

# Compare
print('\n--- Comparison ---')
print('Original count:', fc_count)
print('Flattened count:', fc_count_flat)
print('Match:', fc_count == fc_count_flat)

missing = set(fc_names) - set(fc_names_flat)
extra = set(fc_names_flat) - set(fc_names)

if missing:
    print('Missing in flattened:', missing)
if extra:
    print('Extra in flattened:', extra)
