# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import pytest
from sagemaker.hyperpod.training import HyperPodPytorchJob
from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)


class TestHyperPodSDKResourceProcessing:
    """Integration tests for HyperPod SDK resource processing methods."""

    def test_process_replica_resources_valid_config(self):
        """Test _process_replica_resources with valid configuration."""
        data = {
            'name': 'pod',
            'template': {
                'spec': {
                    'containers': [{
                        'name': 'container-name',
                        'image': 'pytorch:latest',
                        'resources': {
                            'requests': {
                                'nvidia.com/gpu': '1',
                                'cpu': '3',
                                'memory': '1'
                            },
                            'limits': {
                                'nvidia.com/gpu': '1',
                                'cpu': '4',
                                'memory': '2'
                            }
                        }
                    }],
                    'nodeSelector': {
                        'node.kubernetes.io/instance-type': 'ml.g5.8xlarge'
                    }
                }
            }
        }

        # Process the resources
        processed_data = HyperPodPytorchJob._process_replica_resources(data)
        
        # Verify the data was processed
        assert processed_data is not None
        assert 'template' in processed_data
        assert 'spec' in processed_data['template']
        assert 'containers' in processed_data['template']['spec']
        assert len(processed_data['template']['spec']['containers']) > 0
        
        container = processed_data['template']['spec']['containers'][0]
        assert 'resources' in container
        assert 'requests' in container['resources']
        assert 'limits' in container['resources']
        
        logger.info("Successfully processed replica resources with valid config")

    def test_process_replica_resources_missing_containers(self):
        """Test _process_replica_resources with missing containers."""
        data = {
            'name': 'pod',
            'replicas': 1,
            'template': {
                'spec': {
                    'containers': [],  # Empty containers
                    'nodeSelector': {
                        'node.kubernetes.io/instance-type': 'ml.g5.8xlarge'
                    }
                }
            }
        }

        # This should raise a ValueError
        with pytest.raises(ValueError, match="No containers found"):
            HyperPodPytorchJob._process_replica_resources(data)
        
        logger.info("Successfully caught missing containers error")

    def test_get_container_resources(self):
        """Test _get_container_resources method."""
        replica_spec = {
            'template': {
                'spec': {
                    'containers': [{
                        'resources': {
                            'requests': {'cpu': '2', 'memory': '4Gi'},
                            'limits': {'cpu': '4', 'memory': '8Gi'}
                        }
                    }]
                }
            }
        }

        requests, limits = HyperPodPytorchJob._get_container_resources(replica_spec)
        
        assert requests == {'cpu': '2', 'memory': '4Gi'}
        assert limits == {'cpu': '4', 'memory': '8Gi'}
        
        logger.info("Successfully extracted container resources")

    def test_process_replica_resources_with_float_values(self):
        """Test _process_replica_resources with float values."""
        data = {
            'name': 'pod',
            'template': {
                'spec': {
                    'containers': [{
                        'name': 'container-name',
                        'image': 'pytorch:latest',
                        'resources': {
                            'requests': {
                                'nvidia.com/gpu': '1',
                                'cpu': '3.6',
                                'memory': '1.5'
                            },
                            'limits': {
                                'nvidia.com/gpu': '1',
                                'cpu': '4.8',
                                'memory': '2.7'
                            }
                        }
                    }],
                    'nodeSelector': {
                        'node.kubernetes.io/instance-type': 'ml.g5.8xlarge'
                    }
                }
            }
        }

        # Process the resources
        processed_data = HyperPodPytorchJob._process_replica_resources(data)
        
        # Verify the data was processed
        assert processed_data is not None
        container = processed_data['template']['spec']['containers'][0]
        assert 'resources' in container
        
        logger.info("Successfully processed replica resources with float values")
