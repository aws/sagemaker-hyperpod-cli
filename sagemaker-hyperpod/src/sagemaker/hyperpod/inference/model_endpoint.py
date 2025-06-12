from hyperpod.inference.config.constants import *
from hyperpod.inference.config.model_endpoint_config import InferenceEndpointConfigSpec, ModelSourceConfig, S3Storage, FsxStorage
from hyperpod.inference.model_endpoint_base import ModelEndpointBase
from datetime import datetime
from typing import Union


class ModelEndpoint(ModelEndpointBase):
    def _validate_inputs(
        self,
        model_name: str,
        instance_type: str,
        image: str,
        container_port: int,
        model_source_type: Union["fsx", "s3"],
        bucket_name: str,
        bucket_region: str,
        fsx_dns_name: str,
        fsx_file_system_id: str,
        fsx_mount_name: str,
        spec: InferenceEndpointConfigSpec,
    ):
        # Check if spec is provided, other parameters should be None
        if spec is not None:
            if any([model_name, instance_type, image, container_port, model_source_type, 
                    bucket_name, bucket_region, fsx_dns_name, fsx_file_system_id, fsx_mount_name]):
                raise ValueError("When spec is provided, all other parameters must be None")
            if not isinstance(spec, InferenceEndpointConfigSpec):
                raise TypeError(f"spec must be of type InferenceEndpointConfigSpec, got {type(spec)}")
            return
        
        # Validate required parameters when spec is None
        required_params = [model_name, instance_type, image, container_port, model_source_type]
        if any(param is None for param in required_params):
            raise ValueError("When spec is None, model_name, instance_type, image, container_port, and model_source_type must be provided")
        
        # Type validation
        if not isinstance(model_name, str):
            raise TypeError(f"model_name must be of type str, got {type(model_name)}")
        if not isinstance(instance_type, str):
            raise TypeError(f"instance_type must be of type str, got {type(instance_type)}")
        if not isinstance(image, str):
            raise TypeError(f"image must be of type str, got {type(image)}")
        if not isinstance(container_port, int):
            raise TypeError(f"container_port must be of type int, got {type(container_port)}")
        if not isinstance(model_source_type, str) or model_source_type not in ["fsx", "s3"]:
            raise TypeError(f"model_source_type must be either 'fsx' or 's3', got {model_source_type}")
        
        # Validate model_source_type specific parameters
        if model_source_type == 's3':
            if any([bucket_name is None, bucket_region is None]):
                raise ValueError("When model_source_type is 's3', bucket_name and bucket_region must be provided")
            if not isinstance(bucket_name, str):
                raise TypeError(f"bucket_name must be of type str, got {type(bucket_name)}")
            if not isinstance(bucket_region, str):
                raise TypeError(f"bucket_region must be of type str, got {type(bucket_region)}")
        elif model_source_type == 'fsx':
            if fsx_file_system_id is None:
                raise ValueError("When model_source_type is 'fsx', fsx_file_system_id must be provided")
            if not isinstance(fsx_file_system_id, str):
                raise TypeError(f"fsx_file_system_id must be of type str, got {type(fsx_file_system_id)}")
            if fsx_dns_name is not None and not isinstance(fsx_dns_name, str):
                raise TypeError(f"fsx_dns_name must be of type str, got {type(fsx_dns_name)}")
            if fsx_mount_name is not None and not isinstance(fsx_mount_name, str):
                raise TypeError(f"fsx_mount_name must be of type str, got {type(fsx_mount_name)}")

    def _validate_instance_type(self):
        '''
        Get supported instance types from node and model
        '''
        pass

    def _get_default_endpoint_name(self, model_name):
        '''
        Generate default endpoint name if not specified by user
        '''
        time_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")
        
        return model_name + '-' + time_str
    
    def create(
        self,
        namespace: str,
        model_name: str = None,
        instance_type: str = None,
        image: str = None,
        container_port: int = None,
        model_source_type: Union["fsx", "s3"] = None,
        bucket_name: str = None,
        bucket_region: str = None,
        fsx_dns_name: str = None,
        fsx_file_system_id: str = None,
        fsx_mount_name: str = None,
        spec: InferenceEndpointConfigSpec = None,
    ):
        self._validate_inputs(
            model_name, 
            instance_type, 
            image, 
            container_port, 
            model_source_type, 
            bucket_name, 
            bucket_region, 
            fsx_dns_name, 
            fsx_file_system_id, 
            fsx_mount_name, 
            spec
        )

        if spec is None:
            endpoint_name = self._get_default_endpoint_name(model_id)
            
            if model_source_type =='s3':
                model_source_config = ModelSourceConfig(
                    model_source_type=model_source_type,
                    s3_storage=S3Storage(
                        bucket_name=bucket_name,
                        region=bucket_region,
                    )
                )
            else:
                model_source_config = ModelSourceConfig(
                    model_source_type=model_source_type,
                    s3_storage=FsxStorage(
                        fsx_dns_name=fsx_dns_name,
                        file_system_id=fsx_file_system_id,
                        mount_name=fsx_mount_name
                    )
                )

            # create spec config
            spec = InferenceEndpointConfigSpec(
                endpoint_name=endpoint_name,
                instance_type=instance_type,
                model_name=model_name,
                model_source_config=model_source_config,
                image=image,
                container_port=container_port,
            )

        self.invoke_api_call(
            name=spec.modelName,    # use model name as metadata name
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
            spec=spec,
        )