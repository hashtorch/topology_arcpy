import arcpy
import sys
sys.path.insert(0, 'src')

arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened_restored.gdb'
datasets = arcpy.ListDatasets()
print('Restored datasets:', len(datasets))
for ds in datasets:
    arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened_restored.gdb' + '\\' + ds
    fcs = arcpy.ListFeatureClasses()
    print(' ', ds, '-', len(fcs), 'feature classes')
