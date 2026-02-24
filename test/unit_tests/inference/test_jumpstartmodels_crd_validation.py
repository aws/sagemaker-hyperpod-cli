"""
Unit tests for JumpStartModel CRD required field validation.

This module validates that all required fields are properly defined in the
JumpStartModel CRD YAML file used by the inference operator.
"""

import unittest
import yaml
from pathlib import Path


class TestJumpStartModelRequiredFields(unittest.TestCase):
    """Test class for validating required fields in JumpStartModel CRD."""

    @classmethod
    def setUpClass(cls):
        """Load the CRD file once for all tests."""
        cls.base_path = Path(__file__).parent.parent.parent.parent
        cls.crd_path = cls.base_path / "helm_chart" / "HyperPodHelmChart" / "charts" / "inference-operator" / "config" / "crd"
        cls.crd_file = cls.crd_path / "inference.sagemaker.aws.amazon.com_jumpstartmodels.yaml"

        with open(cls.crd_file, 'r', encoding='utf-8') as f:
            cls.crd_content = yaml.safe_load(f)

        # Get v1 version schema
        cls.v1_schema = None
        for version in cls.crd_content.get('spec', {}).get('versions', []):
            if version.get('name') == 'v1':
                cls.v1_schema = version.get('schema', {}).get('openAPIV3Schema', {})
                break

    def test_crd_file_exists(self):
        """Test that the JumpStartModel CRD file exists."""
        self.assertTrue(self.crd_file.exists(), f"CRD file does not exist: {self.crd_file}")

    def test_v1_version_exists(self):
        """Test that v1 version schema exists in the CRD."""
        self.assertIsNotNone(self.v1_schema, "v1 version schema not found in CRD")

    def test_spec_required_fields(self):
        """Test that spec has the required top-level fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {})
        required_fields = spec_properties.get('required', [])

        expected_required = ['model', 'server']
        for field in expected_required:
            self.assertIn(field, required_fields,
                         f"Field '{field}' should be required in spec")

    def test_model_section_exists(self):
        """Test that model section exists in spec."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        self.assertIn('model', spec_properties, "model section should exist in spec")

    def test_model_required_fields(self):
        """Test that model section has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model = spec_properties.get('model', {})

        required_fields = model.get('required', [])
        expected_required = ['acceptEula', 'modelId']
        for field in expected_required:
            self.assertIn(field, required_fields,
                         f"Field '{field}' should be required in model")

    def test_model_accept_eula_field(self):
        """Test that model.acceptEula field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('acceptEula', model_props, "acceptEula should exist in model")
        accept_eula = model_props.get('acceptEula', {})
        self.assertEqual(accept_eula.get('type'), 'boolean', "acceptEula should be of type boolean")
        self.assertIn('default', accept_eula, "acceptEula should have a default value")
        self.assertEqual(accept_eula.get('default'), False, "acceptEula default should be false")

    def test_model_model_id_field(self):
        """Test that model.modelId field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('modelId', model_props, "modelId should exist in model")
        model_id = model_props.get('modelId', {})
        self.assertEqual(model_id.get('type'), 'string', "modelId should be of type string")
        self.assertIn('pattern', model_id, "modelId should have a pattern validation")
        self.assertIn('maxLength', model_id, "modelId should have a maxLength validation")

    def test_model_model_version_field(self):
        """Test that model.modelVersion field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('modelVersion', model_props, "modelVersion should exist in model")
        model_version = model_props.get('modelVersion', {})
        self.assertEqual(model_version.get('type'), 'string', "modelVersion should be of type string")
        self.assertIn('pattern', model_version, "modelVersion should have a pattern validation")
        self.assertIn('minLength', model_version, "modelVersion should have a minLength validation")
        self.assertIn('maxLength', model_version, "modelVersion should have a maxLength validation")

    def test_model_model_hub_name_field(self):
        """Test that model.modelHubName field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('modelHubName', model_props, "modelHubName should exist in model")
        model_hub_name = model_props.get('modelHubName', {})
        self.assertEqual(model_hub_name.get('type'), 'string', "modelHubName should be of type string")
        self.assertIn('default', model_hub_name, "modelHubName should have a default value")
        self.assertEqual(model_hub_name.get('default'), 'SageMakerPublicHub',
                        "modelHubName default should be 'SageMakerPublicHub'")

    def test_model_gated_model_download_role_field(self):
        """Test that model.gatedModelDownloadRole field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('gatedModelDownloadRole', model_props,
                     "gatedModelDownloadRole should exist in model")
        gated_role = model_props.get('gatedModelDownloadRole', {})
        self.assertEqual(gated_role.get('type'), 'string',
                        "gatedModelDownloadRole should be of type string")
        self.assertIn('pattern', gated_role, "gatedModelDownloadRole should have a pattern validation")
        self.assertIn('minLength', gated_role, "gatedModelDownloadRole should have a minLength validation")
        self.assertIn('maxLength', gated_role, "gatedModelDownloadRole should have a maxLength validation")

    def test_model_additional_configs_field(self):
        """Test that model.additionalConfigs field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})

        self.assertIn('additionalConfigs', model_props, "additionalConfigs should exist in model")
        additional_configs = model_props.get('additionalConfigs', {})
        self.assertEqual(additional_configs.get('type'), 'array',
                        "additionalConfigs should be of type array")
        self.assertIn('maxItems', additional_configs, "additionalConfigs should have maxItems validation")

    def test_model_additional_configs_items_required_fields(self):
        """Test that additionalConfigs items have required fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        model_props = spec_properties.get('model', {}).get('properties', {})
        additional_configs_items = model_props.get('additionalConfigs', {}).get('items', {})

        required_fields = additional_configs_items.get('required', [])
        self.assertIn('name', required_fields, "name should be required in additionalConfigs items")
        self.assertIn('value', required_fields, "value should be required in additionalConfigs items")

    def test_server_section_exists(self):
        """Test that server section exists in spec."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        self.assertIn('server', spec_properties, "server section should exist in spec")

    def test_server_required_fields(self):
        """Test that server section has required fields defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        server = spec_properties.get('server', {})

        required_fields = server.get('required', [])
        self.assertIn('instanceType', required_fields,
                     "instanceType should be required in server")

    def test_server_instance_type_field(self):
        """Test that server.instanceType field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        server_props = spec_properties.get('server', {}).get('properties', {})

        self.assertIn('instanceType', server_props, "instanceType should exist in server")
        instance_type = server_props.get('instanceType', {})
        self.assertEqual(instance_type.get('type'), 'string', "instanceType should be of type string")
        self.assertIn('pattern', instance_type, "instanceType should have pattern validation")
        # Check that the pattern requires 'ml.' prefix
        pattern = instance_type.get('pattern', '')
        self.assertIn('ml', pattern.lower(), "instanceType pattern should require 'ml.' prefix")

    def test_server_execution_role_field(self):
        """Test that server.executionRole field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        server_props = spec_properties.get('server', {}).get('properties', {})

        self.assertIn('executionRole', server_props, "executionRole should exist in server")
        execution_role = server_props.get('executionRole', {})
        self.assertEqual(execution_role.get('type'), 'string',
                        "executionRole should be of type string")
        self.assertIn('pattern', execution_role, "executionRole should have pattern validation")
        self.assertIn('minLength', execution_role, "executionRole should have minLength validation")
        self.assertIn('maxLength', execution_role, "executionRole should have maxLength validation")

    def test_server_accelerator_partition_type_field(self):
        """Test that server.acceleratorPartitionType field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        server_props = spec_properties.get('server', {}).get('properties', {})

        self.assertIn('acceleratorPartitionType', server_props,
                     "acceleratorPartitionType should exist in server")
        accelerator_partition = server_props.get('acceleratorPartitionType', {})
        self.assertEqual(accelerator_partition.get('type'), 'string',
                        "acceleratorPartitionType should be of type string")
        self.assertIn('pattern', accelerator_partition,
                     "acceleratorPartitionType should have pattern validation")

    def test_server_validations_field(self):
        """Test that server.validations field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        server_props = spec_properties.get('server', {}).get('properties', {})

        self.assertIn('validations', server_props, "validations should exist in server")
        validations = server_props.get('validations', {})
        self.assertEqual(validations.get('type'), 'object', "validations should be of type object")

    def test_optional_fields_exist(self):
        """Test that optional but commonly used fields exist in spec."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})

        optional_fields = [
            'replicas',
            'autoScalingSpec',
            'loadBalancer',
            'metrics',
            'tlsConfig',
            'sageMakerEndpoint',
            'environmentVariables',
            'maxDeployTimeInSeconds',
            'kvCacheSpec',
            'intelligentRoutingSpec'
        ]

        for field in optional_fields:
            self.assertIn(field, spec_properties,
                         f"Optional field '{field}' should exist in spec")

    def test_replicas_field(self):
        """Test that replicas field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        replicas = spec_properties.get('replicas', {})

        self.assertEqual(replicas.get('type'), 'integer', "replicas should be of type integer")
        self.assertIn('default', replicas, "replicas should have a default value")
        self.assertEqual(replicas.get('default'), 1, "replicas default should be 1")

    def test_sagemaker_endpoint_fields(self):
        """Test that sageMakerEndpoint section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        sagemaker_endpoint_props = spec_properties.get('sageMakerEndpoint', {}).get('properties', {})

        self.assertIn('name', sagemaker_endpoint_props, "name should exist in sageMakerEndpoint")
        name = sagemaker_endpoint_props.get('name', {})
        self.assertEqual(name.get('type'), 'string', "name should be of type string")
        self.assertIn('pattern', name, "name should have pattern validation")
        self.assertIn('maxLength', name, "name should have maxLength validation")

    def test_environment_variables_field(self):
        """Test that environmentVariables field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        env_vars = spec_properties.get('environmentVariables', {})

        self.assertEqual(env_vars.get('type'), 'array', "environmentVariables should be of type array")
        self.assertIn('maxItems', env_vars, "environmentVariables should have maxItems validation")

    def test_environment_variables_items_required_fields(self):
        """Test that environmentVariables items have required fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        env_vars_items = spec_properties.get('environmentVariables', {}).get('items', {})

        required_fields = env_vars_items.get('required', [])
        self.assertIn('name', required_fields, "name should be required in environmentVariables items")
        self.assertIn('value', required_fields, "value should be required in environmentVariables items")

    def test_auto_scaling_spec_fields(self):
        """Test that autoScalingSpec has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        auto_scaling_spec = spec_properties.get('autoScalingSpec', {}).get('properties', {})

        expected_fields = [
            'minReplicaCount',
            'maxReplicaCount',
            'cooldownPeriod',
            'pollingInterval',
            'scaleDownStabilizationTime',
            'scaleUpStabilizationTime'
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
        self.assertIn('modelMetrics', metrics_props, "modelMetrics should exist in metrics")

    def test_load_balancer_fields(self):
        """Test that loadBalancer section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        load_balancer_props = spec_properties.get('loadBalancer', {}).get('properties', {})

        self.assertIn('healthCheckPath', load_balancer_props, "healthCheckPath should exist in loadBalancer")
        self.assertIn('routingAlgorithm', load_balancer_props, "routingAlgorithm should exist in loadBalancer")

        routing_algorithm = load_balancer_props.get('routingAlgorithm', {})
        self.assertIn('enum', routing_algorithm, "routingAlgorithm should have enum values")
        self.assertIn('least_outstanding_requests', routing_algorithm.get('enum', []),
                     "routingAlgorithm should support 'least_outstanding_requests'")
        self.assertIn('round_robin', routing_algorithm.get('enum', []),
                     "routingAlgorithm should support 'round_robin'")

    def test_tls_config_fields(self):
        """Test that tlsConfig section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        tls_config_props = spec_properties.get('tlsConfig', {}).get('properties', {})

        self.assertIn('tlsCertificateOutputS3Uri', tls_config_props,
                     "tlsCertificateOutputS3Uri should exist in tlsConfig")
        tls_uri = tls_config_props.get('tlsCertificateOutputS3Uri', {})
        self.assertIn('pattern', tls_uri, "tlsCertificateOutputS3Uri should have pattern validation")

    def test_kv_cache_spec_fields(self):
        """Test that kvCacheSpec section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        kv_cache_props = spec_properties.get('kvCacheSpec', {}).get('properties', {})

        self.assertIn('enableL1Cache', kv_cache_props, "enableL1Cache should exist in kvCacheSpec")
        self.assertIn('enableL2Cache', kv_cache_props, "enableL2Cache should exist in kvCacheSpec")
        self.assertIn('l2CacheSpec', kv_cache_props, "l2CacheSpec should exist in kvCacheSpec")

    def test_intelligent_routing_spec_fields(self):
        """Test that intelligentRoutingSpec section has expected fields."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        intelligent_routing_props = spec_properties.get('intelligentRoutingSpec', {}).get('properties', {})

        self.assertIn('enabled', intelligent_routing_props, "enabled should exist in intelligentRoutingSpec")
        self.assertIn('routingStrategy', intelligent_routing_props,
                     "routingStrategy should exist in intelligentRoutingSpec")

        routing_strategy = intelligent_routing_props.get('routingStrategy', {})
        self.assertIn('enum', routing_strategy, "routingStrategy should have enum values")
        expected_strategies = ['prefixaware', 'kvaware', 'session', 'roundrobin']
        for strategy in expected_strategies:
            self.assertIn(strategy, routing_strategy.get('enum', []),
                         f"routingStrategy should support '{strategy}'")

    def test_max_deploy_time_field(self):
        """Test that maxDeployTimeInSeconds field is properly defined."""
        spec_properties = self.v1_schema.get('properties', {}).get('spec', {}).get('properties', {})
        max_deploy_time = spec_properties.get('maxDeployTimeInSeconds', {})

        self.assertEqual(max_deploy_time.get('type'), 'integer',
                        "maxDeployTimeInSeconds should be of type integer")
        self.assertIn('default', max_deploy_time, "maxDeployTimeInSeconds should have a default value")
        self.assertEqual(max_deploy_time.get('default'), 3600,
                        "maxDeployTimeInSeconds default should be 3600")


if __name__ == '__main__':
    unittest.main()
