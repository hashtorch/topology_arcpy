import json
import sys
sys.path.insert(0, 'src')

data = json.load(open(r'D:\GDBs\C44B13F20_flattened.gdb\_structure_metadata.json'))
print('Original structure:')
print('Datasets:', len(data['datasets']))
for ds, fcs in data['datasets'].items():
    print(' ', ds, '-', len(fcs), 'FCs')
print('Standalone FCs:', len(data['standalone_fcs']))
