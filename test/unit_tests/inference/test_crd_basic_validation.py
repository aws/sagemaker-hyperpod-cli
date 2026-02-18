"""
Simplified unit tests for CRD format validation.

This module contains essential tests to validate the basic format and structure 
of the CRD YAML files used by the inference operator, focusing on core 
Kubernetes CRD requirements.
"""

import unittest
import yaml
from pathlib import Path


class TestCRDFormat(unittest.TestCase):
    """Test class for validating essential CRD format requirements."""
    
    def setUp(self):
        """Set up test class with file paths."""
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.crd_path = self.base_path / "helm_chart" / "HyperPodHelmChart" / "charts" / "inference-operator" / "config" / "crd"
        
        self.crd_files = [
            self.crd_path / "inference.sagemaker.aws.amazon.com_inferenceendpointconfigs.yaml",
            self.crd_path / "inference.sagemaker.aws.amazon.com_jumpstartmodels.yaml",
            self.crd_path / "inference.sagemaker.aws.amazon.com_sagemakerendpointregistrations.yaml"
        ]
    
    def test_crd_files_exist_and_valid_yaml(self):
        """Test that all CRD files exist and have valid YAML syntax."""
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                # Check file exists
                self.assertTrue(file_path.exists(), f"CRD file does not exist: {file_path}")
                
                # Check for tab characters (not allowed in YAML)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content_text = f.read()
                    if '\t' in content_text:
                        self.fail(f"File {file_path.name} contains tab characters. YAML should use spaces for indentation.")
                
                # Check valid YAML
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = yaml.safe_load(f)
                        self.assertIsNotNone(content, f"YAML content is empty in {file_path.name}")
                    except yaml.YAMLError as e:
                        self.fail(f"Invalid YAML syntax in {file_path.name}: {e}")
    
    def test_required_crd_structure(self):
        """Test that all CRD files have the required Kubernetes CRD structure."""
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                # Check required top-level fields
                required_fields = ['apiVersion', 'kind', 'metadata', 'spec']
                for field in required_fields:
                    self.assertIn(field, content, f"Missing required field '{field}' in {file_path.name}")
                
                # Verify this is a CustomResourceDefinition
                self.assertEqual(content['apiVersion'], "apiextensions.k8s.io/v1",
                    f"Expected apiVersion 'apiextensions.k8s.io/v1' in {file_path.name}")
                self.assertEqual(content['kind'], "CustomResourceDefinition",
                    f"Expected kind 'CustomResourceDefinition' in {file_path.name}")
    
    def test_crd_spec_structure(self):
        """Test that CRD spec has required fields and basic structure."""
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                spec = content.get('spec', {})
                
                # Check required spec fields
                required_spec_fields = ['group', 'names', 'scope', 'versions']
                for field in required_spec_fields:
                    self.assertIn(field, spec, f"Missing required spec field '{field}' in {file_path.name}")
                
                # Validate spec.group
                self.assertEqual(spec['group'], "inference.sagemaker.aws.amazon.com",
                    f"Expected group 'inference.sagemaker.aws.amazon.com' in {file_path.name}")
                
                # Validate spec.scope
                self.assertEqual(spec['scope'], "Namespaced",
                    f"Expected scope 'Namespaced' in {file_path.name}")
    
    def test_crd_names_structure(self):
        """Test that CRD names section has required fields."""
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                names = content.get('spec', {}).get('names', {})
                
                # Check required names fields
                required_names_fields = ['kind', 'listKind', 'plural', 'singular']
                for field in required_names_fields:
                    self.assertIn(field, names, f"Missing required names field '{field}' in {file_path.name}")
                    self.assertTrue(names[field], f"Empty value for names.{field} in {file_path.name}")
    
    def test_crd_versions_structure(self):
        """Test that CRD versions are properly structured with required fields."""
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                versions = content.get('spec', {}).get('versions', [])
                
                # Validate versions is a non-empty list
                self.assertIsInstance(versions, list, f"spec.versions should be a list in {file_path.name}")
                self.assertGreater(len(versions), 0, f"spec.versions should not be empty in {file_path.name}")
                
                # Check each version has required fields
                for i, version in enumerate(versions):
                    required_version_fields = ['name', 'served', 'storage', 'schema']
                    for field in required_version_fields:
                        self.assertIn(field, version,
                            f"Missing required field '{field}' in version {i} of {file_path.name}")
                    
                    # Validate schema has openAPIV3Schema
                    schema = version.get('schema', {})
                    self.assertIn('openAPIV3Schema', schema,
                        f"Missing 'openAPIV3Schema' in version {i} schema of {file_path.name}")
                    
                    openapi_schema = schema.get('openAPIV3Schema', {})
                    self.assertIn('type', openapi_schema,
                        f"Missing 'type' in openAPIV3Schema for version {i} of {file_path.name}")
                    self.assertEqual(openapi_schema['type'], 'object',
                        f"Expected 'type: object' in openAPIV3Schema for version {i} of {file_path.name}")
    
    def test_metadata_name_format(self):
        """Test that metadata.name follows the expected CRD naming convention."""
        expected_names = {
            'inferenceendpointconfigs': 'inferenceendpointconfigs.inference.sagemaker.aws.amazon.com',
            'jumpstartmodels': 'jumpstartmodels.inference.sagemaker.aws.amazon.com', 
            'sagemakerendpointregistrations': 'sagemakerendpointregistrations.inference.sagemaker.aws.amazon.com'
        }
        
        for file_path in self.crd_files:
            with self.subTest(file=file_path.name):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                name = content.get('metadata', {}).get('name', '')
                
                # Find expected name based on filename
                expected_name = None
                for key, value in expected_names.items():
                    if key in file_path.name:
                        expected_name = value
                        break
                
                self.assertIsNotNone(expected_name, f"Could not determine expected name for {file_path.name}")
                self.assertEqual(name, expected_name,
                    f"Expected metadata.name '{expected_name}' in {file_path.name}, got '{name}'")


if __name__ == '__main__':
    unittest.main()
