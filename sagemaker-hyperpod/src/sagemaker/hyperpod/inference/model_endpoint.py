from hyperpod.inference.config.constants import *
from hyperpod.inference.config.model_endpoint_config import InferenceEndpointConfigSpec
from hyperpod.inference.model_endpoint_base import ModelEndpointBase
from datetime import datetime


class ModelEndpoint(ModelEndpointBase):
    def __init__(
        self,
        spec: InferenceEndpointConfigSpec,
        namespace: str = 'default',
    ):
        super().__init__(
            name=spec.modelName,    # use model name as metadata name
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
            spec=spec
        )

        if not self.spec.endpointName:
            time_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")
            self.spec.endpointName = self.spec.modelName + '-' + time_str
