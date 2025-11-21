import logging
import yaml
from typing import List, Optional, ClassVar, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_default_namespace,
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
    on SageMaker HyperPod clusters orchestrated by Amazon EKS. Space templates
    define reusable configurations for creating spaces with predefined settings,
    resources, and constraints.

    **Attributes:**

    .. list-table::
       :header-rows: 1
       :widths: 20 20 60

       * - Attribute
         - Type
         - Description
       * - config_data
         - Dict[str, Any]
         - Dictionary containing the complete template configuration
       * - name
         - str
         - Name of the space template extracted from metadata
       * - namespace
         - str
         - Kubernetes namespace of the template extracted from metadata

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: python

          >>> # Create template from YAML file
          >>> template = HPSpaceTemplate(file_path="template.yaml")
          >>> template.create()
          
          >>> # List all templates
          >>> templates = HPSpaceTemplate.list()
          >>> for template in templates:
          ...     print(f"Template: {template.name}")
    """
    
    is_kubeconfig_loaded: ClassVar[bool] = False

    def __init__(self, *, file_path: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None):
        """Initialize space template with config YAML file path or dictionary data.

        Creates a new HPSpaceTemplate instance from either a YAML configuration file
        or a dictionary containing configuration data. Exactly one of the parameters
        must be provided.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - file_path
             - str, optional
             - Path to YAML configuration file (keyword-only)
           * - config_data
             - Dict[str, Any], optional
             - Dictionary containing configuration data (keyword-only)

        **Raises:**

        ValueError: If both or neither parameters are provided, or if YAML parsing fails
        FileNotFoundError: If the specified file path does not exist

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Initialize from YAML file
              >>> template = HPSpaceTemplate(file_path="my-template.yaml")
              
              >>> # Initialize from dictionary (e.g., from API response)
              >>> config = {"metadata": {"name": "my-template"}, "spec": {...}}
              >>> template = HPSpaceTemplate(config_data=config)
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
        self.namespace = self.config_data.get('metadata', {}).get('namespace')

    @classmethod
    def get_logger(cls):
        """Get logger for the HPSpaceTemplate class.

        **Returns:**

        logging.Logger: Logger instance configured for the HPSpaceTemplate class

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> logger = HPSpaceTemplate.get_logger()
              >>> logger.info("Template operation completed")
        """
        return logging.getLogger(__name__)

    @classmethod
    def verify_kube_config(cls):
        """Verify and load Kubernetes configuration.

        Loads the Kubernetes configuration from the default kubeconfig location
        and verifies compatibility with the cluster. This method is called
        automatically by other methods that interact with the Kubernetes API.

        **Raises:**

        Exception: If the kubeconfig cannot be loaded or is invalid

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Verify kubeconfig before operations
              >>> HPSpaceTemplate.verify_kube_config()
        """
        if not cls.is_kubeconfig_loaded:
            config.load_kube_config()
            cls.is_kubeconfig_loaded = True
            verify_kubernetes_version_compatibility(cls.get_logger())

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_space_template")
    def create(self) -> "HPSpaceTemplate":
        """Create the space template in the Kubernetes cluster.

        Submits the space template configuration to the Kubernetes cluster and
        creates a new template resource. Updates the instance with the server
        response including generated metadata.

        **Returns:**

        HPSpaceTemplate: Updated HPSpaceTemplate instance with server response data

        **Raises:**

        ApiException: If the Kubernetes API call fails
        Exception: If template creation fails for other reasons

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Create template from file
              >>> template = HPSpaceTemplate(file_path="template.yaml")
              >>> created_template = template.create()
              >>> print(f"Created template: {created_template.name}")
        """
        self.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.create_namespaced_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                namespace=self.namespace,
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
    def list(cls, namespace: Optional[str] = None) -> List["HPSpaceTemplate"]:
        """List all space templates in the specified namespace.

        Retrieves all space template resources from the Kubernetes cluster in the
        specified namespace. If no namespace is provided, uses the default namespace
        from the current Kubernetes context.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - namespace
             - str, optional
             - The Kubernetes namespace to list space templates from. If None, uses the default namespace from current context

        **Returns:**

        List[HPSpaceTemplate]: List of HPSpaceTemplate instances found in the namespace

        **Raises:**

        ApiException: If the Kubernetes API call fails
        Exception: If template listing fails for other reasons

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # List templates in default namespace
              >>> templates = HPSpaceTemplate.list()
              >>> print(f"Found {len(templates)} templates")
              
              >>> # List templates in specific namespace
              >>> templates = HPSpaceTemplate.list(namespace="production")
              >>> for template in templates:
              ...     print(f"Template: {template.name}")
        """
        cls.verify_kube_config()

        if not namespace:
            namespace = get_default_namespace()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.list_namespaced_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                namespace=namespace,
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
    def get(cls, name: str, namespace: Optional[str] = None) -> "HPSpaceTemplate":
        """Get a specific space template by name.

        Retrieves a single space template resource from the Kubernetes cluster
        by name. Removes managedFields from the metadata for cleaner output.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - name
             - str
             - Name of the space template to retrieve
           * - namespace
             - str, optional
             - The Kubernetes namespace. If None, uses the default namespace from current context

        **Returns:**

        HPSpaceTemplate: The space template instance with configuration data

        **Raises:**

        ApiException: If the template is not found or Kubernetes API call fails
        Exception: If template retrieval fails for other reasons

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Get template from default namespace
              >>> template = HPSpaceTemplate.get("my-template")
              >>> print(f"Template display name: {template.config_data['spec']['displayName']}")
              
              >>> # Get template from specific namespace
              >>> template = HPSpaceTemplate.get("my-template", namespace="production")
              >>> print(template.to_yaml())
        """
        cls.verify_kube_config()

        if not namespace:
            namespace = get_default_namespace()
        
        try:
            api_instance = client.CustomObjectsApi()
            response = api_instance.get_namespaced_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                namespace=namespace,
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
        """Delete the space template from the Kubernetes cluster.

        Permanently removes the space template resource from the Kubernetes cluster.
        This operation cannot be undone. Any spaces created from this template
        will continue to exist but will no longer reference the template.

        **Raises:**

        ApiException: If the deletion fails or Kubernetes API call fails
        Exception: If template deletion fails for other reasons

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Delete a template
              >>> template = HPSpaceTemplate.get("my-template")
              >>> template.delete()
        """
        self.verify_kube_config()
        
        try:
            api_instance = client.CustomObjectsApi()
            api_instance.delete_namespaced_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                namespace=self.namespace,
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
        """Update the space template from a YAML configuration file.

        Updates the existing space template with new configuration from a YAML file.
        Validates that the template name in the file matches the current template name
        and removes immutable fields before applying the update.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - file_path
             - str
             - Path to the YAML configuration file containing updated template configuration

        **Returns:**

        HPSpaceTemplate: Updated HPSpaceTemplate instance with server response data

        **Raises:**

        FileNotFoundError: If the specified file path does not exist
        ValueError: If YAML parsing fails or template name mismatch occurs
        ApiException: If the Kubernetes API call fails
        Exception: If template update fails for other reasons

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Update template from file
              >>> template = HPSpaceTemplate.get("my-template")
              >>> updated_template = template.update("updated-template.yaml")
              >>> print(f"Updated template: {updated_template.name}")
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
            response = api_instance.patch_namespaced_custom_object(
                group=SPACE_TEMPLATE_GROUP,
                version=SPACE_TEMPLATE_VERSION,
                namespace=self.namespace,
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

        Serializes the template configuration data to a YAML string representation
        with readable formatting (non-flow style).

        **Returns:**

        str: YAML string representation of the template configuration

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Convert template to YAML
              >>> template = HPSpaceTemplate.get("my-template")
              >>> yaml_content = template.to_yaml()
              >>> print(yaml_content)
              
              >>> # Save template to file
              >>> with open("exported-template.yaml", "w") as f:
              ...     f.write(template.to_yaml())
        """
        return yaml.dump(self.config_data, default_flow_style=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the space template to dictionary format.

        Returns the template configuration data as a dictionary, which can be
        used for programmatic access to template properties or serialization
        to other formats.

        **Returns:**

        Dict[str, Any]: Dictionary representation of the template configuration

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Get template as dictionary
              >>> template = HPSpaceTemplate.get("my-template")
              >>> config_dict = template.to_dict()
              >>> print(f"Template spec: {config_dict['spec']}")
              
              >>> # Access specific configuration values
              >>> display_name = config_dict['spec']['displayName']
              >>> default_image = config_dict['spec']['defaultImage']
        """
        return self.config_data
