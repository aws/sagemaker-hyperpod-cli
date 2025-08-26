KUBERNETES_JS_ENDPOINT_TEMPLATE = """### Please keep template file unchanged ###
apiVersion: inference.sagemaker.aws.amazon.com/v1alpha1
kind: JumpStartModel
metadata:
  name:                {{ model_id }}
  namespace:           {{ namespace or "default" }}
spec:
  model:
    acceptEula:               {{ accept_eula or false }}
    modelHubName:             "SageMakerPublicHub"
    modelId:                  {{ model_id }}
    modelVersion:             {{ model_version or "" }}
  sageMakerEndpoint:
    name:                     {{ endpoint_name or "" }}
  server:
    instanceType:             {{ instance_type }}
"""