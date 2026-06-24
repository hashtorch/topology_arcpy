import arcpy
fcs = ['BuildingFootprint', 'Waterbody', 'BuiltUp', 'RoadCenterline', 'CanalCenterline', 'Contour']
for fc in fcs:
    try:
        desc = arcpy.Describe(r'D:\GDBs\C44B13F20_flattened.gdb\TKMDS\\' + fc)
        print(fc, ':', desc.shapeType)
    except:
        print(fc, ':', 'NOT FOUND')
