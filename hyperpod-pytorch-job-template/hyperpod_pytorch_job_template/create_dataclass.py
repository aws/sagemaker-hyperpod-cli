#!/usr/bin/env python3
"""
Convert Kubernetes CRD OpenAPI v3 Schema to Python Dataclasses
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
import re


class CRDToPydanticConverter:
    def __init__(self):
        self.generated_classes: Set[str] = set()
        self.imports = {
            'from pydantic import BaseModel, ConfigDict, Field',
            'from typing import Optional, List, Dict, Union'
        }

    def sanitize_class_name(self, name: str) -> str:
        """Convert a schema property name to a valid Python class name in PascalCase."""
        # Handle camelCase by inserting underscores before uppercase letters
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)

        # Replace hyphens and other non-alphanumeric characters with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Split by underscores and capitalize each word
        words = [word for word in name.split('_') if word]
        name = ''.join(word.capitalize() for word in words)

        # Ensure it starts with a letter
        if name and name[0].isdigit():
            name = f"Class{name}"

        return name or "UnknownClass"

    def sanitize_field_name(self, name: str) -> str:
        """Convert a schema property name to a valid Python field name in snake_case."""
        # Convert camelCase to snake_case
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)

        # Replace hyphens and other chars with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Convert to lowercase
        name = name.lower()

        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip('_')

        # Handle Python keywords
        if name in ['class', 'def', 'for', 'if', 'else', 'while', 'try', 'except', 'import', 'from', 'as', 'pass',
                    'break', 'continue', 'return']:
            name = f"{name}_"

        return name

    def get_python_type(self, schema: Dict[str, Any], property_name: str = "") -> str:
        """Convert OpenAPI type to Python type annotation."""
        if 'type' not in schema:
            # Handle anyOf, oneOf, allOf
            if 'anyOf' in schema:
                types = [self.get_python_type(s, property_name) for s in schema['anyOf']]
                return f"Union[{', '.join(set(types))}]"
            elif 'oneOf' in schema:
                types = [self.get_python_type(s, property_name) for s in schema['oneOf']]
                return f"Union[{', '.join(set(types))}]"
            elif 'allOf' in schema:
                # For allOf, we'll treat it as the first type (simplified)
                return self.get_python_type(schema['allOf'][0], property_name) if schema['allOf'] else 'Any'
            else:
                return 'Any'

        schema_type = schema['type']

        if schema_type == 'string':
            return 'str'
        elif schema_type == 'integer':
            return 'int'
        elif schema_type == 'number':
            return 'float'
        elif schema_type == 'boolean':
            return 'bool'
        elif schema_type == 'array':
            if 'items' in schema:
                item_type = self.get_python_type(schema['items'], property_name)
                return f'List[{item_type}]'
            return 'List[Any]'
        elif schema_type == 'object':
            if 'properties' in schema:
                # Generate a new dataclass for this object
                class_name = self.sanitize_class_name(property_name or 'NestedObject')
                return class_name
            elif 'additionalProperties' in schema:
                if isinstance(schema['additionalProperties'], dict):
                    value_type = self.get_python_type(schema['additionalProperties'])
                    return f'Dict[str, {value_type}]'
                else:
                    return 'Dict[str, Any]'
            return 'Dict[str, Any]'
        else:
            return 'Any'

    def generate_dataclass(self, name: str, schema: Dict[str, Any], required: List[str] = None) -> str:
        """Generate a Pydantic BaseModel from an OpenAPI schema."""
        class_name = self.sanitize_class_name(name)

        if class_name in self.generated_classes:
            return ""  # Already generated

        self.generated_classes.add(class_name)
        required = required or []

        if 'properties' not in schema:
            return ""

        properties = schema['properties']
        fields = []
        nested_classes = []

        for prop_name, prop_schema in properties.items():
            field_name = self.sanitize_field_name(prop_name)
            python_type = self.get_python_type(prop_schema, prop_name)
            is_required = prop_name in required
            if class_name == "VolumeClaimTemplate" and prop_name == "spec":
                prop_name = "VolumeClaimTemplateSpec"

            # Generate nested classes if needed
            if prop_schema.get('type') == 'object' and 'properties' in prop_schema:
                nested_class = self.generate_dataclass(
                    prop_name,
                    prop_schema,
                    prop_schema.get('required', [])
                )
                if nested_class:
                    nested_classes.append(nested_class)
            elif prop_schema.get('type') == 'array' and 'items' in prop_schema:
                items_schema = prop_schema['items']
                if items_schema.get('type') == 'object' and 'properties' in items_schema:
                    nested_class = self.generate_dataclass(
                        prop_name,
                        items_schema,
                        items_schema.get('required', [])
                    )
                    if nested_class:
                        nested_classes.append(nested_class)

            # Create field definition with Field() for alias mapping
            field_config_parts = []

            # Add alias if field name differs from original property name
            if field_name != prop_name:
                field_config_parts.append(f'alias="{field_name}"')

            # Add description if available
            if 'description' in prop_schema:
                description = prop_schema['description'].replace('"', '\\"').replace('\n', ' ').strip()
                if description.startswith("DEPRECATED"):
                    continue
                field_config_parts.append(f'description="{description}"')

            # Handle default values and required fields
            if is_required:
                if 'default' in prop_schema:
                    default_val = repr(prop_schema['default'])
                    if field_config_parts:
                        field_config = ', '.join(field_config_parts)
                        fields.append(f"    {prop_name}: {python_type} = Field(default={default_val}, {field_config})")
                    else:
                        fields.append(f"    {prop_name}: {python_type} = {default_val}")
                else:
                    if field_config_parts:
                        field_config = ', '.join(field_config_parts)
                        fields.append(f"    {prop_name}: {python_type} = Field({field_config})")
                    else:
                        fields.append(f"    {prop_name}: {python_type}")
            else:
                default_val = 'None'
                if 'default' in prop_schema:
                    default_val = repr(prop_schema['default'])

                if field_config_parts:
                    field_config = ', '.join(field_config_parts)
                    fields.append(
                        f"    {prop_name}: Optional[{python_type}] = Field(default={default_val}, {field_config})")
                else:
                    fields.append(f"    {prop_name}: Optional[{python_type}] = {default_val}")

        # Generate the Pydantic model
        model_code = f"""class {class_name}(BaseModel):
"""

        if schema.get('description'):
            description = schema['description'].replace('\n', ' ').strip()
            model_code += f'    """{description}"""\n'

        # forbid extra inputs
        model_code += f"    model_config = ConfigDict(extra='forbid')\n\n"

        if fields:
            model_code += '\n'.join(fields)
        else:
            model_code += "    pass"

        # Combine nested classes with main class
        result = '\n\n'.join(nested_classes)
        if result and nested_classes:
            result += '\n\n'
        result += model_code

        return result

    def convert_crd_schema(self, crd_data: Dict[str, Any]) -> str:
        """Convert only the spec portion of a CRD schema to Python dataclasses."""
        results = []

        # Reset state
        self.generated_classes.clear()

        # Extract spec schema from CRD
        try:
            if 'spec' in crd_data and 'versions' in crd_data['spec']:
                # Handle multiple versions
                for version in crd_data['spec']['versions']:
                    if 'schema' in version and 'openAPIV3Schema' in version['schema']:
                        schema = version['schema']['openAPIV3Schema']

                        if 'properties' in schema and 'spec' in schema['properties']:
                            # Only generate classes for the spec portion
                            spec_schema = schema['properties']['spec']
                            spec_class = self.generate_dataclass(
                                f"{crd_data['spec']['names']['kind']}Spec",
                                spec_schema,
                                spec_schema.get('required', [])
                            )
                            if spec_class:
                                results.append(spec_class)

                        break  # Use first version for now
            else:
                # Handle direct schema input - assume it's already the spec portion
                if 'openAPIV3Schema' in crd_data:
                    schema = crd_data['openAPIV3Schema']
                    main_class = self.generate_dataclass(
                        "CustomResourceSpec",
                        schema,
                        schema.get('required', [])
                    )
                    if main_class:
                        results.append(main_class)
                elif 'properties' in crd_data:
                    # Direct schema properties - assume it's the spec
                    main_class = self.generate_dataclass(
                        "CustomResourceSpec",
                        crd_data,
                        crd_data.get('required', [])
                    )
                    if main_class:
                        results.append(main_class)

        except KeyError as e:
            raise ValueError(f"Invalid CRD structure: missing {e}")

        if not results:
            raise ValueError("No spec schema found in CRD data")

        # Combine imports and classes
        imports_code = '\n'.join(sorted(self.imports))
        classes_code = '\n\n'.join(results)

        return f"{imports_code}\n\n\n{classes_code}"


def create_dataclass(crd_file_name: str, python_file_name: str):
    converter = CRDToPydanticConverter()

    with open(crd_file_name, 'r') as f:
        crd_data = yaml.safe_load(f)

    # Convert to dataclasses
    dataclasses_code = converter.convert_crd_schema(crd_data)

    # Save to file
    with open(python_file_name, 'w') as f:
        f.write(dataclasses_code)

    print("Writing Complete")

if __name__ == '__main__':
    create_dataclass("v1_0/schema_1.json", "v1_0/model.py")