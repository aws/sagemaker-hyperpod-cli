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

    def test_process_replicas_with_only_accelerator_partitions(self, skip_validate_accelerator_partition_in_cluster):
        
        data = {
            'template': {
                'spec': {
                    'nodeSelector': {'node.kubernetes.io/instance-type': 'ml.p4d.24xlarge'},
                    'containers': [{
                        'resources': {
                            'requests': {'nvidia.com/mig-1g.5gb': '2'},
                            'limits': {'nvidia.com/mig-1g.5gb': '2'}
                        }
                    }]
                }
            }
        }

        result = HyperPodPytorchJob._process_replica_resources(data)

        # For ml.p4d.24xlarge: 96 CPU, 1152 GB memory, 8 GPUs
        # MIG ratio: (2 * 1) / (8 * 7) = 2/56 = 0.0357
        # Expected CPU: int(0.0357 * 96) = 3
        # Expected memory: int(0.0357 * 1152) = 41
        requests = result['template']['spec']['containers'][0]['resources']['requests']
        assert requests['cpu'] == '3.0'
        assert requests['memory'] == '41.0Gi'
        assert requests['nvidia.com/mig-1g.5gb'] == '2'

        logger.info("Successfully verified MIG partition CPU/memory allocation")

    def test_process_replicas_with_accelerator_partitions_and_cpu(self, skip_validate_accelerator_partition_in_cluster):
        data = {
            'template': {
                'spec': {
                    'nodeSelector': {'node.kubernetes.io/instance-type': 'ml.p4d.24xlarge'},
                    'containers': [{
                        'resources': {
                            'requests': {'cpu': '10', 'nvidia.com/mig-1g.5gb': '2'},
                            'limits': {'nvidia.com/mig-1g.5gb': '2'}
                        }
                    }]
                }
            }
        }

        result = HyperPodPytorchJob._process_replica_resources(data)

        # CPU specified as 10, memory calculated as: int((10/96) * 1152) = 120
        requests = result['template']['spec']['containers'][0]['resources']['requests']
        assert requests['cpu'] == '10.0'
        assert requests['memory'] == '120.0Gi'

        logger.info("Successfully verified MIG partition with CPU-only allocation")

    def test_process_replicas_with_accelerator_partitions_and_memory(self, skip_validate_accelerator_partition_in_cluster):
        data = {
            'template': {
                'spec': {
                    'nodeSelector': {'node.kubernetes.io/instance-type': 'ml.p4d.24xlarge'},
                    'containers': [{
                        'resources': {
                            'requests': {'memory': '100Gi', 'nvidia.com/mig-1g.5gb': '2'},
                            'limits': {'nvidia.com/mig-1g.5gb': '2'}
                        }
                    }]
                }
            }
        }

        result = HyperPodPytorchJob._process_replica_resources(data)

        # Memory specified as 100, CPU calculated as: int((100/1152) * 96) = 8
        requests = result['template']['spec']['containers'][0]['resources']['requests']
        assert requests['cpu'] == '8.0'
        assert requests['memory'] == '100.0Gi'

        logger.info("Successfully verified MIG partition with memory-only allocation")

    def test_process_replicas_accelerator_partition(self, skip_validate_accelerator_partition_in_cluster):
        data = {
            'template': {
                'spec': {
                    'nodeSelector': {'node.kubernetes.io/instance-type': 'ml.p4d.24xlarge'},
                    'containers': [{
                        'resources': {
                            'requests': {'cpu': '15', 'memory': '200Gi', 'nvidia.com/mig-1g.5gb': '2'},
                            'limits': {'nvidia.com/mig-1g.5gb': '2'}
                        }
                    }]
                }
            }
        }

        result = HyperPodPytorchJob._process_replica_resources(data)

        # Both CPU and memory specified, should use exact values
        requests = result['template']['spec']['containers'][0]['resources']['requests']
        assert requests['cpu'] == '15.0'
        assert requests['memory'] == '200.0Gi'

        logger.info("Successfully verified MIG partition with both CPU and memory specified")