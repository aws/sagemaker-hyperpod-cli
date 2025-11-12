import logging
import yaml
from typing import List, Optional, ClassVar, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.common.utils import (
    handle_exception,
    verify_kubernetes_version_compatibility
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.cli.constants.space_template_constants import (
    SPACE_TEMPLATE_GROUP,
    SPACE_TEMPLATE_VERSION,
    SPACE_TEMPLATE_PLURAL,
)


class HPSpaceTemplate:
    """HyperPod Space Template on Amazon SageMaker HyperPod clusters.

    This class provides methods to create, manage, and monitor space templates
    on SageMaker HyperPod clusters orchestrated by Amazon EKS.
    """
    
    is_kubeconfig_loaded: ClassVar[bool] = False

    def __init__(self, *, file_path: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None):
        """Initialize space template with config YAML file path or dictionary data.
        
        Args:
            file_path: Path to YAML configuration file
            config_data: Dictionary containing configuration data
            
        Raises:
            ValueError: If both or neither parameters are provided
        """
        if (file_path is None) == (config_data is None):
            raise ValueError("Exactly one of 'file_path' or 'config_data' must be provided")
        
        if file_path is not None:
            # Initialize from file path
            try:
                with open(file_path, 'r') as f:
                    self.config_data = yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"File '{file_path}' not found")
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML file: {e}")
        else:
            # Initialize from dictionary data (e.g., from Kubernetes API response)
            self.config_data = config_data
        
        self.name = self.config_data.get('metadata', {}).get('name')

    @classmethod
    def get_logger(cls):
        """Get logger for the class."""
        return logging.getLogger(__name__)

    @classmethod
    def verify_kube_config(cls):
        """Verify and load Kubernetes configuration."""
        if not cls.is_kubeconfig_loaded:
            config.load_kube_config()
            cls.is_kubeconfig_loaded = True
            verify_kubernetes_version_compatibility(cls.get_logger())

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_space_template")
    def create(self) -> "HPSpaceTemplate":
        """Create the space template in the cluster.
        
        Returns:
            Updated HPSpaceTemplate instance with server response
        """
        self.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.create_cluster_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                plural=SPACE_TEMPLATE_PLURAL,
                body=self.config_data
            )
            
            self.config_data = response
            self.get_logger().info(f"Space template '{self.name}' created successfully")
                
        except ApiException as e:
            handle_exception(e, self.name, None)
        except Exception as e:
            self.get_logger().error(f"Error creating space template: {e}")
            raise

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_space_templates")
    def list(cls) -> List["HPSpaceTemplate"]:
        """List all space templates.
        
        Returns:
            List of HPSpaceTemplate instances
        """
        cls.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.list_cluster_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                plural=SPACE_TEMPLATE_PLURAL
            )
            
            templates = []
            for item in response.get("items", []):
                templates.append(cls(config_data=item))
            
            return templates
                
        except ApiException as e:
            handle_exception(e, "list", None)
        except Exception as e:
            cls.get_logger().error(f"Error listing space templates: {e}")
            raise

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_space_template")
    def get(cls, name: str) -> "HPSpaceTemplate":
        """Get a specific space template by name.
        
        Args:
            name: Name of the space template
            
        Returns:
            HPSpaceTemplate instance
        """
        cls.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.get_cluster_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                plural=SPACE_TEMPLATE_PLURAL,
                name=name
            )
            
            # Remove managedFields for cleaner output
            if 'metadata' in response:
                response['metadata'].pop('managedFields', None)
            
            return cls(config_data=response)
                
        except ApiException as e:
            handle_exception(e, name, None)
        except Exception as e:
            cls.get_logger().error(f"Error getting space template '{name}': {e}")
            raise

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "delete_space_template")
    def delete(self) -> None:
        """Delete the space template from the cluster."""
        self.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            api_instance.delete_cluster_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                plural=SPACE_TEMPLATE_PLURAL,
                name=self.name
            )
            
            self.get_logger().info(f"Space template '{self.name}' deleted successfully")
                
        except ApiException as e:
            handle_exception(e, self.name, None)
        except Exception as e:
            self.get_logger().error(f"Error deleting space template '{self.name}': {e}")
            raise

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "update_space_template")
    def update(self, file_path: str) -> "HPSpaceTemplate":
        """Update the space template from a YAML file.
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            Updated HPSpaceTemplate instance
        """
        self.verify_kube_config()
        
        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Validate that the name matches
            yaml_name = config_data.get('metadata', {}).get('name')
            if yaml_name and yaml_name != self.name:
                raise ValueError(f"Name mismatch. Template name '{self.name}' does not match YAML name '{yaml_name}'")

            # Remove immutable fields
            if 'metadata' in config_data:
                for field in ['resourceVersion', 'uid', 'creationTimestamp', 'managedFields']:
                    config_data['metadata'].pop(field, None)
            
            api_instance = client.CustomObjectsApi()
            response = api_instance.patch_cluster_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                plural=SPACE_TEMPLATE_PLURAL,
                name=self.name,
                body=config_data
            )
            
            self.config_data = response
            self.get_logger().info(f"Space template '{self.name}' updated successfully")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{file_path}' not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
        except ApiException as e:
            handle_exception(e, self.name, None)
        except Exception as e:
            self.get_logger().error(f"Error updating space template '{self.name}': {e}")
            raise

    def to_yaml(self) -> str:
        """Convert the space template to YAML format.
        
        Returns:
            YAML string representation
        """
        return yaml.dump(self.config_data, default_flow_style=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the space template to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return self.config_data
