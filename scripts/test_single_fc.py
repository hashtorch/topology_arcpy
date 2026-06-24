import arcpy
import sys
sys.path.insert(0, 'src')

# Test topology rule on individual feature classes to find which ones work
arcpy.env.workspace = r'D:\GDBs\C44B13F20_flattened.gdb\TKMDS'

# Test feature classes
test_fcs = ['BuildingFootprint', 'BuiltUp', 'Cultivation', 'Plantation', 'Woodland', 'WaterCourseArea', 'WardBoundary', 'RoadCarriageway']

for fc in test_fcs:
    try:
        # Try to create test topology
        test_topology_name = "test_" + fc
        arcpy.CreateTopology_management("D:\GDBs\C44B13F20_flattened.gdb\\TKMDS", test_topology_name)

        # Add feature class
        arcpy.AddFeatureClassToTopology_management("D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + test_topology_name, "D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + fc)

        # Try to add rule
        arcpy.AddRuleToTopology_management("D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + test_topology_name, "Must Not Overlap (Area)", "D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + fc)

        print(fc, ": SUCCESS")

        # Clean up
        arcpy.Delete_management("D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + test_topology_name)

    except Exception as e:
        print(fc, ": FAILED -", str(e)[:100])

        # Clean up
        try:
            arcpy.Delete_management("D:\GDBs\C44B13F20_flattened.gdb\\TKMDS\\" + test_topology_name)
        except:
            pass
