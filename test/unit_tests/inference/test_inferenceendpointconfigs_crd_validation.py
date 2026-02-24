"""
Unit tests for InferenceEndpointConfig CRD required field validation.

This module validates that all required fields are properly defined in the
InferenceEndpointConfig CRD YAML file used by the inference operator.
"""

import unittest
import yaml
from pathlib import Path


class TestInferenceEndpointConfigRequiredFields(unittest.TestCase):
    """Test class for validating required fields in InferenceEndpointConfig CRD."""

    @classmethod
    def setUpClass(cls):
        """Load the CRD file once for all tests."""
        cls.base_path = Path(__file__).parent.parent.parent.parent
        cls.crd_path = cls.base_path / "helm_chart" / "HyperPodHelmChart" / "charts" / "inference-operator" / "config" / "crd"
        cls.crd_file = cls.crd_path / "inference.sagemaker.aws.amazon.com_inferenceendpointconfigs.yaml"

        with open(cls.crd_file, 'r', encoding='utf-8') as f:
            cls.crd_content = yaml.safe_load(f)

        # Get v1 version schema
        cls.v1_schema = None
        for version in cls.crd_content.get('spec', {}).get('versions', []):
            if version.get('name') == 'v1':
                cls.v1_schema = version.get('schema', {}).get('openAPIV3Schema', {})
                break

    def test_crd_file_exists(self):
        """Test that the InferenceEndpointConfig CRD file exists."""
        self.assertTrue(self.crd_file.exists(), f"CRD file does not exist: {self.crd_file}")

    def test_v1_version_exists(self):
        """Test that v1 version schema exists in the CRD."""
        self.assertIsNotNone(self.v1_schema, "v1 version schema not found in CRD")

    def test_spec_required_fields(self):
        """Test that spec has the required top-level fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {})
        required_fields = spec_properties.get('required', [])

        expected_required = ['modelName', 'modelSourceConfig', 'worker']
        for field in expected_required:
            self.assertIn(field, required_fields,
                         f"Field '{field}' should be required in spec")

    def test_modelname_field_exists(self):
        """Test that modelName field is defined in spec."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        self.assertIn('modelName', spec_properties, "modelName field should exist in spec")

        model_name = spec_properties.get('modelName', {})
        self.assertEqual(model_name.get('type'), 'string', "modelName should be of type string")
        self.assertIn('pattern', model_name, "modelName should have a pattern validation")
        self.assertIn('maxLength', model_name, "modelName should have a maxLength validation")

    def test_model_source_config_required_fields(self):
        """Test that modelSourceConfig has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config = spec_properties.get('modelSourceConfig', {})

        required_fields = model_source_config.get('required', [])
        self.assertIn('modelSourceType', required_fields,
                     "modelSourceType should be required in modelSourceConfig")

    def test_model_source_config_model_source_type_field(self):
        """Test that modelSourceType field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config_props = spec_properties.get('modelSourceConfig', {}).get('properties', {})

        self.assertIn('modelSourceType', model_source_config_props,
                     "modelSourceType should exist in modelSourceConfig")

        model_source_type = model_source_config_props.get('modelSourceType', {})
        self.assertIn('enum', model_source_type, "modelSourceType should have enum values")
        self.assertIn('fsx', model_source_type.get('enum', []), "modelSourceType should support 'fsx'")
        self.assertIn('s3', model_source_type.get('enum', []), "modelSourceType should support 's3'")

    def test_model_source_config_fsx_storage_required_fields(self):
        """Test that fsxStorage has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config_props = spec_properties.get('modelSourceConfig', {}).get('properties', {})
        fsx_storage = model_source_config_props.get('fsxStorage', {})

        required_fields = fsx_storage.get('required', [])
        self.assertIn('fileSystemId', required_fields,
                     "fileSystemId should be required in fsxStorage")

    def test_model_source_config_fsx_storage_fields(self):
        """Test that fsxStorage fields are properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config_props = spec_properties.get('modelSourceConfig', {}).get('properties', {})
        fsx_storage_props = model_source_config_props.get('fsxStorage', {}).get('properties', {})

        self.assertIn('fileSystemId', fsx_storage_props, "fileSystemId should exist in fsxStorage")
        self.assertIn('dnsName', fsx_storage_props, "dnsName should exist in fsxStorage")
        self.assertIn('mountName', fsx_storage_props, "mountName should exist in fsxStorage")

    def test_model_source_config_s3_storage_required_fields(self):
        """Test that s3Storage has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config_props = spec_properties.get('modelSourceConfig', {}).get('properties', {})
        s3_storage = model_source_config_props.get('s3Storage', {})

        required_fields = s3_storage.get('required', [])
        self.assertIn('bucketName', required_fields,
                     "bucketName should be required in s3Storage")
        self.assertIn('region', required_fields,
                     "region should be required in s3Storage")

    def test_model_source_config_s3_storage_fields(self):
        """Test that s3Storage fields are properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_source_config_props = spec_properties.get('modelSourceConfig', {}).get('properties', {})
        s3_storage_props = model_source_config_props.get('s3Storage', {}).get('properties', {})

        self.assertIn('bucketName', s3_storage_props, "bucketName should exist in s3Storage")
        self.assertIn('region', s3_storage_props, "region should exist in s3Storage")

    def test_worker_required_fields(self):
        """Test that worker section has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker = spec_properties.get('worker', {})

        required_fields = worker.get('required', [])
        expected_required = ['image', 'modelInvocationPort', 'modelVolumeMount', 'resources']
        for field in expected_required:
            self.assertIn(field, required_fields,
                         f"Field '{field}' should be required in worker")

    def test_worker_image_field(self):
        """Test that worker.image field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})

        self.assertIn('image', worker_props, "image should exist in worker")
        image = worker_props.get('image', {})
        self.assertEqual(image.get('type'), 'string', "image should be of type string")

    def test_worker_model_invocation_port_required_fields(self):
        """Test that modelInvocationPort has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})
        model_invocation_port = worker_props.get('modelInvocationPort', {})

        required_fields = model_invocation_port.get('required', [])
        self.assertIn('containerPort', required_fields,
                     "containerPort should be required in modelInvocationPort")

    def test_worker_model_invocation_port_fields(self):
        """Test that modelInvocationPort fields are properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})
        port_props = worker_props.get('modelInvocationPort', {}).get('properties', {})

        self.assertIn('containerPort', port_props, "containerPort should exist in modelInvocationPort")
        container_port = port_props.get('containerPort', {})
        self.assertEqual(container_port.get('type'), 'integer', "containerPort should be of type integer")
        self.assertIn('minimum', container_port, "containerPort should have minimum validation")
        self.assertIn('maximum', container_port, "containerPort should have maximum validation")

        self.assertIn('name', port_props, "name should exist in modelInvocationPort")
        name = port_props.get('name', {})
        self.assertIn('pattern', name, "name should have pattern validation")

    def test_worker_model_volume_mount_required_fields(self):
        """Test that modelVolumeMount has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})
        model_volume_mount = worker_props.get('modelVolumeMount', {})

        required_fields = model_volume_mount.get('required', [])
        self.assertIn('name', required_fields,
                     "name should be required in modelVolumeMount")

    def test_worker_model_volume_mount_fields(self):
        """Test that modelVolumeMount fields are properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})
        volume_mount_props = worker_props.get('modelVolumeMount', {}).get('properties', {})

        self.assertIn('name', volume_mount_props, "name should exist in modelVolumeMount")
        self.assertIn('mountPath', volume_mount_props, "mountPath should exist in modelVolumeMount")

    def test_worker_resources_field(self):
        """Test that worker.resources field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})

        self.assertIn('resources', worker_props, "resources should exist in worker")
        resources = worker_props.get('resources', {})
        self.assertEqual(resources.get('type'), 'object', "resources should be of type object")

    def test_worker_resources_fields(self):
        """Test that resources has expected sub-fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        worker_props = spec_properties.get('worker', {}).get('properties', {})
        resources_props = worker_props.get('resources', {}).get('properties', {})

        self.assertIn('limits', resources_props, "limits should exist in resources")
        self.assertIn('requests', resources_props, "requests should exist in resources")

    def test_optional_fields_exist(self):
        """Test that optional but commonly used fields exist in spec."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})

        optional_fields = [
            'endpointName',
            'instanceType',
            'instanceTypes',
            'replicas',
            'autoScalingSpec',
            'loadBalancer',
            'metrics',
            'tlsConfig',
            'tags'
        ]

        for field in optional_fields:
            self.assertIn(field, spec_properties,
                         f"Optional field '{field}' should exist in spec")

    def test_endpoint_name_validation(self):
        """Test that endpointName has proper validation."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        endpoint_name = spec_properties.get('endpointName', {})

        self.assertIn('pattern', endpoint_name, "endpointName should have pattern validation")
        self.assertIn('maxLength', endpoint_name, "endpointName should have maxLength validation")

    def test_instance_type_validation(self):
        """Test that instanceType has proper validation."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        instance_type = spec_properties.get('instanceType', {})

        self.assertEqual(instance_type.get('type'), 'string', "instanceType should be of type string")
        self.assertIn('pattern', instance_type, "instanceType should have pattern validation")
        # Check that the pattern requires 'ml.' prefix
        pattern = instance_type.get('pattern', '')
        self.assertIn('ml', pattern.lower(), "instanceType pattern should require 'ml.' prefix")

    def test_replicas_field(self):
        """Test that replicas field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        replicas = spec_properties.get('replicas', {})

        self.assertEqual(replicas.get('type'), 'integer', "replicas should be of type integer")
        self.assertIn('default', replicas, "replicas should have a default value")

    def test_auto_scaling_spec_fields(self):
        """Test that autoScalingSpec has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        auto_scaling_spec = spec_properties.get('autoScalingSpec', {}).get('properties', {})

        expected_fields = [
            'minReplicaCount',
            'maxReplicaCount',
            'cooldownPeriod',
            'pollingInterval'
        ]

        for field in expected_fields:
            self.assertIn(field, auto_scaling_spec,
                         f"Field '{field}' should exist in autoScalingSpec")

    def test_metrics_fields(self):
        """Test that metrics section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        metrics_props = spec_properties.get('metrics', {}).get('properties', {})

        self.assertIn('enabled', metrics_props, "enabled should exist in metrics")
        self.assertIn('metricsScrapeIntervalSeconds', metrics_props,
                     "metricsScrapeIntervalSeconds should exist in metrics")

    def test_load_balancer_fields(self):
        """Test that loadBalancer section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        load_balancer_props = spec_properties.get('loadBalancer', {}).get('properties', {})

        self.assertIn('healthCheckPath', load_balancer_props, "healthCheckPath should exist in loadBalancer")
        self.assertIn('routingAlgorithm', load_balancer_props, "routingAlgorithm should exist in loadBalancer")


if __name__ == '__main__':
    unittest.main()
