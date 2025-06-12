from hyperpod.inference.config.constants import *
from hyperpod.inference.config.jumpstart_model_endpoint_config import Model, JumpStartModelSpec, SageMakerEndpoint, Server
from hyperpod.inference.model_endpoint_base import ModelEndpointBase
from datetime import datetime


class JumpStartModelEndpoint(ModelEndpointBase):
    def _validate_inputs(
            self,
            model_id: str,
            instance_type: str,
            spec: JumpStartModelSpec,
        ):
        # Check if spec is provided, other parameters should be None
        if spec is not None:
            if model_id or instance_type:
                raise ValueError("Either spec or model_id and instance_type must be provided, but not both.")
            if not isinstance(spec, JumpStartModelSpec):
                raise TypeError(f"spec must be of type JumpStartModelSpec, got {type(spec)}")
            return

        # Validate required parameters when spec is None
        if model_id is None or instance_type is None:
            raise ValueError("Must provide both model_id and instance_type.")
        
        # Type validation
        if not isinstance(model_id, str):
            raise TypeError(f"model_id must be of type str, got {type(model_id)}")
        if not isinstance(instance_type, str):
            raise TypeError(f"instance_type must be of type str, got {type(instance_type)}")

    def _validate_instance_type(self):
        '''
        Get supported instance types from node and model
        '''
        pass

    def _get_default_endpoint_name(self, model_id):
        '''
        Generate default endpoint name if not specified by user
        '''
        time_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")
        
        return model_id + '-' + time_str
    
    def create(
        self,
        namespace: str,
        model_id: str = None,
        instance_type: str = None,
        spec: JumpStartModelSpec = None,
    ):
        self._validate_inputs(model_id, instance_type, spec)

        if spec is None:
            sagemaker_endpoint = self._get_default_endpoint_name(model_id)
            
            # create spec config
            spec = JumpStartModelSpec(
                model=Model(model_id=model_id),
                server=Server(instance_type=instance_type),
                sage_maker_endpoint=SageMakerEndpoint(name=sagemaker_endpoint),
            )

        self.invoke_api_call(
            name=spec.model.modelId,    # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )
