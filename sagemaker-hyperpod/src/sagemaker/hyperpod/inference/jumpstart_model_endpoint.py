from hyperpod.inference.config.constants import *
from hyperpod.inference.config.jumpstart_model_endpoint_config import Model, JumpStartModelSpec, SageMakerEndpoint, Server
from hyperpod.inference.model_endpoint_base import ModelEndpointBase
from datetime import datetime


class JumpStartModelEndpoint(ModelEndpointBase):
    def __init__(
        self,
        namespace: str = 'default',
        model_id: str = None,
        instance_type: str = None,
        sagemaker_endpoint: str = None,
        spec: JumpStartModelSpec = None,
    ):
        if spec is None:
            spec = JumpStartModelSpec(
                model=Model(model_id=model_id),
                server=Server(instance_type=instance_type),
                sage_maker_endpoint=SageMakerEndpoint(name=sagemaker_endpoint),
            )

        super().__init__(
            name=spec.model.modelId,    # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec
        )
        
        '''
        if not self.spec.sageMakerEndpoint.name :
            time_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")
            endpoint_name = self.spec.model.modelId + '-' + time_str
            self.spec.sage_maker_endpoint.name = endpoint_name
        '''