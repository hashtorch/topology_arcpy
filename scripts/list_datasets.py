import arcpy
arcpy.env.workspace = r'D:\GDBs\C44B13F20.gdb'
datasets = arcpy.ListDatasets()
print('Available datasets:')
for ds in datasets:
    print(' ', ds)