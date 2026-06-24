import arcpy
import os

# Delete flattened GDB if exists
flattened_gdb = r'D:\GDBs\C44B13F20_flattened.gdb'
if arcpy.Exists(flattened_gdb):
    print('Deleting existing flattened GDB...')
    arcpy.Delete_management(flattened_gdb)
    print('Deleted!')

# Now test flatten with our system
print('Testing flatten operation...')
import sys
sys.path.insert(0, 'src')
from src.gdbops import flatten_gdb

try:
    structure = flatten_gdb(r'D:\GDBs\C44B13F20.gdb', flattened_gdb, 'Infrastructure')
    print('Flatten completed successfully!')
    print('Structure preserved with {} datasets'.format(len(structure.datasets)))
except Exception as e:
    print('Flatten failed:', str(e))
    import traceback
    traceback.print_exc()
