#!/usr/bin/env python3
import json
from hyperpod_dev_space_template.v1_0.model import DevSpaceConfig

schema = DevSpaceConfig.model_json_schema()
with open('hyperpod_dev_space_template/v1_0/schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
print('✅ Schema updated!')
