import arcpy
fcs = ['CompoundWall', 'BuildingFootprint', 'WaterCourseArea', 'ElectricPole', 'WirelessStationMast', 'Powerline', 'BuiltUp', 'Cultivation', 'Plantation', 'Woodland', 'WardBoundary', 'OtherLine', 'RoadCenterline', 'RoadCarriageway']
for fc in fcs:
    desc = arcpy.Describe(r'D:\GDBs\C44B13F20_flattened.gdb\TKMDS\\' + fc)
    print(fc, ':', desc.shapeType)
