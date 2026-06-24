import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config import load_config

config = load_config('topology.config.toml')
print('Rules loaded:', len(config.rules))
print('Dataset:', config.dataset_name)
print('GDB path from config:', config.gdb_path)
for r in config.rules:
    print('Rule:', r.origin_fc, r.rule_type, r.destination_fc)
