"""Unit tests for space utils module."""

import unittest
from sagemaker.hyperpod.space.utils import camel_to_snake, get_model_fields, map_kubernetes_response_to_model
from hyperpod_space_template.v1_0.model import SpaceConfig


class TestSpaceUtils(unittest.TestCase):
    """Test cases for space utils functions."""

    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion."""
        self.assertEqual(camel_to_snake("displayName"), "display_name")
        self.assertEqual(camel_to_snake("desiredStatus"), "desired_status")
        self.assertEqual(camel_to_snake("ownershipType"), "ownership_type")
        self.assertEqual(camel_to_snake("image"), "image")
        self.assertEqual(camel_to_snake("name"), "name")

    def test_get_model_fields(self):
        """Test model fields extraction."""
        fields = get_model_fields(SpaceConfig)
        expected_fields = {
            'name', 'display_name', 'namespace', 'image', 'desired_status',
            'ownership_type', 'resources', 'storage', 'volumes', 'container_config',
            'node_selector', 'affinity', 'tolerations', 'lifecycle', 'template_ref'
        }
        self.assertTrue(expected_fields.issubset(fields))

    def test_map_kubernetes_response_to_model(self):
        """Test Kubernetes response mapping to model format."""
        k8s_data = {
            'metadata': {'name': 'test-space', 'namespace': 'default'},
            'spec': {
                'image': 'test:latest',
                'displayName': 'Test Space',
                'desiredStatus': 'Running',
                'unknownField': 'should be ignored'
            },
            'status': {
                'currentStatus': 'Running',
                'anotherUnknownField': 'also ignored'
            }
        }
        
        mapped = map_kubernetes_response_to_model(k8s_data, SpaceConfig)
        
        # Check that expected fields are mapped correctly
        self.assertEqual(mapped['name'], 'test-space')
        self.assertEqual(mapped['namespace'], 'default')
        self.assertEqual(mapped['image'], 'test:latest')
        self.assertEqual(mapped['display_name'], 'Test Space')
        self.assertEqual(mapped['desired_status'], 'Running')
        
        # Check that unknown fields are filtered out
        self.assertNotIn('unknownField', mapped)
        self.assertNotIn('anotherUnknownField', mapped)
        self.assertNotIn('currentStatus', mapped)

    def test_map_kubernetes_response_creates_valid_config(self):
        """Test that mapped data creates valid SpaceConfig."""
        k8s_data = {
            'metadata': {'name': 'valid-space', 'namespace': 'test'},
            'spec': {
                'image': 'valid:latest',
                'displayName': 'Valid Space',
                'desiredStatus': 'Running'
            }
        }
        
        mapped = map_kubernetes_response_to_model(k8s_data, SpaceConfig)
        config = SpaceConfig(**mapped)
        
        self.assertEqual(config.name, 'valid-space')
        self.assertEqual(config.display_name, 'Valid Space')
        self.assertEqual(config.namespace, 'test')
        self.assertEqual(config.image, 'valid:latest')
