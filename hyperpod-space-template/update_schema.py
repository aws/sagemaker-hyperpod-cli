#!/usr/bin/env python3
import json
from hyperpod_space_template.v1_1.model import SpaceConfig

schema = SpaceConfig.model_json_schema()
with open('hyperpod_space_template/v1_1/schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
print('✅ Schema updated!')
