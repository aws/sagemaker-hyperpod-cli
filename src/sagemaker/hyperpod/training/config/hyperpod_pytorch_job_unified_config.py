from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union


class Conditions(BaseModel):
    """JobCondition describes current state of a job."""

    model_config = ConfigDict(extra="forbid")

    lastProbeTime: Optional[str] = Field(
        default=None,
        alias="last_probe_time",
        description="Last time the condition was checked.",
    )
    lastTransitionTime: Optional[str] = Field(
        default=None,
        alias="last_transition_time",
        description="Last time the condition transit from one status to another.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Human readable message indicating details about last transition.",
    )
    reason: Optional[str] = Field(
        default=None, description="(brief) reason for the condition's last transition."
    )
    status: str = Field(
        description="Status of the condition, one of True, False, Unknown."
    )
    type: str = Field(description="Type of job condition, Complete or Failed.")


class JobPods(BaseModel):
    """ObjectReference contains enough information to let you inspect or modify the referred object."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None, alias="api_version", description="API version of the referent."
    )
    fieldPath: Optional[str] = Field(
        default=None,
        alias="field_path",
        description='If referring to a piece of an object instead of an entire object, this string should contain a valid JSON/Go field access statement, such as desiredState.manifest.containers[2]. For example, if the object reference is to a container within a pod, this would take on a value like: "spec.containers{name}" (where "name" refers to the name of the container that triggered the event) or if no container name is specified "spec.containers[2]" (container with index 2 in this pod). This syntax is chosen only to have some well-defined way of referencing a part of an object.',
    )
    kind: Optional[str] = Field(
        default=None,
        description="Kind of the referent. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds",
    )
    name: Optional[str] = Field(
        default=None,
        description="Name of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/",
    )
    resourceVersion: Optional[str] = Field(
        default=None,
        alias="resource_version",
        description="Specific resourceVersion to which this reference is made, if any. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#concurrency-control-and-consistency",
    )
    uid: Optional[str] = Field(
        default=None,
        description="UID of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids",
    )


class ManagerPods(BaseModel):
    """Pod Manager pods"""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None, alias="api_version", description="API version of the referent."
    )
    fieldPath: Optional[str] = Field(
        default=None,
        alias="field_path",
        description='If referring to a piece of an object instead of an entire object, this string should contain a valid JSON/Go field access statement, such as desiredState.manifest.containers[2]. For example, if the object reference is to a container within a pod, this would take on a value like: "spec.containers{name}" (where "name" refers to the name of the container that triggered the event) or if no container name is specified "spec.containers[2]" (container with index 2 in this pod). This syntax is chosen only to have some well-defined way of referencing a part of an object.',
    )
    kind: Optional[str] = Field(
        default=None,
        description="Kind of the referent. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds",
    )
    name: Optional[str] = Field(
        default=None,
        description="Name of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/",
    )
    resourceVersion: Optional[str] = Field(
        default=None,
        alias="resource_version",
        description="Specific resourceVersion to which this reference is made, if any. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#concurrency-control-and-consistency",
    )
    uid: Optional[str] = Field(
        default=None,
        description="UID of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids",
    )


class PodManagerStatuses(BaseModel):
    """ObjectReference contains enough information to let you inspect or modify the referred object."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None, alias="api_version", description="API version of the referent."
    )
    fieldPath: Optional[str] = Field(
        default=None,
        alias="field_path",
        description='If referring to a piece of an object instead of an entire object, this string should contain a valid JSON/Go field access statement, such as desiredState.manifest.containers[2]. For example, if the object reference is to a container within a pod, this would take on a value like: "spec.containers{name}" (where "name" refers to the name of the container that triggered the event) or if no container name is specified "spec.containers[2]" (container with index 2 in this pod). This syntax is chosen only to have some well-defined way of referencing a part of an object.',
    )
    kind: Optional[str] = Field(
        default=None,
        description="Kind of the referent. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds",
    )
    name: Optional[str] = Field(
        default=None,
        description="Name of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/",
    )
    resourceVersion: Optional[str] = Field(
        default=None,
        alias="resource_version",
        description="Specific resourceVersion to which this reference is made, if any. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#concurrency-control-and-consistency",
    )
    uid: Optional[str] = Field(
        default=None,
        description="UID of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids",
    )


class Tolerations(BaseModel):
    """The pod this Toleration is attached to tolerates any taint that matches the triple <key,value,effect> using the matching operator <operator>."""

    model_config = ConfigDict(extra="forbid")

    effect: Optional[str] = Field(
        default=None,
        description="Effect indicates the taint effect to match. Empty means match all taint effects. When specified, allowed values are NoSchedule, PreferNoSchedule and NoExecute.",
    )
    key: Optional[str] = Field(
        default=None,
        description="Key is the taint key that the toleration applies to. Empty means match all taint keys. If the key is empty, operator must be Exists; this combination means to match all values and all keys.",
    )
    operator: Optional[str] = Field(
        default=None,
        description="Operator represents a key's relationship to the value. Valid operators are Exists and Equal. Defaults to Equal. Exists is equivalent to wildcard for value, so that a pod can tolerate all taints of a particular category.",
    )
    tolerationSeconds: Optional[int] = Field(
        default=None,
        alias="toleration_seconds",
        description="TolerationSeconds represents the period of time the toleration (which must be of effect NoExecute, otherwise this field is ignored) tolerates the taint. By default, it is not set, which means tolerate the taint forever (do not evict). Zero and negative values will be treated as 0 (evict immediately) by the system.",
    )
    value: Optional[str] = Field(
        default=None,
        description="Value is the taint value the toleration matches to. If the operator is Exists, the value should be empty, otherwise just a regular string.",
    )


class PodSetInfo(BaseModel):
    """DEPRECATED podSetInfo to include pod set information provided by Kueue in podSetInfos PodSetInformation assigned to the HyperPodPytorchJob's PodSet by Kueue podSetInfo is retained here to support operator upgrade"""

    model_config = ConfigDict(extra="forbid")

    annotations: Optional[Dict[str, str]] = Field(
        default=None, description="Annotations to be added to the PodSpecTemplate"
    )
    labels: Optional[Dict[str, str]] = Field(
        default=None, description="Labels to be added to the PodSepcTemplate"
    )
    nodeSelector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="node_selector",
        description="NodeSelectors to be added to the PodSpecTemplate",
    )
    tolerations: Optional[List[Tolerations]] = Field(
        default=None, description="Tolerations to be added to the PodSpecTemplate"
    )


class PodSetInfos(BaseModel):
    """PodSetInformation contains the data that Kueue wants to inject into an admitted PodSpecTemplate"""

    model_config = ConfigDict(extra="forbid")

    annotations: Optional[Dict[str, str]] = Field(
        default=None, description="Annotations to be added to the PodSpecTemplate"
    )
    labels: Optional[Dict[str, str]] = Field(
        default=None, description="Labels to be added to the PodSepcTemplate"
    )
    nodeSelector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="node_selector",
        description="NodeSelectors to be added to the PodSpecTemplate",
    )
    tolerations: Optional[List[Tolerations]] = Field(
        default=None, description="Tolerations to be added to the PodSpecTemplate"
    )


class Metadata(BaseModel):
    """Standard object's metadata. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata"""

    model_config = ConfigDict(extra="forbid")

    annotations: Optional[Dict[str, str]] = None
    finalizers: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class MatchExpressions(BaseModel):
    """A node selector requirement is a selector that contains values, a key, and an operator that relates the key and values."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="The label key that the selector applies to.")
    operator: str = Field(
        description="Represents a key's relationship to a set of values. Valid operators are In, NotIn, Exists, DoesNotExist. Gt, and Lt."
    )
    values: Optional[List[str]] = Field(
        default=None,
        description="An array of string values. If the operator is In or NotIn, the values array must be non-empty. If the operator is Exists or DoesNotExist, the values array must be empty. If the operator is Gt or Lt, the values array must have a single element, which will be interpreted as an integer. This array is replaced during a strategic merge patch.",
    )


class MatchFields(BaseModel):
    """A node selector requirement is a selector that contains values, a key, and an operator that relates the key and values."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="The label key that the selector applies to.")
    operator: str = Field(
        description="Represents a key's relationship to a set of values. Valid operators are In, NotIn, Exists, DoesNotExist. Gt, and Lt."
    )
    values: Optional[List[str]] = Field(
        default=None,
        description="An array of string values. If the operator is In or NotIn, the values array must be non-empty. If the operator is Exists or DoesNotExist, the values array must be empty. If the operator is Gt or Lt, the values array must have a single element, which will be interpreted as an integer. This array is replaced during a strategic merge patch.",
    )


class Preference(BaseModel):
    """A node selector term, associated with the corresponding weight."""

    model_config = ConfigDict(extra="forbid")

    matchExpressions: Optional[List[MatchExpressions]] = Field(
        default=None,
        alias="match_expressions",
        description="A list of node selector requirements by node's labels.",
    )
    matchFields: Optional[List[MatchFields]] = Field(
        default=None,
        alias="match_fields",
        description="A list of node selector requirements by node's fields.",
    )


class PreferredDuringSchedulingIgnoredDuringExecution(BaseModel):
    """An empty preferred scheduling term matches all objects with implicit weight 0 (i.e. it's a no-op). A null preferred scheduling term matches no objects (i.e. is also a no-op)."""

    model_config = ConfigDict(extra="forbid")

    preference: Preference = Field(
        description="A node selector term, associated with the corresponding weight."
    )
    weight: int = Field(
        description="Weight associated with matching the corresponding nodeSelectorTerm, in the range 1-100."
    )


class NodeSelectorTerms(BaseModel):
    """A null or empty node selector term matches no objects. The requirements of them are ANDed. The TopologySelectorTerm type implements a subset of the NodeSelectorTerm."""

    model_config = ConfigDict(extra="forbid")

    matchExpressions: Optional[List[MatchExpressions]] = Field(
        default=None,
        alias="match_expressions",
        description="A list of node selector requirements by node's labels.",
    )
    matchFields: Optional[List[MatchFields]] = Field(
        default=None,
        alias="match_fields",
        description="A list of node selector requirements by node's fields.",
    )


class RequiredDuringSchedulingIgnoredDuringExecution(BaseModel):
    """If the affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to an update), the system may or may not try to eventually evict the pod from its node."""

    model_config = ConfigDict(extra="forbid")

    nodeSelectorTerms: List[NodeSelectorTerms] = Field(
        alias="node_selector_terms",
        description="Required. A list of node selector terms. The terms are ORed.",
    )


class NodeAffinity(BaseModel):
    """Describes node affinity scheduling rules for the pod."""

    model_config = ConfigDict(extra="forbid")

    preferredDuringSchedulingIgnoredDuringExecution: Optional[
        List[PreferredDuringSchedulingIgnoredDuringExecution]
    ] = Field(
        default=None,
        alias="preferred_during_scheduling_ignored_during_execution",
        description='The scheduler will prefer to schedule pods to nodes that satisfy the affinity expressions specified by this field, but it may choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.), compute a sum by iterating through the elements of this field and adding "weight" to the sum if the node matches the corresponding matchExpressions; the node(s) with the highest sum are the most preferred.',
    )
    requiredDuringSchedulingIgnoredDuringExecution: Optional[
        RequiredDuringSchedulingIgnoredDuringExecution
    ] = Field(
        default=None,
        alias="required_during_scheduling_ignored_during_execution",
        description="If the affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to an update), the system may or may not try to eventually evict the pod from its node.",
    )


class PodAffinity(BaseModel):
    """Describes pod affinity scheduling rules (e.g. co-locate this pod in the same node, zone, etc. as some other pod(s))."""

    model_config = ConfigDict(extra="forbid")

    preferredDuringSchedulingIgnoredDuringExecution: Optional[
        List[PreferredDuringSchedulingIgnoredDuringExecution]
    ] = Field(
        default=None,
        alias="preferred_during_scheduling_ignored_during_execution",
        description='The scheduler will prefer to schedule pods to nodes that satisfy the affinity expressions specified by this field, but it may choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.), compute a sum by iterating through the elements of this field and adding "weight" to the sum if the node has pods which matches the corresponding podAffinityTerm; the node(s) with the highest sum are the most preferred.',
    )
    requiredDuringSchedulingIgnoredDuringExecution: Optional[
        List[RequiredDuringSchedulingIgnoredDuringExecution]
    ] = Field(
        default=None,
        alias="required_during_scheduling_ignored_during_execution",
        description="If the affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to a pod label update), the system may or may not try to eventually evict the pod from its node. When there are multiple elements, the lists of nodes corresponding to each podAffinityTerm are intersected, i.e. all terms must be satisfied.",
    )


class PodAntiAffinity(BaseModel):
    """Describes pod anti-affinity scheduling rules (e.g. avoid putting this pod in the same node, zone, etc. as some other pod(s))."""

    model_config = ConfigDict(extra="forbid")

    preferredDuringSchedulingIgnoredDuringExecution: Optional[
        List[PreferredDuringSchedulingIgnoredDuringExecution]
    ] = Field(
        default=None,
        alias="preferred_during_scheduling_ignored_during_execution",
        description='The scheduler will prefer to schedule pods to nodes that satisfy the anti-affinity expressions specified by this field, but it may choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling anti-affinity expressions, etc.), compute a sum by iterating through the elements of this field and adding "weight" to the sum if the node has pods which matches the corresponding podAffinityTerm; the node(s) with the highest sum are the most preferred.',
    )
    requiredDuringSchedulingIgnoredDuringExecution: Optional[
        List[RequiredDuringSchedulingIgnoredDuringExecution]
    ] = Field(
        default=None,
        alias="required_during_scheduling_ignored_during_execution",
        description="If the anti-affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the anti-affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to a pod label update), the system may or may not try to eventually evict the pod from its node. When there are multiple elements, the lists of nodes corresponding to each podAffinityTerm are intersected, i.e. all terms must be satisfied.",
    )


class Affinity(BaseModel):
    """If specified, the pod's scheduling constraints"""

    model_config = ConfigDict(extra="forbid")

    nodeAffinity: Optional[NodeAffinity] = Field(
        default=None,
        alias="node_affinity",
        description="Describes node affinity scheduling rules for the pod.",
    )
    podAffinity: Optional[PodAffinity] = Field(
        default=None,
        alias="pod_affinity",
        description="Describes pod affinity scheduling rules (e.g. co-locate this pod in the same node, zone, etc. as some other pod(s)).",
    )
    podAntiAffinity: Optional[PodAntiAffinity] = Field(
        default=None,
        alias="pod_anti_affinity",
        description="Describes pod anti-affinity scheduling rules (e.g. avoid putting this pod in the same node, zone, etc. as some other pod(s)).",
    )


class ConfigMapKeyRef(BaseModel):
    """Selects a key of a ConfigMap."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="The key to select.")
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="Specify whether the ConfigMap or its key must be defined",
    )


class FieldRef(BaseModel):
    """Selects a field of the pod: supports metadata.name, metadata.namespace, `metadata.labels['<KEY>']`, `metadata.annotations['<KEY>']`, spec.nodeName, spec.serviceAccountName, status.hostIP, status.podIP, status.podIPs."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None,
        alias="api_version",
        description='Version of the schema the FieldPath is written in terms of, defaults to "v1".',
    )
    fieldPath: str = Field(
        alias="field_path",
        description="Path of the field to select in the specified API version.",
    )


class ResourceFieldRef(BaseModel):
    """Selects a resource of the container: only resources limits and requests (limits.cpu, limits.memory, limits.ephemeral-storage, requests.cpu, requests.memory and requests.ephemeral-storage) are currently supported."""

    model_config = ConfigDict(extra="forbid")

    containerName: Optional[str] = Field(
        default=None,
        alias="container_name",
        description="Container name: required for volumes, optional for env vars",
    )
    divisor: Optional[Union[int, str]] = Field(
        default=None,
        description='Specifies the output format of the exposed resources, defaults to "1"',
    )
    resource: str = Field(description="Required: resource to select")


class SecretKeyRef(BaseModel):
    """Selects a key of a secret in the pod's namespace"""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        description="The key of the secret to select from.  Must be a valid secret key."
    )
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="Specify whether the Secret or its key must be defined",
    )


class ValueFrom(BaseModel):
    """Source for the environment variable's value. Cannot be used if value is not empty."""

    model_config = ConfigDict(extra="forbid")

    configMapKeyRef: Optional[ConfigMapKeyRef] = Field(
        default=None,
        alias="config_map_key_ref",
        description="Selects a key of a ConfigMap.",
    )
    fieldRef: Optional[FieldRef] = Field(
        default=None,
        alias="field_ref",
        description="Selects a field of the pod: supports metadata.name, metadata.namespace, `metadata.labels['<KEY>']`, `metadata.annotations['<KEY>']`, spec.nodeName, spec.serviceAccountName, status.hostIP, status.podIP, status.podIPs.",
    )
    resourceFieldRef: Optional[ResourceFieldRef] = Field(
        default=None,
        alias="resource_field_ref",
        description="Selects a resource of the container: only resources limits and requests (limits.cpu, limits.memory, limits.ephemeral-storage, requests.cpu, requests.memory and requests.ephemeral-storage) are currently supported.",
    )
    secretKeyRef: Optional[SecretKeyRef] = Field(
        default=None,
        alias="secret_key_ref",
        description="Selects a key of a secret in the pod's namespace",
    )


class Env(BaseModel):
    """EnvVar represents an environment variable present in a Container."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name of the environment variable. Must be a C_IDENTIFIER."
    )
    value: Optional[str] = Field(
        default=None,
        description='Variable references $(VAR_NAME) are expanded using the previously defined environment variables in the container and any service environment variables. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Defaults to "".',
    )
    valueFrom: Optional[ValueFrom] = Field(
        default=None,
        alias="value_from",
        description="Source for the environment variable's value. Cannot be used if value is not empty.",
    )


class ConfigMapRef(BaseModel):
    """The ConfigMap to select from"""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None, description="Specify whether the ConfigMap must be defined"
    )


class SecretRef(BaseModel):
    """The Secret to select from"""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None, description="Specify whether the Secret must be defined"
    )


class EnvFrom(BaseModel):
    """EnvFromSource represents the source of a set of ConfigMaps"""

    model_config = ConfigDict(extra="forbid")

    configMapRef: Optional[ConfigMapRef] = Field(
        default=None, alias="config_map_ref", description="The ConfigMap to select from"
    )
    prefix: Optional[str] = Field(
        default=None,
        description="An optional identifier to prepend to each key in the ConfigMap. Must be a C_IDENTIFIER.",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None, alias="secret_ref", description="The Secret to select from"
    )


class Exec(BaseModel):
    """Exec specifies the action to take."""

    model_config = ConfigDict(extra="forbid")

    command: Optional[List[str]] = Field(
        default=None,
        description="Command is the command line to execute inside the container, the working directory for the command  is root ('/') in the container's filesystem. The command is simply exec'd, it is not run inside a shell, so traditional shell instructions ('|', etc) won't work. To use a shell, you need to explicitly call out to that shell. Exit status of 0 is treated as live/healthy and non-zero is unhealthy.",
    )


class HttpHeaders(BaseModel):
    """HTTPHeader describes a custom header to be used in HTTP probes"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="The header field name. This will be canonicalized upon output, so case-variant names will be understood as the same header."
    )
    value: str = Field(description="The header field value")


class HttpGet(BaseModel):
    """HTTPGet specifies the http request to perform."""

    model_config = ConfigDict(extra="forbid")

    host: Optional[str] = Field(
        default=None,
        description='Host name to connect to, defaults to the pod IP. You probably want to set "Host" in httpHeaders instead.',
    )
    httpHeaders: Optional[List[HttpHeaders]] = Field(
        default=None,
        alias="http_headers",
        description="Custom headers to set in the request. HTTP allows repeated headers.",
    )
    path: Optional[str] = Field(
        default=None, description="Path to access on the HTTP server."
    )
    port: Union[int, str] = Field(
        description="Name or number of the port to access on the container. Number must be in the range 1 to 65535. Name must be an IANA_SVC_NAME."
    )
    scheme: Optional[str] = Field(
        default=None,
        description="Scheme to use for connecting to the host. Defaults to HTTP.",
    )


class Sleep(BaseModel):
    """Sleep represents the duration that the container should sleep before being terminated."""

    model_config = ConfigDict(extra="forbid")

    seconds: int = Field(description="Seconds is the number of seconds to sleep.")


class TcpSocket(BaseModel):
    """Deprecated. TCPSocket is NOT supported as a LifecycleHandler and kept for the backward compatibility. There are no validation of this field and lifecycle hooks will fail in runtime when tcp handler is specified."""

    model_config = ConfigDict(extra="forbid")

    host: Optional[str] = Field(
        default=None,
        description="Optional: Host name to connect to, defaults to the pod IP.",
    )
    port: Union[int, str] = Field(
        description="Number or name of the port to access on the container. Number must be in the range 1 to 65535. Name must be an IANA_SVC_NAME."
    )


class PostStart(BaseModel):
    """PostStart is called immediately after a container is created. If the handler fails, the container is terminated and restarted according to its restart policy. Other management of the container blocks until the hook completes. More info: https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#container-hooks"""

    model_config = ConfigDict(extra="forbid")

    exec: Optional[Exec] = Field(
        default=None, description="Exec specifies the action to take."
    )
    httpGet: Optional[HttpGet] = Field(
        default=None,
        alias="http_get",
        description="HTTPGet specifies the http request to perform.",
    )
    sleep: Optional[Sleep] = Field(
        default=None,
        description="Sleep represents the duration that the container should sleep before being terminated.",
    )
    tcpSocket: Optional[TcpSocket] = Field(
        default=None,
        alias="tcp_socket",
        description="Deprecated. TCPSocket is NOT supported as a LifecycleHandler and kept for the backward compatibility. There are no validation of this field and lifecycle hooks will fail in runtime when tcp handler is specified.",
    )


class PreStop(BaseModel):
    """PreStop is called immediately before a container is terminated due to an API request or management event such as liveness/startup probe failure, preemption, resource contention, etc. The handler is not called if the container crashes or exits. The Pod's termination grace period countdown begins before the PreStop hook is executed. Regardless of the outcome of the handler, the container will eventually terminate within the Pod's termination grace period (unless delayed by finalizers). Other management of the container blocks until the hook completes or until the termination grace period is reached. More info: https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#container-hooks"""

    model_config = ConfigDict(extra="forbid")

    exec: Optional[Exec] = Field(
        default=None, description="Exec specifies the action to take."
    )
    httpGet: Optional[HttpGet] = Field(
        default=None,
        alias="http_get",
        description="HTTPGet specifies the http request to perform.",
    )
    sleep: Optional[Sleep] = Field(
        default=None,
        description="Sleep represents the duration that the container should sleep before being terminated.",
    )
    tcpSocket: Optional[TcpSocket] = Field(
        default=None,
        alias="tcp_socket",
        description="Deprecated. TCPSocket is NOT supported as a LifecycleHandler and kept for the backward compatibility. There are no validation of this field and lifecycle hooks will fail in runtime when tcp handler is specified.",
    )


class Lifecycle(BaseModel):
    """Actions that the management system should take in response to container lifecycle events. Cannot be updated."""

    model_config = ConfigDict(extra="forbid")

    postStart: Optional[PostStart] = Field(
        default=None,
        alias="post_start",
        description="PostStart is called immediately after a container is created. If the handler fails, the container is terminated and restarted according to its restart policy. Other management of the container blocks until the hook completes. More info: https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#container-hooks",
    )
    preStop: Optional[PreStop] = Field(
        default=None,
        alias="pre_stop",
        description="PreStop is called immediately before a container is terminated due to an API request or management event such as liveness/startup probe failure, preemption, resource contention, etc. The handler is not called if the container crashes or exits. The Pod's termination grace period countdown begins before the PreStop hook is executed. Regardless of the outcome of the handler, the container will eventually terminate within the Pod's termination grace period (unless delayed by finalizers). Other management of the container blocks until the hook completes or until the termination grace period is reached. More info: https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#container-hooks",
    )


class Grpc(BaseModel):
    """GRPC specifies an action involving a GRPC port."""

    model_config = ConfigDict(extra="forbid")

    port: int = Field(
        description="Port number of the gRPC service. Number must be in the range 1 to 65535."
    )
    service: Optional[str] = Field(
        default="",
        description="Service is the name of the service to place in the gRPC HealthCheckRequest (see https://github.com/grpc/grpc/blob/master/doc/health-checking.md).  If this is not specified, the default behavior is defined by gRPC.",
    )


class LivenessProbe(BaseModel):
    """Periodic probe of container liveness. Container will be restarted if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes"""

    model_config = ConfigDict(extra="forbid")

    exec: Optional[Exec] = Field(
        default=None, description="Exec specifies the action to take."
    )
    failureThreshold: Optional[int] = Field(
        default=None,
        alias="failure_threshold",
        description="Minimum consecutive failures for the probe to be considered failed after having succeeded. Defaults to 3. Minimum value is 1.",
    )
    grpc: Optional[Grpc] = Field(
        default=None, description="GRPC specifies an action involving a GRPC port."
    )
    httpGet: Optional[HttpGet] = Field(
        default=None,
        alias="http_get",
        description="HTTPGet specifies the http request to perform.",
    )
    initialDelaySeconds: Optional[int] = Field(
        default=None,
        alias="initial_delay_seconds",
        description="Number of seconds after the container has started before liveness probes are initiated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    periodSeconds: Optional[int] = Field(
        default=None,
        alias="period_seconds",
        description="How often (in seconds) to perform the probe. Default to 10 seconds. Minimum value is 1.",
    )
    successThreshold: Optional[int] = Field(
        default=None,
        alias="success_threshold",
        description="Minimum consecutive successes for the probe to be considered successful after having failed. Defaults to 1. Must be 1 for liveness and startup. Minimum value is 1.",
    )
    tcpSocket: Optional[TcpSocket] = Field(
        default=None,
        alias="tcp_socket",
        description="TCPSocket specifies an action involving a TCP port.",
    )
    terminationGracePeriodSeconds: Optional[int] = Field(
        default=None,
        alias="termination_grace_period_seconds",
        description="Optional duration in seconds the pod needs to terminate gracefully upon probe failure. The grace period is the duration in seconds after the processes running in the pod are sent a termination signal and the time when the processes are forcibly halted with a kill signal. Set this value longer than the expected cleanup time for your process. If this value is nil, the pod's terminationGracePeriodSeconds will be used. Otherwise, this value overrides the value provided by the pod spec. Value must be non-negative integer. The value zero indicates stop immediately via the kill signal (no opportunity to shut down). This is a beta field and requires enabling ProbeTerminationGracePeriod feature gate. Minimum value is 1. spec.terminationGracePeriodSeconds is used if unset.",
    )
    timeoutSeconds: Optional[int] = Field(
        default=None,
        alias="timeout_seconds",
        description="Number of seconds after which the probe times out. Defaults to 1 second. Minimum value is 1. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )


class Ports(BaseModel):
    """ContainerPort represents a network port in a single container."""

    model_config = ConfigDict(extra="forbid")

    containerPort: int = Field(
        alias="container_port",
        description="Number of port to expose on the pod's IP address. This must be a valid port number, 0 < x < 65536.",
    )
    hostIP: Optional[str] = Field(
        default=None,
        alias="host_ip",
        description="What host IP to bind the external port to.",
    )
    hostPort: Optional[int] = Field(
        default=None,
        alias="host_port",
        description="Number of port to expose on the host. If specified, this must be a valid port number, 0 < x < 65536. If HostNetwork is specified, this must match ContainerPort. Most containers do not need this.",
    )
    name: Optional[str] = Field(
        default=None,
        description="If specified, this must be an IANA_SVC_NAME and unique within the pod. Each named port in a pod must have a unique name. Name for the port that can be referred to by services.",
    )
    protocol: Optional[str] = Field(
        default="TCP",
        description='Protocol for port. Must be UDP, TCP, or SCTP. Defaults to "TCP".',
    )


class ReadinessProbe(BaseModel):
    """Periodic probe of container service readiness. Container will be removed from service endpoints if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes"""

    model_config = ConfigDict(extra="forbid")

    exec: Optional[Exec] = Field(
        default=None, description="Exec specifies the action to take."
    )
    failureThreshold: Optional[int] = Field(
        default=None,
        alias="failure_threshold",
        description="Minimum consecutive failures for the probe to be considered failed after having succeeded. Defaults to 3. Minimum value is 1.",
    )
    grpc: Optional[Grpc] = Field(
        default=None, description="GRPC specifies an action involving a GRPC port."
    )
    httpGet: Optional[HttpGet] = Field(
        default=None,
        alias="http_get",
        description="HTTPGet specifies the http request to perform.",
    )
    initialDelaySeconds: Optional[int] = Field(
        default=None,
        alias="initial_delay_seconds",
        description="Number of seconds after the container has started before liveness probes are initiated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    periodSeconds: Optional[int] = Field(
        default=None,
        alias="period_seconds",
        description="How often (in seconds) to perform the probe. Default to 10 seconds. Minimum value is 1.",
    )
    successThreshold: Optional[int] = Field(
        default=None,
        alias="success_threshold",
        description="Minimum consecutive successes for the probe to be considered successful after having failed. Defaults to 1. Must be 1 for liveness and startup. Minimum value is 1.",
    )
    tcpSocket: Optional[TcpSocket] = Field(
        default=None,
        alias="tcp_socket",
        description="TCPSocket specifies an action involving a TCP port.",
    )
    terminationGracePeriodSeconds: Optional[int] = Field(
        default=None,
        alias="termination_grace_period_seconds",
        description="Optional duration in seconds the pod needs to terminate gracefully upon probe failure. The grace period is the duration in seconds after the processes running in the pod are sent a termination signal and the time when the processes are forcibly halted with a kill signal. Set this value longer than the expected cleanup time for your process. If this value is nil, the pod's terminationGracePeriodSeconds will be used. Otherwise, this value overrides the value provided by the pod spec. Value must be non-negative integer. The value zero indicates stop immediately via the kill signal (no opportunity to shut down). This is a beta field and requires enabling ProbeTerminationGracePeriod feature gate. Minimum value is 1. spec.terminationGracePeriodSeconds is used if unset.",
    )
    timeoutSeconds: Optional[int] = Field(
        default=None,
        alias="timeout_seconds",
        description="Number of seconds after which the probe times out. Defaults to 1 second. Minimum value is 1. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )


class ResizePolicy(BaseModel):
    """ContainerResizePolicy represents resource resize policy for the container."""

    model_config = ConfigDict(extra="forbid")

    resourceName: str = Field(
        alias="resource_name",
        description="Name of the resource to which this resource resize policy applies. Supported values: cpu, memory.",
    )
    restartPolicy: str = Field(
        alias="restart_policy",
        description="Restart policy to apply when specified resource is resized. If not specified, it defaults to NotRequired.",
    )


class Claims(BaseModel):
    """ResourceClaim references one entry in PodSpec.ResourceClaims."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name must match the name of one entry in pod.spec.resourceClaims of the Pod where this field is used. It makes that resource available inside a container."
    )
    request: Optional[str] = Field(
        default=None,
        description="Request is the name chosen for a request in the referenced claim. If empty, everything from the claim is made available, otherwise only the result of this request.",
    )


class Resources(BaseModel):
    """Compute Resources required by this container. Cannot be updated. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"""

    model_config = ConfigDict(extra="forbid")

    claims: Optional[List[Claims]] = Field(
        default=None,
        description="Claims lists the names of resources, defined in spec.resourceClaims, that are used by this container.  This is an alpha field and requires enabling the DynamicResourceAllocation feature gate.  This field is immutable. It can only be set for containers.",
    )
    limits: Optional[Dict[str, Union[int, str]]] = Field(
        default=None,
        description="Limits describes the maximum amount of compute resources allowed. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )
    requests: Optional[Dict[str, Union[int, str]]] = Field(
        default=None,
        description="Requests describes the minimum amount of compute resources required. If Requests is omitted for a container, it defaults to Limits if that is explicitly specified, otherwise to an implementation-defined value. Requests cannot exceed Limits. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )


class AppArmorProfile(BaseModel):
    """appArmorProfile is the AppArmor options to use by this container. If set, this profile overrides the pod's appArmorProfile. Note that this field cannot be set when spec.os.name is windows."""

    model_config = ConfigDict(extra="forbid")

    localhostProfile: Optional[str] = Field(
        default=None,
        alias="localhost_profile",
        description='localhostProfile indicates a profile loaded on the node that should be used. The profile must be preconfigured on the node to work. Must match the loaded name of the profile. Must be set if and only if type is "Localhost".',
    )
    type: str = Field(
        description="type indicates which kind of AppArmor profile will be applied. Valid options are:   Localhost - a profile pre-loaded on the node.   RuntimeDefault - the container runtime's default profile.   Unconfined - no AppArmor enforcement."
    )


class Capabilities(BaseModel):
    """The capabilities to add/drop when running containers. Defaults to the default set of capabilities granted by the container runtime. Note that this field cannot be set when spec.os.name is windows."""

    model_config = ConfigDict(extra="forbid")

    add: Optional[List[str]] = Field(default=None, description="Added capabilities")
    drop: Optional[List[str]] = Field(default=None, description="Removed capabilities")


class SeLinuxOptions(BaseModel):
    """The SELinux context to be applied to the container. If unspecified, the container runtime will allocate a random SELinux context for each container.  May also be set in PodSecurityContext.  If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is windows."""

    model_config = ConfigDict(extra="forbid")

    level: Optional[str] = Field(
        default=None,
        description="Level is SELinux level label that applies to the container.",
    )
    role: Optional[str] = Field(
        default=None,
        description="Role is a SELinux role label that applies to the container.",
    )
    type: Optional[str] = Field(
        default=None,
        description="Type is a SELinux type label that applies to the container.",
    )
    user: Optional[str] = Field(
        default=None,
        description="User is a SELinux user label that applies to the container.",
    )


class SeccompProfile(BaseModel):
    """The seccomp options to use by this container. If seccomp options are provided at both the pod & container level, the container options override the pod options. Note that this field cannot be set when spec.os.name is windows."""

    model_config = ConfigDict(extra="forbid")

    localhostProfile: Optional[str] = Field(
        default=None,
        alias="localhost_profile",
        description='localhostProfile indicates a profile defined in a file on the node should be used. The profile must be preconfigured on the node to work. Must be a descending path, relative to the kubelet\'s configured seccomp profile location. Must be set if type is "Localhost". Must NOT be set for any other type.',
    )
    type: str = Field(
        description="type indicates which kind of seccomp profile will be applied. Valid options are:  Localhost - a profile defined in a file on the node should be used. RuntimeDefault - the container runtime default profile should be used. Unconfined - no profile should be applied."
    )


class WindowsOptions(BaseModel):
    """The Windows specific settings applied to all containers. If unspecified, the options from the PodSecurityContext will be used. If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is linux."""

    model_config = ConfigDict(extra="forbid")

    gmsaCredentialSpec: Optional[str] = Field(
        default=None,
        alias="gmsa_credential_spec",
        description="GMSACredentialSpec is where the GMSA admission webhook (https://github.com/kubernetes-sigs/windows-gmsa) inlines the contents of the GMSA credential spec named by the GMSACredentialSpecName field.",
    )
    gmsaCredentialSpecName: Optional[str] = Field(
        default=None,
        alias="gmsa_credential_spec_name",
        description="GMSACredentialSpecName is the name of the GMSA credential spec to use.",
    )
    hostProcess: Optional[bool] = Field(
        default=None,
        alias="host_process",
        description="HostProcess determines if a container should be run as a 'Host Process' container. All of a Pod's containers must have the same effective HostProcess value (it is not allowed to have a mix of HostProcess containers and non-HostProcess containers). In addition, if HostProcess is true then HostNetwork must also be set to true.",
    )
    runAsUserName: Optional[str] = Field(
        default=None,
        alias="run_as_user_name",
        description="The UserName in Windows to run the entrypoint of the container process. Defaults to the user specified in image metadata if unspecified. May also be set in PodSecurityContext. If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence.",
    )


class SecurityContext(BaseModel):
    """SecurityContext defines the security options the container should be run with. If set, the fields of SecurityContext override the equivalent fields of PodSecurityContext. More info: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/"""

    model_config = ConfigDict(extra="forbid")

    allowPrivilegeEscalation: Optional[bool] = Field(
        default=None,
        alias="allow_privilege_escalation",
        description="AllowPrivilegeEscalation controls whether a process can gain more privileges than its parent process. This bool directly controls if the no_new_privs flag will be set on the container process. AllowPrivilegeEscalation is true always when the container is: 1) run as Privileged 2) has CAP_SYS_ADMIN Note that this field cannot be set when spec.os.name is windows.",
    )
    appArmorProfile: Optional[AppArmorProfile] = Field(
        default=None,
        alias="app_armor_profile",
        description="appArmorProfile is the AppArmor options to use by this container. If set, this profile overrides the pod's appArmorProfile. Note that this field cannot be set when spec.os.name is windows.",
    )
    capabilities: Optional[Capabilities] = Field(
        default=None,
        description="The capabilities to add/drop when running containers. Defaults to the default set of capabilities granted by the container runtime. Note that this field cannot be set when spec.os.name is windows.",
    )
    privileged: Optional[bool] = Field(
        default=None,
        description="Run container in privileged mode. Processes in privileged containers are essentially equivalent to root on the host. Defaults to false. Note that this field cannot be set when spec.os.name is windows.",
    )
    procMount: Optional[str] = Field(
        default=None,
        alias="proc_mount",
        description="procMount denotes the type of proc mount to use for the containers. The default value is Default which uses the container runtime defaults for readonly paths and masked paths. This requires the ProcMountType feature flag to be enabled. Note that this field cannot be set when spec.os.name is windows.",
    )
    readOnlyRootFilesystem: Optional[bool] = Field(
        default=None,
        alias="read_only_root_filesystem",
        description="Whether this container has a read-only root filesystem. Default is false. Note that this field cannot be set when spec.os.name is windows.",
    )
    runAsGroup: Optional[int] = Field(
        default=None,
        alias="run_as_group",
        description="The GID to run the entrypoint of the container process. Uses runtime default if unset. May also be set in PodSecurityContext.  If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is windows.",
    )
    runAsNonRoot: Optional[bool] = Field(
        default=None,
        alias="run_as_non_root",
        description="Indicates that the container must run as a non-root user. If true, the Kubelet will validate the image at runtime to ensure that it does not run as UID 0 (root) and fail to start the container if it does. If unset or false, no such validation will be performed. May also be set in PodSecurityContext.  If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence.",
    )
    runAsUser: Optional[int] = Field(
        default=None,
        alias="run_as_user",
        description="The UID to run the entrypoint of the container process. Defaults to user specified in image metadata if unspecified. May also be set in PodSecurityContext.  If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is windows.",
    )
    seLinuxOptions: Optional[SeLinuxOptions] = Field(
        default=None,
        alias="se_linux_options",
        description="The SELinux context to be applied to the container. If unspecified, the container runtime will allocate a random SELinux context for each container.  May also be set in PodSecurityContext.  If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is windows.",
    )
    seccompProfile: Optional[SeccompProfile] = Field(
        default=None,
        alias="seccomp_profile",
        description="The seccomp options to use by this container. If seccomp options are provided at both the pod & container level, the container options override the pod options. Note that this field cannot be set when spec.os.name is windows.",
    )
    windowsOptions: Optional[WindowsOptions] = Field(
        default=None,
        alias="windows_options",
        description="The Windows specific settings applied to all containers. If unspecified, the options from the PodSecurityContext will be used. If set in both SecurityContext and PodSecurityContext, the value specified in SecurityContext takes precedence. Note that this field cannot be set when spec.os.name is linux.",
    )


class StartupProbe(BaseModel):
    """StartupProbe indicates that the Pod has successfully initialized. If specified, no other probes are executed until this completes successfully. If this probe fails, the Pod will be restarted, just as if the livenessProbe failed. This can be used to provide different probe parameters at the beginning of a Pod's lifecycle, when it might take a long time to load data or warm a cache, than during steady-state operation. This cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes"""

    model_config = ConfigDict(extra="forbid")

    exec: Optional[Exec] = Field(
        default=None, description="Exec specifies the action to take."
    )
    failureThreshold: Optional[int] = Field(
        default=None,
        alias="failure_threshold",
        description="Minimum consecutive failures for the probe to be considered failed after having succeeded. Defaults to 3. Minimum value is 1.",
    )
    grpc: Optional[Grpc] = Field(
        default=None, description="GRPC specifies an action involving a GRPC port."
    )
    httpGet: Optional[HttpGet] = Field(
        default=None,
        alias="http_get",
        description="HTTPGet specifies the http request to perform.",
    )
    initialDelaySeconds: Optional[int] = Field(
        default=None,
        alias="initial_delay_seconds",
        description="Number of seconds after the container has started before liveness probes are initiated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    periodSeconds: Optional[int] = Field(
        default=None,
        alias="period_seconds",
        description="How often (in seconds) to perform the probe. Default to 10 seconds. Minimum value is 1.",
    )
    successThreshold: Optional[int] = Field(
        default=None,
        alias="success_threshold",
        description="Minimum consecutive successes for the probe to be considered successful after having failed. Defaults to 1. Must be 1 for liveness and startup. Minimum value is 1.",
    )
    tcpSocket: Optional[TcpSocket] = Field(
        default=None,
        alias="tcp_socket",
        description="TCPSocket specifies an action involving a TCP port.",
    )
    terminationGracePeriodSeconds: Optional[int] = Field(
        default=None,
        alias="termination_grace_period_seconds",
        description="Optional duration in seconds the pod needs to terminate gracefully upon probe failure. The grace period is the duration in seconds after the processes running in the pod are sent a termination signal and the time when the processes are forcibly halted with a kill signal. Set this value longer than the expected cleanup time for your process. If this value is nil, the pod's terminationGracePeriodSeconds will be used. Otherwise, this value overrides the value provided by the pod spec. Value must be non-negative integer. The value zero indicates stop immediately via the kill signal (no opportunity to shut down). This is a beta field and requires enabling ProbeTerminationGracePeriod feature gate. Minimum value is 1. spec.terminationGracePeriodSeconds is used if unset.",
    )
    timeoutSeconds: Optional[int] = Field(
        default=None,
        alias="timeout_seconds",
        description="Number of seconds after which the probe times out. Defaults to 1 second. Minimum value is 1. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )


class VolumeDevices(BaseModel):
    """volumeDevice describes a mapping of a raw block device within a container."""

    model_config = ConfigDict(extra="forbid")

    devicePath: str = Field(
        alias="device_path",
        description="devicePath is the path inside of the container that the device will be mapped to.",
    )
    name: str = Field(
        description="name must match the name of a persistentVolumeClaim in the pod"
    )


class VolumeMounts(BaseModel):
    """VolumeMount describes a mounting of a Volume within a container."""

    model_config = ConfigDict(extra="forbid")

    mountPath: str = Field(
        alias="mount_path",
        description="Path within the container at which the volume should be mounted.  Must not contain ':'.",
    )
    mountPropagation: Optional[str] = Field(
        default=None,
        alias="mount_propagation",
        description="mountPropagation determines how mounts are propagated from the host to container and the other way around. When not set, MountPropagationNone is used. This field is beta in 1.10. When RecursiveReadOnly is set to IfPossible or to Enabled, MountPropagation must be None or unspecified (which defaults to None).",
    )
    name: str = Field(description="This must match the Name of a Volume.")
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="Mounted read-only if true, read-write otherwise (false or unspecified). Defaults to false.",
    )
    recursiveReadOnly: Optional[str] = Field(
        default=None,
        alias="recursive_read_only",
        description="RecursiveReadOnly specifies whether read-only mounts should be handled recursively.  If ReadOnly is false, this field has no meaning and must be unspecified.  If ReadOnly is true, and this field is set to Disabled, the mount is not made recursively read-only.  If this field is set to IfPossible, the mount is made recursively read-only, if it is supported by the container runtime.  If this field is set to Enabled, the mount is made recursively read-only if it is supported by the container runtime, otherwise the pod will not be started and an error will be generated to indicate the reason.  If this field is set to IfPossible or Enabled, MountPropagation must be set to None (or be unspecified, which defaults to None).  If this field is not specified, it is treated as an equivalent of Disabled.",
    )
    subPath: Optional[str] = Field(
        default=None,
        alias="sub_path",
        description="Path within the volume from which the container's volume should be mounted. Defaults to \"\" (volume's root).",
    )
    subPathExpr: Optional[str] = Field(
        default=None,
        alias="sub_path_expr",
        description="Expanded path within the volume from which the container's volume should be mounted. Behaves similarly to SubPath but environment variable references $(VAR_NAME) are expanded using the container's environment. Defaults to \"\" (volume's root). SubPathExpr and SubPath are mutually exclusive.",
    )


class Containers(BaseModel):
    """A single application container that you want to run within a pod."""

    model_config = ConfigDict(extra="forbid")

    args: Optional[List[str]] = Field(
        default=None,
        description='Arguments to the entrypoint. The container image\'s CMD is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    command: Optional[List[str]] = Field(
        default=None,
        description='Entrypoint array. Not executed within a shell. The container image\'s ENTRYPOINT is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    env: Optional[List[Env]] = Field(
        default=None,
        description="List of environment variables to set in the container. Cannot be updated.",
    )
    envFrom: Optional[List[EnvFrom]] = Field(
        default=None,
        alias="env_from",
        description="List of sources to populate environment variables in the container. The keys defined within a source must be a C_IDENTIFIER. All invalid keys will be reported as an event when the container is starting. When a key exists in multiple sources, the value associated with the last source will take precedence. Values defined by an Env with a duplicate key will take precedence. Cannot be updated.",
    )
    image: Optional[str] = Field(
        default=None,
        description="Container image name. More info: https://kubernetes.io/docs/concepts/containers/images This field is optional to allow higher level config management to default or override container images in workload controllers like Deployments and StatefulSets.",
    )
    imagePullPolicy: Optional[str] = Field(
        default=None,
        alias="image_pull_policy",
        description="Image pull policy. One of Always, Never, IfNotPresent. Defaults to Always if :latest tag is specified, or IfNotPresent otherwise. Cannot be updated. More info: https://kubernetes.io/docs/concepts/containers/images#updating-images",
    )
    lifecycle: Optional[Lifecycle] = Field(
        default=None,
        description="Actions that the management system should take in response to container lifecycle events. Cannot be updated.",
    )
    livenessProbe: Optional[LivenessProbe] = Field(
        default=None,
        alias="liveness_probe",
        description="Periodic probe of container liveness. Container will be restarted if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    name: str = Field(
        description="Name of the container specified as a DNS_LABEL. Each container in a pod must have a unique name (DNS_LABEL). Cannot be updated."
    )
    ports: Optional[List[Ports]] = Field(
        default=None,
        description='List of ports to expose from the container. Not specifying a port here DOES NOT prevent that port from being exposed. Any port which is listening on the default "0.0.0.0" address inside a container will be accessible from the network. Modifying this array with strategic merge patch may corrupt the data. For more information See https://github.com/kubernetes/kubernetes/issues/108255. Cannot be updated.',
    )
    readinessProbe: Optional[ReadinessProbe] = Field(
        default=None,
        alias="readiness_probe",
        description="Periodic probe of container service readiness. Container will be removed from service endpoints if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    resizePolicy: Optional[List[ResizePolicy]] = Field(
        default=None,
        alias="resize_policy",
        description="Resources resize policy for the container.",
    )
    resources: Optional[Resources] = Field(
        default=None,
        description="Compute Resources required by this container. Cannot be updated. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )
    restartPolicy: Optional[str] = Field(
        default=None,
        alias="restart_policy",
        description='RestartPolicy defines the restart behavior of individual containers in a pod. This field may only be set for init containers, and the only allowed value is "Always". For non-init containers or when this field is not specified, the restart behavior is defined by the Pod\'s restart policy and the container type. Setting the RestartPolicy as "Always" for the init container will have the following effect: this init container will be continually restarted on exit until all regular containers have terminated. Once all regular containers have completed, all init containers with restartPolicy "Always" will be shut down. This lifecycle differs from normal init containers and is often referred to as a "sidecar" container. Although this init container still starts in the init container sequence, it does not wait for the container to complete before proceeding to the next init container. Instead, the next init container starts immediately after this init container is started, or after any startupProbe has successfully completed.',
    )
    securityContext: Optional[SecurityContext] = Field(
        default=None,
        alias="security_context",
        description="SecurityContext defines the security options the container should be run with. If set, the fields of SecurityContext override the equivalent fields of PodSecurityContext. More info: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/",
    )
    startupProbe: Optional[StartupProbe] = Field(
        default=None,
        alias="startup_probe",
        description="StartupProbe indicates that the Pod has successfully initialized. If specified, no other probes are executed until this completes successfully. If this probe fails, the Pod will be restarted, just as if the livenessProbe failed. This can be used to provide different probe parameters at the beginning of a Pod's lifecycle, when it might take a long time to load data or warm a cache, than during steady-state operation. This cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    stdin: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a buffer for stdin in the container runtime. If this is not set, reads from stdin in the container will always result in EOF. Default is false.",
    )
    stdinOnce: Optional[bool] = Field(
        default=None,
        alias="stdin_once",
        description="Whether the container runtime should close the stdin channel after it has been opened by a single attach. When stdin is true the stdin stream will remain open across multiple attach sessions. If stdinOnce is set to true, stdin is opened on container start, is empty until the first client attaches to stdin, and then remains open and accepts data until the client disconnects, at which time stdin is closed and remains closed until the container is restarted. If this flag is false, a container processes that reads from stdin will never receive an EOF. Default is false",
    )
    terminationMessagePath: Optional[str] = Field(
        default=None,
        alias="termination_message_path",
        description="Optional: Path at which the file to which the container's termination message will be written is mounted into the container's filesystem. Message written is intended to be brief final status, such as an assertion failure message. Will be truncated by the node if greater than 4096 bytes. The total message length across all containers will be limited to 12kb. Defaults to /dev/termination-log. Cannot be updated.",
    )
    terminationMessagePolicy: Optional[str] = Field(
        default=None,
        alias="termination_message_policy",
        description="Indicate how the termination message should be populated. File will use the contents of terminationMessagePath to populate the container status message on both success and failure. FallbackToLogsOnError will use the last chunk of container log output if the termination message file is empty and the container exited with an error. The log output is limited to 2048 bytes or 80 lines, whichever is smaller. Defaults to File. Cannot be updated.",
    )
    tty: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a TTY for itself, also requires 'stdin' to be true. Default is false.",
    )
    volumeDevices: Optional[List[VolumeDevices]] = Field(
        default=None,
        alias="volume_devices",
        description="volumeDevices is the list of block devices to be used by the container.",
    )
    volumeMounts: Optional[List[VolumeMounts]] = Field(
        default=None,
        alias="volume_mounts",
        description="Pod volumes to mount into the container's filesystem. Cannot be updated.",
    )
    workingDir: Optional[str] = Field(
        default=None,
        alias="working_dir",
        description="Container's working directory. If not specified, the container runtime's default will be used, which might be configured in the container image. Cannot be updated.",
    )


class Options(BaseModel):
    """PodDNSConfigOption defines DNS resolver options of a pod."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, description="Required.")
    value: Optional[str] = None


class DnsConfig(BaseModel):
    """Specifies the DNS parameters of a pod. Parameters specified here will be merged to the generated DNS configuration based on DNSPolicy."""

    model_config = ConfigDict(extra="forbid")

    nameservers: Optional[List[str]] = Field(
        default=None,
        description="A list of DNS name server IP addresses. This will be appended to the base nameservers generated from DNSPolicy. Duplicated nameservers will be removed.",
    )
    options: Optional[List[Options]] = Field(
        default=None,
        description="A list of DNS resolver options. This will be merged with the base options generated from DNSPolicy. Duplicated entries will be removed. Resolution options given in Options will override those that appear in the base DNSPolicy.",
    )
    searches: Optional[List[str]] = Field(
        default=None,
        description="A list of DNS search domains for host-name lookup. This will be appended to the base search paths generated from DNSPolicy. Duplicated search paths will be removed.",
    )


class EphemeralContainers(BaseModel):
    """An EphemeralContainer is a temporary container that you may add to an existing Pod for user-initiated activities such as debugging. Ephemeral containers have no resource or scheduling guarantees, and they will not be restarted when they exit or when a Pod is removed or restarted. The kubelet may evict a Pod if an ephemeral container causes the Pod to exceed its resource allocation.  To add an ephemeral container, use the ephemeralcontainers subresource of an existing Pod. Ephemeral containers may not be removed or restarted."""

    model_config = ConfigDict(extra="forbid")

    args: Optional[List[str]] = Field(
        default=None,
        description='Arguments to the entrypoint. The image\'s CMD is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    command: Optional[List[str]] = Field(
        default=None,
        description='Entrypoint array. Not executed within a shell. The image\'s ENTRYPOINT is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    env: Optional[List[Env]] = Field(
        default=None,
        description="List of environment variables to set in the container. Cannot be updated.",
    )
    envFrom: Optional[List[EnvFrom]] = Field(
        default=None,
        alias="env_from",
        description="List of sources to populate environment variables in the container. The keys defined within a source must be a C_IDENTIFIER. All invalid keys will be reported as an event when the container is starting. When a key exists in multiple sources, the value associated with the last source will take precedence. Values defined by an Env with a duplicate key will take precedence. Cannot be updated.",
    )
    image: Optional[str] = Field(
        default=None,
        description="Container image name. More info: https://kubernetes.io/docs/concepts/containers/images",
    )
    imagePullPolicy: Optional[str] = Field(
        default=None,
        alias="image_pull_policy",
        description="Image pull policy. One of Always, Never, IfNotPresent. Defaults to Always if :latest tag is specified, or IfNotPresent otherwise. Cannot be updated. More info: https://kubernetes.io/docs/concepts/containers/images#updating-images",
    )
    lifecycle: Optional[Lifecycle] = Field(
        default=None, description="Lifecycle is not allowed for ephemeral containers."
    )
    livenessProbe: Optional[LivenessProbe] = Field(
        default=None,
        alias="liveness_probe",
        description="Probes are not allowed for ephemeral containers.",
    )
    name: str = Field(
        description="Name of the ephemeral container specified as a DNS_LABEL. This name must be unique among all containers, init containers and ephemeral containers."
    )
    ports: Optional[List[Ports]] = Field(
        default=None, description="Ports are not allowed for ephemeral containers."
    )
    readinessProbe: Optional[ReadinessProbe] = Field(
        default=None,
        alias="readiness_probe",
        description="Probes are not allowed for ephemeral containers.",
    )
    resizePolicy: Optional[List[ResizePolicy]] = Field(
        default=None,
        alias="resize_policy",
        description="Resources resize policy for the container.",
    )
    resources: Optional[Resources] = Field(
        default=None,
        description="Resources are not allowed for ephemeral containers. Ephemeral containers use spare resources already allocated to the pod.",
    )
    restartPolicy: Optional[str] = Field(
        default=None,
        alias="restart_policy",
        description="Restart policy for the container to manage the restart behavior of each container within a pod. This may only be set for init containers. You cannot set this field on ephemeral containers.",
    )
    securityContext: Optional[SecurityContext] = Field(
        default=None,
        alias="security_context",
        description="Optional: SecurityContext defines the security options the ephemeral container should be run with. If set, the fields of SecurityContext override the equivalent fields of PodSecurityContext.",
    )
    startupProbe: Optional[StartupProbe] = Field(
        default=None,
        alias="startup_probe",
        description="Probes are not allowed for ephemeral containers.",
    )
    stdin: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a buffer for stdin in the container runtime. If this is not set, reads from stdin in the container will always result in EOF. Default is false.",
    )
    stdinOnce: Optional[bool] = Field(
        default=None,
        alias="stdin_once",
        description="Whether the container runtime should close the stdin channel after it has been opened by a single attach. When stdin is true the stdin stream will remain open across multiple attach sessions. If stdinOnce is set to true, stdin is opened on container start, is empty until the first client attaches to stdin, and then remains open and accepts data until the client disconnects, at which time stdin is closed and remains closed until the container is restarted. If this flag is false, a container processes that reads from stdin will never receive an EOF. Default is false",
    )
    targetContainerName: Optional[str] = Field(
        default=None,
        alias="target_container_name",
        description="If set, the name of the container from PodSpec that this ephemeral container targets. The ephemeral container will be run in the namespaces (IPC, PID, etc) of this container. If not set then the ephemeral container uses the namespaces configured in the Pod spec.  The container runtime must implement support for this feature. If the runtime does not support namespace targeting then the result of setting this field is undefined.",
    )
    terminationMessagePath: Optional[str] = Field(
        default=None,
        alias="termination_message_path",
        description="Optional: Path at which the file to which the container's termination message will be written is mounted into the container's filesystem. Message written is intended to be brief final status, such as an assertion failure message. Will be truncated by the node if greater than 4096 bytes. The total message length across all containers will be limited to 12kb. Defaults to /dev/termination-log. Cannot be updated.",
    )
    terminationMessagePolicy: Optional[str] = Field(
        default=None,
        alias="termination_message_policy",
        description="Indicate how the termination message should be populated. File will use the contents of terminationMessagePath to populate the container status message on both success and failure. FallbackToLogsOnError will use the last chunk of container log output if the termination message file is empty and the container exited with an error. The log output is limited to 2048 bytes or 80 lines, whichever is smaller. Defaults to File. Cannot be updated.",
    )
    tty: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a TTY for itself, also requires 'stdin' to be true. Default is false.",
    )
    volumeDevices: Optional[List[VolumeDevices]] = Field(
        default=None,
        alias="volume_devices",
        description="volumeDevices is the list of block devices to be used by the container.",
    )
    volumeMounts: Optional[List[VolumeMounts]] = Field(
        default=None,
        alias="volume_mounts",
        description="Pod volumes to mount into the container's filesystem. Subpath mounts are not allowed for ephemeral containers. Cannot be updated.",
    )
    workingDir: Optional[str] = Field(
        default=None,
        alias="working_dir",
        description="Container's working directory. If not specified, the container runtime's default will be used, which might be configured in the container image. Cannot be updated.",
    )


class HostAliases(BaseModel):
    """HostAlias holds the mapping between IP and hostnames that will be injected as an entry in the pod's hosts file."""

    model_config = ConfigDict(extra="forbid")

    hostnames: Optional[List[str]] = Field(
        default=None, description="Hostnames for the above IP address."
    )
    ip: str = Field(description="IP address of the host file entry.")


class ImagePullSecrets(BaseModel):
    """LocalObjectReference contains enough information to let you locate the referenced object inside the same namespace."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )


class InitContainers(BaseModel):
    """A single application container that you want to run within a pod."""

    model_config = ConfigDict(extra="forbid")

    args: Optional[List[str]] = Field(
        default=None,
        description='Arguments to the entrypoint. The container image\'s CMD is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    command: Optional[List[str]] = Field(
        default=None,
        description='Entrypoint array. Not executed within a shell. The container image\'s ENTRYPOINT is used if this is not provided. Variable references $(VAR_NAME) are expanded using the container\'s environment. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Cannot be updated. More info: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell',
    )
    env: Optional[List[Env]] = Field(
        default=None,
        description="List of environment variables to set in the container. Cannot be updated.",
    )
    envFrom: Optional[List[EnvFrom]] = Field(
        default=None,
        alias="env_from",
        description="List of sources to populate environment variables in the container. The keys defined within a source must be a C_IDENTIFIER. All invalid keys will be reported as an event when the container is starting. When a key exists in multiple sources, the value associated with the last source will take precedence. Values defined by an Env with a duplicate key will take precedence. Cannot be updated.",
    )
    image: Optional[str] = Field(
        default=None,
        description="Container image name. More info: https://kubernetes.io/docs/concepts/containers/images This field is optional to allow higher level config management to default or override container images in workload controllers like Deployments and StatefulSets.",
    )
    imagePullPolicy: Optional[str] = Field(
        default=None,
        alias="image_pull_policy",
        description="Image pull policy. One of Always, Never, IfNotPresent. Defaults to Always if :latest tag is specified, or IfNotPresent otherwise. Cannot be updated. More info: https://kubernetes.io/docs/concepts/containers/images#updating-images",
    )
    lifecycle: Optional[Lifecycle] = Field(
        default=None,
        description="Actions that the management system should take in response to container lifecycle events. Cannot be updated.",
    )
    livenessProbe: Optional[LivenessProbe] = Field(
        default=None,
        alias="liveness_probe",
        description="Periodic probe of container liveness. Container will be restarted if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    name: str = Field(
        description="Name of the container specified as a DNS_LABEL. Each container in a pod must have a unique name (DNS_LABEL). Cannot be updated."
    )
    ports: Optional[List[Ports]] = Field(
        default=None,
        description='List of ports to expose from the container. Not specifying a port here DOES NOT prevent that port from being exposed. Any port which is listening on the default "0.0.0.0" address inside a container will be accessible from the network. Modifying this array with strategic merge patch may corrupt the data. For more information See https://github.com/kubernetes/kubernetes/issues/108255. Cannot be updated.',
    )
    readinessProbe: Optional[ReadinessProbe] = Field(
        default=None,
        alias="readiness_probe",
        description="Periodic probe of container service readiness. Container will be removed from service endpoints if the probe fails. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    resizePolicy: Optional[List[ResizePolicy]] = Field(
        default=None,
        alias="resize_policy",
        description="Resources resize policy for the container.",
    )
    resources: Optional[Resources] = Field(
        default=None,
        description="Compute Resources required by this container. Cannot be updated. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )
    restartPolicy: Optional[str] = Field(
        default=None,
        alias="restart_policy",
        description='RestartPolicy defines the restart behavior of individual containers in a pod. This field may only be set for init containers, and the only allowed value is "Always". For non-init containers or when this field is not specified, the restart behavior is defined by the Pod\'s restart policy and the container type. Setting the RestartPolicy as "Always" for the init container will have the following effect: this init container will be continually restarted on exit until all regular containers have terminated. Once all regular containers have completed, all init containers with restartPolicy "Always" will be shut down. This lifecycle differs from normal init containers and is often referred to as a "sidecar" container. Although this init container still starts in the init container sequence, it does not wait for the container to complete before proceeding to the next init container. Instead, the next init container starts immediately after this init container is started, or after any startupProbe has successfully completed.',
    )
    securityContext: Optional[SecurityContext] = Field(
        default=None,
        alias="security_context",
        description="SecurityContext defines the security options the container should be run with. If set, the fields of SecurityContext override the equivalent fields of PodSecurityContext. More info: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/",
    )
    startupProbe: Optional[StartupProbe] = Field(
        default=None,
        alias="startup_probe",
        description="StartupProbe indicates that the Pod has successfully initialized. If specified, no other probes are executed until this completes successfully. If this probe fails, the Pod will be restarted, just as if the livenessProbe failed. This can be used to provide different probe parameters at the beginning of a Pod's lifecycle, when it might take a long time to load data or warm a cache, than during steady-state operation. This cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle#container-probes",
    )
    stdin: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a buffer for stdin in the container runtime. If this is not set, reads from stdin in the container will always result in EOF. Default is false.",
    )
    stdinOnce: Optional[bool] = Field(
        default=None,
        alias="stdin_once",
        description="Whether the container runtime should close the stdin channel after it has been opened by a single attach. When stdin is true the stdin stream will remain open across multiple attach sessions. If stdinOnce is set to true, stdin is opened on container start, is empty until the first client attaches to stdin, and then remains open and accepts data until the client disconnects, at which time stdin is closed and remains closed until the container is restarted. If this flag is false, a container processes that reads from stdin will never receive an EOF. Default is false",
    )
    terminationMessagePath: Optional[str] = Field(
        default=None,
        alias="termination_message_path",
        description="Optional: Path at which the file to which the container's termination message will be written is mounted into the container's filesystem. Message written is intended to be brief final status, such as an assertion failure message. Will be truncated by the node if greater than 4096 bytes. The total message length across all containers will be limited to 12kb. Defaults to /dev/termination-log. Cannot be updated.",
    )
    terminationMessagePolicy: Optional[str] = Field(
        default=None,
        alias="termination_message_policy",
        description="Indicate how the termination message should be populated. File will use the contents of terminationMessagePath to populate the container status message on both success and failure. FallbackToLogsOnError will use the last chunk of container log output if the termination message file is empty and the container exited with an error. The log output is limited to 2048 bytes or 80 lines, whichever is smaller. Defaults to File. Cannot be updated.",
    )
    tty: Optional[bool] = Field(
        default=None,
        description="Whether this container should allocate a TTY for itself, also requires 'stdin' to be true. Default is false.",
    )
    volumeDevices: Optional[List[VolumeDevices]] = Field(
        default=None,
        alias="volume_devices",
        description="volumeDevices is the list of block devices to be used by the container.",
    )
    volumeMounts: Optional[List[VolumeMounts]] = Field(
        default=None,
        alias="volume_mounts",
        description="Pod volumes to mount into the container's filesystem. Cannot be updated.",
    )
    workingDir: Optional[str] = Field(
        default=None,
        alias="working_dir",
        description="Container's working directory. If not specified, the container runtime's default will be used, which might be configured in the container image. Cannot be updated.",
    )


class Os(BaseModel):
    """Specifies the OS of the containers in the pod. Some pod and container fields are restricted if this is set.  If the OS field is set to linux, the following fields must be unset: -securityContext.windowsOptions  If the OS field is set to windows, following fields must be unset: - spec.hostPID - spec.hostIPC - spec.hostUsers - spec.securityContext.appArmorProfile - spec.securityContext.seLinuxOptions - spec.securityContext.seccompProfile - spec.securityContext.fsGroup - spec.securityContext.fsGroupChangePolicy - spec.securityContext.sysctls - spec.shareProcessNamespace - spec.securityContext.runAsUser - spec.securityContext.runAsGroup - spec.securityContext.supplementalGroups - spec.securityContext.supplementalGroupsPolicy - spec.containers[*].securityContext.appArmorProfile - spec.containers[*].securityContext.seLinuxOptions - spec.containers[*].securityContext.seccompProfile - spec.containers[*].securityContext.capabilities - spec.containers[*].securityContext.readOnlyRootFilesystem - spec.containers[*].securityContext.privileged - spec.containers[*].securityContext.allowPrivilegeEscalation - spec.containers[*].securityContext.procMount - spec.containers[*].securityContext.runAsUser - spec.containers[*].securityContext.runAsGroup"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name is the name of the operating system. The currently supported values are linux and windows. Additional value may be defined in future and can be one of: https://github.com/opencontainers/runtime-spec/blob/master/config.md#platform-specific-configuration Clients should expect to handle additional values and treat unrecognized values in this field as os: null"
    )


class ReadinessGates(BaseModel):
    """PodReadinessGate contains the reference to a pod condition"""

    model_config = ConfigDict(extra="forbid")

    conditionType: str = Field(
        alias="condition_type",
        description="ConditionType refers to a condition in the pod's condition list with matching type.",
    )


class ResourceClaims(BaseModel):
    """PodResourceClaim references exactly one ResourceClaim, either directly or by naming a ResourceClaimTemplate which is then turned into a ResourceClaim for the pod.  It adds a name to it that uniquely identifies the ResourceClaim inside the Pod. Containers that need access to the ResourceClaim reference it with this name."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name uniquely identifies this resource claim inside the pod. This must be a DNS_LABEL."
    )
    resourceClaimName: Optional[str] = Field(
        default=None,
        alias="resource_claim_name",
        description="ResourceClaimName is the name of a ResourceClaim object in the same namespace as this pod.  Exactly one of ResourceClaimName and ResourceClaimTemplateName must be set.",
    )
    resourceClaimTemplateName: Optional[str] = Field(
        default=None,
        alias="resource_claim_template_name",
        description="ResourceClaimTemplateName is the name of a ResourceClaimTemplate object in the same namespace as this pod.  The template will be used to create a new ResourceClaim, which will be bound to this pod. When this pod is deleted, the ResourceClaim will also be deleted. The pod name and resource name, along with a generated component, will be used to form a unique name for the ResourceClaim, which will be recorded in pod.status.resourceClaimStatuses.  This field is immutable and no changes will be made to the corresponding ResourceClaim by the control plane after creating the ResourceClaim.  Exactly one of ResourceClaimName and ResourceClaimTemplateName must be set.",
    )


class SchedulingGates(BaseModel):
    """PodSchedulingGate is associated to a Pod to guard its scheduling."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name of the scheduling gate. Each scheduling gate must have a unique name field."
    )


class LabelSelector(BaseModel):
    """LabelSelector is used to find matching pods. Pods that match this label selector are counted to determine the number of pods in their corresponding topology domain."""

    model_config = ConfigDict(extra="forbid")

    matchExpressions: Optional[List[MatchExpressions]] = Field(
        default=None,
        alias="match_expressions",
        description="matchExpressions is a list of label selector requirements. The requirements are ANDed.",
    )
    matchLabels: Optional[Dict[str, str]] = Field(
        default=None,
        alias="match_labels",
        description='matchLabels is a map of {key,value} pairs. A single {key,value} in the matchLabels map is equivalent to an element of matchExpressions, whose key field is "key", the operator is "In", and the values array contains only "value". The requirements are ANDed.',
    )


class NamespaceSelector(BaseModel):
    """A label query over the set of namespaces that the term applies to. The term is applied to the union of the namespaces selected by this field and the ones listed in the namespaces field. null selector and null or empty namespaces list means "this pod's namespace". An empty selector ({}) matches all namespaces."""

    model_config = ConfigDict(extra="forbid")

    matchExpressions: Optional[List[MatchExpressions]] = Field(
        default=None,
        alias="match_expressions",
        description="matchExpressions is a list of label selector requirements. The requirements are ANDed.",
    )
    matchLabels: Optional[Dict[str, str]] = Field(
        default=None,
        alias="match_labels",
        description='matchLabels is a map of {key,value} pairs. A single {key,value} in the matchLabels map is equivalent to an element of matchExpressions, whose key field is "key", the operator is "In", and the values array contains only "value". The requirements are ANDed.',
    )


class TopologySpreadConstraints(BaseModel):
    """TopologySpreadConstraint specifies how to spread matching pods among the given topology."""

    model_config = ConfigDict(extra="forbid")

    labelSelector: Optional[LabelSelector] = Field(
        default=None,
        alias="label_selector",
        description="LabelSelector is used to find matching pods. Pods that match this label selector are counted to determine the number of pods in their corresponding topology domain.",
    )
    matchLabelKeys: Optional[List[str]] = Field(
        default=None,
        alias="match_label_keys",
        description="MatchLabelKeys is a set of pod label keys to select the pods over which spreading will be calculated. The keys are used to lookup values from the incoming pod labels, those key-value labels are ANDed with labelSelector to select the group of existing pods over which spreading will be calculated for the incoming pod. The same key is forbidden to exist in both MatchLabelKeys and LabelSelector. MatchLabelKeys cannot be set when LabelSelector isn't set. Keys that don't exist in the incoming pod labels will be ignored. A null or empty list means only match against labelSelector.  This is a beta field and requires the MatchLabelKeysInPodTopologySpread feature gate to be enabled (enabled by default).",
    )
    maxSkew: int = Field(
        alias="max_skew",
        description="MaxSkew describes the degree to which pods may be unevenly distributed. When `whenUnsatisfiable=DoNotSchedule`, it is the maximum permitted difference between the number of matching pods in the target topology and the global minimum. The global minimum is the minimum number of matching pods in an eligible domain or zero if the number of eligible domains is less than MinDomains. For example, in a 3-zone cluster, MaxSkew is set to 1, and pods with the same labelSelector spread as 2/2/1: In this case, the global minimum is 1. | zone1 | zone2 | zone3 | |  P P  |  P P  |   P   | - if MaxSkew is 1, incoming pod can only be scheduled to zone3 to become 2/2/2; scheduling it onto zone1(zone2) would make the ActualSkew(3-1) on zone1(zone2) violate MaxSkew(1). - if MaxSkew is 2, incoming pod can be scheduled onto any zone. When `whenUnsatisfiable=ScheduleAnyway`, it is used to give higher precedence to topologies that satisfy it. It's a required field. Default value is 1 and 0 is not allowed.",
    )
    minDomains: Optional[int] = Field(
        default=None,
        alias="min_domains",
        description='MinDomains indicates a minimum number of eligible domains. When the number of eligible domains with matching topology keys is less than minDomains, Pod Topology Spread treats "global minimum" as 0, and then the calculation of Skew is performed. And when the number of eligible domains with matching topology keys equals or greater than minDomains, this value has no effect on scheduling. As a result, when the number of eligible domains is less than minDomains, scheduler won\'t schedule more than maxSkew Pods to those domains. If value is nil, the constraint behaves as if MinDomains is equal to 1. Valid values are integers greater than 0. When value is not nil, WhenUnsatisfiable must be DoNotSchedule.  For example, in a 3-zone cluster, MaxSkew is set to 2, MinDomains is set to 5 and pods with the same labelSelector spread as 2/2/2: | zone1 | zone2 | zone3 | |  P P  |  P P  |  P P  | The number of domains is less than 5(MinDomains), so "global minimum" is treated as 0. In this situation, new pod with the same labelSelector cannot be scheduled, because computed skew will be 3(3 - 0) if new Pod is scheduled to any of the three zones, it will violate MaxSkew.',
    )
    nodeAffinityPolicy: Optional[str] = Field(
        default=None,
        alias="node_affinity_policy",
        description="NodeAffinityPolicy indicates how we will treat Pod's nodeAffinity/nodeSelector when calculating pod topology spread skew. Options are: - Honor: only nodes matching nodeAffinity/nodeSelector are included in the calculations. - Ignore: nodeAffinity/nodeSelector are ignored. All nodes are included in the calculations.  If this value is nil, the behavior is equivalent to the Honor policy. This is a beta-level feature default enabled by the NodeInclusionPolicyInPodTopologySpread feature flag.",
    )
    nodeTaintsPolicy: Optional[str] = Field(
        default=None,
        alias="node_taints_policy",
        description="NodeTaintsPolicy indicates how we will treat node taints when calculating pod topology spread skew. Options are: - Honor: nodes without taints, along with tainted nodes for which the incoming pod has a toleration, are included. - Ignore: node taints are ignored. All nodes are included.  If this value is nil, the behavior is equivalent to the Ignore policy. This is a beta-level feature default enabled by the NodeInclusionPolicyInPodTopologySpread feature flag.",
    )
    topologyKey: str = Field(
        alias="topology_key",
        description='TopologyKey is the key of node labels. Nodes that have a label with this key and identical values are considered to be in the same topology. We consider each <key, value> as a "bucket", and try to put balanced number of pods into each bucket. We define a domain as a particular instance of a topology. Also, we define an eligible domain as a domain whose nodes meet the requirements of nodeAffinityPolicy and nodeTaintsPolicy. e.g. If TopologyKey is "kubernetes.io/hostname", each Node is a domain of that topology. And, if TopologyKey is "topology.kubernetes.io/zone", each zone is a domain of that topology. It\'s a required field.',
    )
    whenUnsatisfiable: str = Field(
        alias="when_unsatisfiable",
        description='WhenUnsatisfiable indicates how to deal with a pod if it doesn\'t satisfy the spread constraint. - DoNotSchedule (default) tells the scheduler not to schedule it. - ScheduleAnyway tells the scheduler to schedule the pod in any location,   but giving higher precedence to topologies that would help reduce the   skew. A constraint is considered "Unsatisfiable" for an incoming pod if and only if every possible node assignment for that pod would violate "MaxSkew" on some topology. For example, in a 3-zone cluster, MaxSkew is set to 1, and pods with the same labelSelector spread as 3/1/1: | zone1 | zone2 | zone3 | | P P P |   P   |   P   | If WhenUnsatisfiable is set to DoNotSchedule, incoming pod can only be scheduled to zone2(zone3) to become 3/2/1(3/1/2) as ActualSkew(2-1) on zone2(zone3) satisfies MaxSkew(1). In other words, the cluster can still be imbalanced, but scheduler won\'t make it *more* imbalanced. It\'s a required field.',
    )


class AwsElasticBlockStore(BaseModel):
    """awsElasticBlockStore represents an AWS Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes#awselasticblockstore"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type of the volume that you want to mount. Tip: Ensure that the filesystem type is supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://kubernetes.io/docs/concepts/storage/volumes#awselasticblockstore',
    )
    partition: Optional[int] = Field(
        default=None,
        description='partition is the partition in the volume that you want to mount. If omitted, the default is to mount by volume name. Examples: For volume /dev/sda1, you specify the partition as "1". Similarly, the volume partition for /dev/sda is "0" (or you can leave the property empty).',
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly value true will force the readOnly setting in VolumeMounts. More info: https://kubernetes.io/docs/concepts/storage/volumes#awselasticblockstore",
    )
    volumeID: str = Field(
        alias="volume_id",
        description="volumeID is unique ID of the persistent disk resource in AWS (Amazon EBS volume). More info: https://kubernetes.io/docs/concepts/storage/volumes#awselasticblockstore",
    )


class AzureDisk(BaseModel):
    """azureDisk represents an Azure Data Disk mount on the host and bind mount to the pod."""

    model_config = ConfigDict(extra="forbid")

    cachingMode: Optional[str] = Field(
        default=None,
        alias="caching_mode",
        description="cachingMode is the Host Caching mode: None, Read Only, Read Write.",
    )
    diskName: str = Field(
        alias="disk_name",
        description="diskName is the Name of the data disk in the blob storage",
    )
    diskURI: str = Field(
        alias="disk_uri",
        description="diskURI is the URI of data disk in the blob storage",
    )
    fsType: Optional[str] = Field(
        default="ext4",
        alias="fs_type",
        description='fsType is Filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    kind: Optional[str] = Field(
        default=None,
        description="kind expected values are Shared: multiple blob disks per storage account  Dedicated: single blob disk per storage account  Managed: azure managed data disk (only in managed availability set). defaults to shared",
    )
    readOnly: Optional[bool] = Field(
        default=False,
        alias="read_only",
        description="readOnly Defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )


class AzureFile(BaseModel):
    """azureFile represents an Azure File Service mount on the host and bind mount to the pod."""

    model_config = ConfigDict(extra="forbid")

    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    secretName: str = Field(
        alias="secret_name",
        description="secretName is the  name of secret that contains Azure Storage Account Name and Key",
    )
    shareName: str = Field(
        alias="share_name", description="shareName is the azure share Name"
    )


class Cephfs(BaseModel):
    """cephFS represents a Ceph FS mount on the host that shares a pod's lifetime"""

    model_config = ConfigDict(extra="forbid")

    monitors: List[str] = Field(
        description="monitors is Required: Monitors is a collection of Ceph monitors More info: https://examples.k8s.io/volumes/cephfs/README.md#how-to-use-it"
    )
    path: Optional[str] = Field(
        default=None,
        description="path is Optional: Used as the mounted root, rather than the full Ceph tree, default is /",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly is Optional: Defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts. More info: https://examples.k8s.io/volumes/cephfs/README.md#how-to-use-it",
    )
    secretFile: Optional[str] = Field(
        default=None,
        alias="secret_file",
        description="secretFile is Optional: SecretFile is the path to key ring for User, default is /etc/ceph/user.secret More info: https://examples.k8s.io/volumes/cephfs/README.md#how-to-use-it",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef is Optional: SecretRef is reference to the authentication secret for User, default is empty. More info: https://examples.k8s.io/volumes/cephfs/README.md#how-to-use-it",
    )
    user: Optional[str] = Field(
        default=None,
        description="user is optional: User is the rados user name, default is admin More info: https://examples.k8s.io/volumes/cephfs/README.md#how-to-use-it",
    )


class Cinder(BaseModel):
    """cinder represents a cinder volume attached and mounted on kubelets host machine. More info: https://examples.k8s.io/mysql-cinder-pd/README.md"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://examples.k8s.io/mysql-cinder-pd/README.md',
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts. More info: https://examples.k8s.io/mysql-cinder-pd/README.md",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef is optional: points to a secret object containing parameters used to connect to OpenStack.",
    )
    volumeID: str = Field(
        alias="volume_id",
        description="volumeID used to identify the volume in cinder. More info: https://examples.k8s.io/mysql-cinder-pd/README.md",
    )


class Items(BaseModel):
    """Maps a string key to a path within a volume."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="key is the key to project.")
    mode: Optional[int] = Field(
        default=None,
        description="mode is Optional: mode bits used to set permissions on this file. Must be an octal value between 0000 and 0777 or a decimal value between 0 and 511. YAML accepts both octal and decimal values, JSON requires decimal values for mode bits. If not specified, the volume defaultMode will be used. This might be in conflict with other options that affect the file mode, like fsGroup, and the result can be other mode bits set.",
    )
    path: str = Field(
        description="path is the relative path of the file to map the key to. May not be an absolute path. May not contain the path element '..'. May not start with the string '..'."
    )


class ConfigMap(BaseModel):
    """configMap represents a configMap that should populate this volume"""

    model_config = ConfigDict(extra="forbid")

    defaultMode: Optional[int] = Field(
        default=None,
        alias="default_mode",
        description="defaultMode is optional: mode bits used to set permissions on created files by default. Must be an octal value between 0000 and 0777 or a decimal value between 0 and 511. YAML accepts both octal and decimal values, JSON requires decimal values for mode bits. Defaults to 0644. Directories within the path are not affected by this setting. This might be in conflict with other options that affect the file mode, like fsGroup, and the result can be other mode bits set.",
    )
    items: Optional[List[Items]] = Field(
        default=None,
        description="items if unspecified, each key-value pair in the Data field of the referenced ConfigMap will be projected into the volume as a file whose name is the key and content is the value. If specified, the listed keys will be projected into the specified paths, and unlisted keys will not be present. If a key is specified which is not present in the ConfigMap, the volume setup will error unless it is marked optional. Paths must be relative and may not contain the '..' path or start with '..'.",
    )
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="optional specify whether the ConfigMap or its keys must be defined",
    )


class NodePublishSecretRef(BaseModel):
    """nodePublishSecretRef is a reference to the secret object containing sensitive information to pass to the CSI driver to complete the CSI NodePublishVolume and NodeUnpublishVolume calls. This field is optional, and  may be empty if no secret is required. If the secret object contains more than one secret, all secret references are passed."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )


class Csi(BaseModel):
    """csi (Container Storage Interface) represents ephemeral storage that is handled by certain external CSI drivers (Beta feature)."""

    model_config = ConfigDict(extra="forbid")

    driver: str = Field(
        description="driver is the name of the CSI driver that handles this volume. Consult with your admin for the correct name as registered in the cluster."
    )
    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType to mount. Ex. "ext4", "xfs", "ntfs". If not provided, the empty value is passed to the associated CSI driver which will determine the default filesystem to apply.',
    )
    nodePublishSecretRef: Optional[NodePublishSecretRef] = Field(
        default=None,
        alias="node_publish_secret_ref",
        description="nodePublishSecretRef is a reference to the secret object containing sensitive information to pass to the CSI driver to complete the CSI NodePublishVolume and NodeUnpublishVolume calls. This field is optional, and  may be empty if no secret is required. If the secret object contains more than one secret, all secret references are passed.",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly specifies a read-only configuration for the volume. Defaults to false (read/write).",
    )
    volumeAttributes: Optional[Dict[str, str]] = Field(
        default=None,
        alias="volume_attributes",
        description="volumeAttributes stores driver-specific properties that are passed to the CSI driver. Consult your driver's documentation for supported values.",
    )


class DownwardApi(BaseModel):
    """downwardAPI represents downward API about the pod that should populate this volume"""

    model_config = ConfigDict(extra="forbid")

    defaultMode: Optional[int] = Field(
        default=None,
        alias="default_mode",
        description="Optional: mode bits to use on created files by default. Must be a Optional: mode bits used to set permissions on created files by default. Must be an octal value between 0000 and 0777 or a decimal value between 0 and 511. YAML accepts both octal and decimal values, JSON requires decimal values for mode bits. Defaults to 0644. Directories within the path are not affected by this setting. This might be in conflict with other options that affect the file mode, like fsGroup, and the result can be other mode bits set.",
    )
    items: Optional[List[Items]] = Field(
        default=None, description="Items is a list of downward API volume file"
    )


class EmptyDir(BaseModel):
    """emptyDir represents a temporary directory that shares a pod's lifetime. More info: https://kubernetes.io/docs/concepts/storage/volumes#emptydir"""

    model_config = ConfigDict(extra="forbid")

    medium: Optional[str] = Field(
        default=None,
        description='medium represents what type of storage medium should back this directory. The default is "" which means to use the node\'s default medium. Must be an empty string (default) or Memory. More info: https://kubernetes.io/docs/concepts/storage/volumes#emptydir',
    )
    sizeLimit: Optional[Union[int, str]] = Field(
        default=None,
        alias="size_limit",
        description="sizeLimit is the total amount of local storage required for this EmptyDir volume. The size limit is also applicable for memory medium. The maximum usage on memory medium EmptyDir would be the minimum value between the SizeLimit specified here and the sum of memory limits of all containers in a pod. The default is nil which means that the limit is undefined. More info: https://kubernetes.io/docs/concepts/storage/volumes#emptydir",
    )


class DataSource(BaseModel):
    """dataSource field can be used to specify either: * An existing VolumeSnapshot object (snapshot.storage.k8s.io/VolumeSnapshot) * An existing PVC (PersistentVolumeClaim) If the provisioner or an external controller can support the specified data source, it will create a new volume based on the contents of the specified data source. When the AnyVolumeDataSource feature gate is enabled, dataSource contents will be copied to dataSourceRef, and dataSourceRef contents will be copied to dataSource when dataSourceRef.namespace is not specified. If the namespace is specified, then dataSourceRef will not be copied to dataSource."""

    model_config = ConfigDict(extra="forbid")

    apiGroup: Optional[str] = Field(
        default=None,
        alias="api_group",
        description="APIGroup is the group for the resource being referenced. If APIGroup is not specified, the specified Kind must be in the core API group. For any other third-party types, APIGroup is required.",
    )
    kind: str = Field(description="Kind is the type of resource being referenced")
    name: str = Field(description="Name is the name of resource being referenced")


class DataSourceRef(BaseModel):
    """dataSourceRef specifies the object from which to populate the volume with data, if a non-empty volume is desired. This may be any object from a non-empty API group (non core object) or a PersistentVolumeClaim object. When this field is specified, volume binding will only succeed if the type of the specified object matches some installed volume populator or dynamic provisioner. This field will replace the functionality of the dataSource field and as such if both fields are non-empty, they must have the same value. For backwards compatibility, when namespace isn't specified in dataSourceRef, both fields (dataSource and dataSourceRef) will be set to the same value automatically if one of them is empty and the other is non-empty. When namespace is specified in dataSourceRef, dataSource isn't set to the same value and must be empty. There are three important differences between dataSource and dataSourceRef: * While dataSource only allows two specific types of objects, dataSourceRef   allows any non-core object, as well as PersistentVolumeClaim objects. * While dataSource ignores disallowed values (dropping them), dataSourceRef   preserves all values, and generates an error if a disallowed value is   specified. * While dataSource only allows local objects, dataSourceRef allows objects   in any namespaces. (Beta) Using this field requires the AnyVolumeDataSource feature gate to be enabled. (Alpha) Using the namespace field of dataSourceRef requires the CrossNamespaceVolumeDataSource feature gate to be enabled."""

    model_config = ConfigDict(extra="forbid")

    apiGroup: Optional[str] = Field(
        default=None,
        alias="api_group",
        description="APIGroup is the group for the resource being referenced. If APIGroup is not specified, the specified Kind must be in the core API group. For any other third-party types, APIGroup is required.",
    )
    kind: str = Field(description="Kind is the type of resource being referenced")
    name: str = Field(description="Name is the name of resource being referenced")
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace is the namespace of resource being referenced Note that when a namespace is specified, a gateway.networking.k8s.io/ReferenceGrant object is required in the referent namespace to allow that namespace's owner to accept the reference. See the ReferenceGrant documentation for details. (Alpha) This field requires the CrossNamespaceVolumeDataSource feature gate to be enabled.",
    )


class Selector(BaseModel):
    """selector is a label query over volumes to consider for binding."""

    model_config = ConfigDict(extra="forbid")

    matchExpressions: Optional[List[MatchExpressions]] = Field(
        default=None,
        alias="match_expressions",
        description="matchExpressions is a list of label selector requirements. The requirements are ANDed.",
    )
    matchLabels: Optional[Dict[str, str]] = Field(
        default=None,
        alias="match_labels",
        description='matchLabels is a map of {key,value} pairs. A single {key,value} in the matchLabels map is equivalent to an element of matchExpressions, whose key field is "key", the operator is "In", and the values array contains only "value". The requirements are ANDed.',
    )


class VolumeClaimTemplateSpec(BaseModel):
    """The specification for the PersistentVolumeClaim. The entire content is copied unchanged into the PVC that gets created from this template. The same fields as in a PersistentVolumeClaim are also valid here."""

    model_config = ConfigDict(extra="forbid")

    accessModes: Optional[List[str]] = Field(
        default=None,
        alias="access_modes",
        description="accessModes contains the desired access modes the volume should have. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#access-modes-1",
    )
    dataSource: Optional[DataSource] = Field(
        default=None,
        alias="data_source",
        description="dataSource field can be used to specify either: * An existing VolumeSnapshot object (snapshot.storage.k8s.io/VolumeSnapshot) * An existing PVC (PersistentVolumeClaim) If the provisioner or an external controller can support the specified data source, it will create a new volume based on the contents of the specified data source. When the AnyVolumeDataSource feature gate is enabled, dataSource contents will be copied to dataSourceRef, and dataSourceRef contents will be copied to dataSource when dataSourceRef.namespace is not specified. If the namespace is specified, then dataSourceRef will not be copied to dataSource.",
    )
    dataSourceRef: Optional[DataSourceRef] = Field(
        default=None,
        alias="data_source_ref",
        description="dataSourceRef specifies the object from which to populate the volume with data, if a non-empty volume is desired. This may be any object from a non-empty API group (non core object) or a PersistentVolumeClaim object. When this field is specified, volume binding will only succeed if the type of the specified object matches some installed volume populator or dynamic provisioner. This field will replace the functionality of the dataSource field and as such if both fields are non-empty, they must have the same value. For backwards compatibility, when namespace isn't specified in dataSourceRef, both fields (dataSource and dataSourceRef) will be set to the same value automatically if one of them is empty and the other is non-empty. When namespace is specified in dataSourceRef, dataSource isn't set to the same value and must be empty. There are three important differences between dataSource and dataSourceRef: * While dataSource only allows two specific types of objects, dataSourceRef   allows any non-core object, as well as PersistentVolumeClaim objects. * While dataSource ignores disallowed values (dropping them), dataSourceRef   preserves all values, and generates an error if a disallowed value is   specified. * While dataSource only allows local objects, dataSourceRef allows objects   in any namespaces. (Beta) Using this field requires the AnyVolumeDataSource feature gate to be enabled. (Alpha) Using the namespace field of dataSourceRef requires the CrossNamespaceVolumeDataSource feature gate to be enabled.",
    )
    resources: Optional[Resources] = Field(
        default=None,
        description="resources represents the minimum resources the volume should have. If RecoverVolumeExpansionFailure feature is enabled users are allowed to specify resource requirements that are lower than previous value but must still be higher than capacity recorded in the status field of the claim. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#resources",
    )
    selector: Optional[Selector] = Field(
        default=None,
        description="selector is a label query over volumes to consider for binding.",
    )
    storageClassName: Optional[str] = Field(
        default=None,
        alias="storage_class_name",
        description="storageClassName is the name of the StorageClass required by the claim. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#class-1",
    )
    volumeAttributesClassName: Optional[str] = Field(
        default=None,
        alias="volume_attributes_class_name",
        description="volumeAttributesClassName may be used to set the VolumeAttributesClass used by this claim. If specified, the CSI driver will create or update the volume with the attributes defined in the corresponding VolumeAttributesClass. This has a different purpose than storageClassName, it can be changed after the claim is created. An empty string value means that no VolumeAttributesClass will be applied to the claim but it's not allowed to reset this field to empty string once it is set. If unspecified and the PersistentVolumeClaim is unbound, the default VolumeAttributesClass will be set by the persistentvolume controller if it exists. If the resource referred to by volumeAttributesClass does not exist, this PersistentVolumeClaim will be set to a Pending state, as reflected by the modifyVolumeStatus field, until such as a resource exists. More info: https://kubernetes.io/docs/concepts/storage/volume-attributes-classes/ (Beta) Using this field requires the VolumeAttributesClass feature gate to be enabled (off by default).",
    )
    volumeMode: Optional[str] = Field(
        default=None,
        alias="volume_mode",
        description="volumeMode defines what type of volume is required by the claim. Value of Filesystem is implied when not included in claim spec.",
    )
    volumeName: Optional[str] = Field(
        default=None,
        alias="volume_name",
        description="volumeName is the binding reference to the PersistentVolume backing this claim.",
    )


class VolumeClaimTemplate(BaseModel):
    """Will be used to create a stand-alone PVC to provision the volume. The pod in which this EphemeralVolumeSource is embedded will be the owner of the PVC, i.e. the PVC will be deleted together with the pod.  The name of the PVC will be `<pod name>-<volume name>` where `<volume name>` is the name from the `PodSpec.Volumes` array entry. Pod validation will reject the pod if the concatenated name is not valid for a PVC (for example, too long).  An existing PVC with that name that is not owned by the pod will *not* be used for the pod to avoid using an unrelated volume by mistake. Starting the pod is then blocked until the unrelated PVC is removed. If such a pre-created PVC is meant to be used by the pod, the PVC has to updated with an owner reference to the pod once the pod exists. Normally this should not be necessary, but it may be useful when manually reconstructing a broken cluster.  This field is read-only and no changes will be made by Kubernetes to the PVC after it has been created.  Required, must not be nil."""

    model_config = ConfigDict(extra="forbid")

    metadata: Optional[Metadata] = Field(
        default=None,
        description="May contain labels and annotations that will be copied into the PVC when creating it. No other fields are allowed and will be rejected during validation.",
    )
    volumeClaimTemplateSpec: VolumeClaimTemplateSpec = Field(
        alias="volume_claim_template_spec",
        description="The specification for the PersistentVolumeClaim. The entire content is copied unchanged into the PVC that gets created from this template. The same fields as in a PersistentVolumeClaim are also valid here.",
    )


class Ephemeral(BaseModel):
    """ephemeral represents a volume that is handled by a cluster storage driver. The volume's lifecycle is tied to the pod that defines it - it will be created before the pod starts, and deleted when the pod is removed.  Use this if: a) the volume is only needed while the pod runs, b) features of normal volumes like restoring from snapshot or capacity    tracking are needed, c) the storage driver is specified through a storage class, and d) the storage driver supports dynamic volume provisioning through    a PersistentVolumeClaim (see EphemeralVolumeSource for more    information on the connection between this volume type    and PersistentVolumeClaim).  Use PersistentVolumeClaim or one of the vendor-specific APIs for volumes that persist for longer than the lifecycle of an individual pod.  Use CSI for light-weight local ephemeral volumes if the CSI driver is meant to be used that way - see the documentation of the driver for more information.  A pod can use both types of ephemeral volumes and persistent volumes at the same time."""

    model_config = ConfigDict(extra="forbid")

    volumeClaimTemplate: Optional[VolumeClaimTemplate] = Field(
        default=None,
        alias="volume_claim_template",
        description="Will be used to create a stand-alone PVC to provision the volume. The pod in which this EphemeralVolumeSource is embedded will be the owner of the PVC, i.e. the PVC will be deleted together with the pod.  The name of the PVC will be `<pod name>-<volume name>` where `<volume name>` is the name from the `PodSpec.Volumes` array entry. Pod validation will reject the pod if the concatenated name is not valid for a PVC (for example, too long).  An existing PVC with that name that is not owned by the pod will *not* be used for the pod to avoid using an unrelated volume by mistake. Starting the pod is then blocked until the unrelated PVC is removed. If such a pre-created PVC is meant to be used by the pod, the PVC has to updated with an owner reference to the pod once the pod exists. Normally this should not be necessary, but it may be useful when manually reconstructing a broken cluster.  This field is read-only and no changes will be made by Kubernetes to the PVC after it has been created.  Required, must not be nil.",
    )


class Fc(BaseModel):
    """fc represents a Fibre Channel resource that is attached to a kubelet's host machine and then exposed to the pod."""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    lun: Optional[int] = Field(
        default=None, description="lun is Optional: FC target lun number"
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly is Optional: Defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    targetWWNs: Optional[List[str]] = Field(
        default=None,
        alias="target_wwns",
        description="targetWWNs is Optional: FC target worldwide names (WWNs)",
    )
    wwids: Optional[List[str]] = Field(
        default=None,
        description="wwids Optional: FC volume world wide identifiers (wwids) Either wwids or combination of targetWWNs and lun must be set, but not both simultaneously.",
    )


class FlexVolume(BaseModel):
    """flexVolume represents a generic volume resource that is provisioned/attached using an exec based plugin."""

    model_config = ConfigDict(extra="forbid")

    driver: str = Field(
        description="driver is the name of the driver to use for this volume."
    )
    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". The default filesystem depends on FlexVolume script.',
    )
    options: Optional[Dict[str, str]] = Field(
        default=None,
        description="options is Optional: this field holds extra command options if any.",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly is Optional: defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef is Optional: secretRef is reference to the secret object containing sensitive information to pass to the plugin scripts. This may be empty if no secret object is specified. If the secret object contains more than one secret, all secrets are passed to the plugin scripts.",
    )


class Flocker(BaseModel):
    """flocker represents a Flocker volume attached to a kubelet's host machine. This depends on the Flocker control service being running"""

    model_config = ConfigDict(extra="forbid")

    datasetName: Optional[str] = Field(
        default=None,
        alias="dataset_name",
        description="datasetName is Name of the dataset stored as metadata -> name on the dataset for Flocker should be considered as deprecated",
    )
    datasetUUID: Optional[str] = Field(
        default=None,
        alias="dataset_uuid",
        description="datasetUUID is the UUID of the dataset. This is unique identifier of a Flocker dataset",
    )


class GcePersistentDisk(BaseModel):
    """gcePersistentDisk represents a GCE Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is filesystem type of the volume that you want to mount. Tip: Ensure that the filesystem type is supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk',
    )
    partition: Optional[int] = Field(
        default=None,
        description='partition is the partition in the volume that you want to mount. If omitted, the default is to mount by volume name. Examples: For volume /dev/sda1, you specify the partition as "1". Similarly, the volume partition for /dev/sda is "0" (or you can leave the property empty). More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk',
    )
    pdName: str = Field(
        alias="pd_name",
        description="pdName is unique name of the PD resource in GCE. Used to identify the disk in GCE. More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the ReadOnly setting in VolumeMounts. Defaults to false. More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk",
    )


class GitRepo(BaseModel):
    """gitRepo represents a git repository at a particular revision. DEPRECATED: GitRepo is deprecated. To provision a container with a git repo, mount an EmptyDir into an InitContainer that clones the repo using git, then mount the EmptyDir into the Pod's container."""

    model_config = ConfigDict(extra="forbid")

    directory: Optional[str] = Field(
        default=None,
        description="directory is the target directory name. Must not contain or start with '..'.  If '.' is supplied, the volume directory will be the git repository.  Otherwise, if specified, the volume will contain the git repository in the subdirectory with the given name.",
    )
    repository: str = Field(description="repository is the URL")
    revision: Optional[str] = Field(
        default=None,
        description="revision is the commit hash for the specified revision.",
    )


class Glusterfs(BaseModel):
    """glusterfs represents a Glusterfs mount on the host that shares a pod's lifetime. More info: https://examples.k8s.io/volumes/glusterfs/README.md"""

    model_config = ConfigDict(extra="forbid")

    endpoints: str = Field(
        description="endpoints is the endpoint name that details Glusterfs topology. More info: https://examples.k8s.io/volumes/glusterfs/README.md#create-a-pod"
    )
    path: str = Field(
        description="path is the Glusterfs volume path. More info: https://examples.k8s.io/volumes/glusterfs/README.md#create-a-pod"
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the Glusterfs volume to be mounted with read-only permissions. Defaults to false. More info: https://examples.k8s.io/volumes/glusterfs/README.md#create-a-pod",
    )


class HostPath(BaseModel):
    """hostPath represents a pre-existing file or directory on the host machine that is directly exposed to the container. This is generally used for system agents or other privileged things that are allowed to see the host machine. Most containers will NOT need this. More info: https://kubernetes.io/docs/concepts/storage/volumes#hostpath"""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        description="path of the directory on the host. If the path is a symlink, it will follow the link to the real path. More info: https://kubernetes.io/docs/concepts/storage/volumes#hostpath"
    )
    type: Optional[str] = Field(
        default=None,
        description='type for HostPath Volume Defaults to "" More info: https://kubernetes.io/docs/concepts/storage/volumes#hostpath',
    )


class Image(BaseModel):
    """image represents an OCI object (a container image or artifact) pulled and mounted on the kubelet's host machine. The volume is resolved at pod startup depending on which PullPolicy value is provided:  - Always: the kubelet always attempts to pull the reference. Container creation will fail If the pull fails. - Never: the kubelet never pulls the reference and only uses a local image or artifact. Container creation will fail if the reference isn't present. - IfNotPresent: the kubelet pulls if the reference isn't already present on disk. Container creation will fail if the reference isn't present and the pull fails.  The volume gets re-resolved if the pod gets deleted and recreated, which means that new remote content will become available on pod recreation. A failure to resolve or pull the image during pod startup will block containers from starting and may add significant latency. Failures will be retried using normal volume backoff and will be reported on the pod reason and message. The types of objects that may be mounted by this volume are defined by the container runtime implementation on a host machine and at minimum must include all valid types supported by the container image field. The OCI object gets mounted in a single directory (spec.containers[*].volumeMounts.mountPath) by merging the manifest layers in the same way as for container images. The volume will be mounted read-only (ro) and non-executable files (noexec). Sub path mounts for containers are not supported (spec.containers[*].volumeMounts.subpath). The field spec.securityContext.fsGroupChangePolicy has no effect on this volume type."""

    model_config = ConfigDict(extra="forbid")

    pullPolicy: Optional[str] = Field(
        default=None,
        alias="pull_policy",
        description="Policy for pulling OCI objects. Possible values are: Always: the kubelet always attempts to pull the reference. Container creation will fail If the pull fails. Never: the kubelet never pulls the reference and only uses a local image or artifact. Container creation will fail if the reference isn't present. IfNotPresent: the kubelet pulls if the reference isn't already present on disk. Container creation will fail if the reference isn't present and the pull fails. Defaults to Always if :latest tag is specified, or IfNotPresent otherwise.",
    )
    reference: Optional[str] = Field(
        default=None,
        description="Required: Image or artifact reference to be used. Behaves in the same way as pod.spec.containers[*].image. Pull secrets will be assembled in the same way as for the container image by looking up node credentials, SA image pull secrets, and pod spec image pull secrets. More info: https://kubernetes.io/docs/concepts/containers/images This field is optional to allow higher level config management to default or override container images in workload controllers like Deployments and StatefulSets.",
    )


class Iscsi(BaseModel):
    """iscsi represents an ISCSI Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://examples.k8s.io/volumes/iscsi/README.md"""

    model_config = ConfigDict(extra="forbid")

    chapAuthDiscovery: Optional[bool] = Field(
        default=None,
        alias="chap_auth_discovery",
        description="chapAuthDiscovery defines whether support iSCSI Discovery CHAP authentication",
    )
    chapAuthSession: Optional[bool] = Field(
        default=None,
        alias="chap_auth_session",
        description="chapAuthSession defines whether support iSCSI Session CHAP authentication",
    )
    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type of the volume that you want to mount. Tip: Ensure that the filesystem type is supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://kubernetes.io/docs/concepts/storage/volumes#iscsi',
    )
    initiatorName: Optional[str] = Field(
        default=None,
        alias="initiator_name",
        description="initiatorName is the custom iSCSI Initiator Name. If initiatorName is specified with iscsiInterface simultaneously, new iSCSI interface <target portal>:<volume name> will be created for the connection.",
    )
    iqn: str = Field(description="iqn is the target iSCSI Qualified Name.")
    iscsiInterface: Optional[str] = Field(
        default="default",
        alias="iscsi_interface",
        description="iscsiInterface is the interface Name that uses an iSCSI transport. Defaults to 'default' (tcp).",
    )
    lun: int = Field(description="lun represents iSCSI Target Lun number.")
    portals: Optional[List[str]] = Field(
        default=None,
        description="portals is the iSCSI Target Portal List. The portal is either an IP or ip_addr:port if the port is other than default (typically TCP ports 860 and 3260).",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the ReadOnly setting in VolumeMounts. Defaults to false.",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef is the CHAP Secret for iSCSI target and initiator authentication",
    )
    targetPortal: str = Field(
        alias="target_portal",
        description="targetPortal is iSCSI Target Portal. The Portal is either an IP or ip_addr:port if the port is other than default (typically TCP ports 860 and 3260).",
    )


class Nfs(BaseModel):
    """nfs represents an NFS mount on the host that shares a pod's lifetime More info: https://kubernetes.io/docs/concepts/storage/volumes#nfs"""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        description="path that is exported by the NFS server. More info: https://kubernetes.io/docs/concepts/storage/volumes#nfs"
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the NFS export to be mounted with read-only permissions. Defaults to false. More info: https://kubernetes.io/docs/concepts/storage/volumes#nfs",
    )
    server: str = Field(
        description="server is the hostname or IP address of the NFS server. More info: https://kubernetes.io/docs/concepts/storage/volumes#nfs"
    )


class PersistentVolumeClaim(BaseModel):
    """persistentVolumeClaimVolumeSource represents a reference to a PersistentVolumeClaim in the same namespace. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#persistentvolumeclaims"""

    model_config = ConfigDict(extra="forbid")

    claimName: str = Field(
        alias="claim_name",
        description="claimName is the name of a PersistentVolumeClaim in the same namespace as the pod using this volume. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#persistentvolumeclaims",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly Will force the ReadOnly setting in VolumeMounts. Default false.",
    )


class PhotonPersistentDisk(BaseModel):
    """photonPersistentDisk represents a PhotonController persistent disk attached and mounted on kubelets host machine"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    pdID: str = Field(
        alias="pd_id",
        description="pdID is the ID that identifies Photon Controller persistent disk",
    )


class PortworxVolume(BaseModel):
    """portworxVolume represents a portworx volume attached and mounted on kubelets host machine"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fSType represents the filesystem type to mount Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    volumeID: str = Field(
        alias="volume_id", description="volumeID uniquely identifies a Portworx volume"
    )


class ClusterTrustBundle(BaseModel):
    """ClusterTrustBundle allows a pod to access the `.spec.trustBundle` field of ClusterTrustBundle objects in an auto-updating file.  Alpha, gated by the ClusterTrustBundleProjection feature gate.  ClusterTrustBundle objects can either be selected by name, or by the combination of signer name and a label selector.  Kubelet performs aggressive normalization of the PEM contents written into the pod filesystem.  Esoteric PEM features such as inter-block comments and block headers are stripped.  Certificates are deduplicated. The ordering of certificates within the file is arbitrary, and Kubelet may change the order over time."""

    model_config = ConfigDict(extra="forbid")

    labelSelector: Optional[LabelSelector] = Field(
        default=None,
        alias="label_selector",
        description='Select all ClusterTrustBundles that match this label selector.  Only has effect if signerName is set.  Mutually-exclusive with name.  If unset, interpreted as "match nothing".  If set but empty, interpreted as "match everything".',
    )
    name: Optional[str] = Field(
        default=None,
        description="Select a single ClusterTrustBundle by object name.  Mutually-exclusive with signerName and labelSelector.",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="If true, don't block pod startup if the referenced ClusterTrustBundle(s) aren't available.  If using name, then the named ClusterTrustBundle is allowed not to exist.  If using signerName, then the combination of signerName and labelSelector is allowed to match zero ClusterTrustBundles.",
    )
    path: str = Field(
        description="Relative path from the volume root to write the bundle."
    )
    signerName: Optional[str] = Field(
        default=None,
        alias="signer_name",
        description="Select all ClusterTrustBundles that match this signer name. Mutually-exclusive with name.  The contents of all selected ClusterTrustBundles will be unified and deduplicated.",
    )


class Secret(BaseModel):
    """secret information about the secret data to project"""

    model_config = ConfigDict(extra="forbid")

    items: Optional[List[Items]] = Field(
        default=None,
        description="items if unspecified, each key-value pair in the Data field of the referenced Secret will be projected into the volume as a file whose name is the key and content is the value. If specified, the listed keys will be projected into the specified paths, and unlisted keys will not be present. If a key is specified which is not present in the Secret, the volume setup will error unless it is marked optional. Paths must be relative and may not contain the '..' path or start with '..'.",
    )
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="optional field specify whether the Secret or its key must be defined",
    )


class ServiceAccountToken(BaseModel):
    """serviceAccountToken is information about the serviceAccountToken data to project"""

    model_config = ConfigDict(extra="forbid")

    audience: Optional[str] = Field(
        default=None,
        description="audience is the intended audience of the token. A recipient of a token must identify itself with an identifier specified in the audience of the token, and otherwise should reject the token. The audience defaults to the identifier of the apiserver.",
    )
    expirationSeconds: Optional[int] = Field(
        default=None,
        alias="expiration_seconds",
        description="expirationSeconds is the requested duration of validity of the service account token. As the token approaches expiration, the kubelet volume plugin will proactively rotate the service account token. The kubelet will start trying to rotate the token if the token is older than 80 percent of its time to live or if the token is older than 24 hours.Defaults to 1 hour and must be at least 10 minutes.",
    )
    path: str = Field(
        description="path is the path relative to the mount point of the file to project the token into."
    )


class Sources(BaseModel):
    """Projection that may be projected along with other supported volume types. Exactly one of these fields must be set."""

    model_config = ConfigDict(extra="forbid")

    clusterTrustBundle: Optional[ClusterTrustBundle] = Field(
        default=None,
        alias="cluster_trust_bundle",
        description="ClusterTrustBundle allows a pod to access the `.spec.trustBundle` field of ClusterTrustBundle objects in an auto-updating file.  Alpha, gated by the ClusterTrustBundleProjection feature gate.  ClusterTrustBundle objects can either be selected by name, or by the combination of signer name and a label selector.  Kubelet performs aggressive normalization of the PEM contents written into the pod filesystem.  Esoteric PEM features such as inter-block comments and block headers are stripped.  Certificates are deduplicated. The ordering of certificates within the file is arbitrary, and Kubelet may change the order over time.",
    )
    configMap: Optional[ConfigMap] = Field(
        default=None,
        alias="config_map",
        description="configMap information about the configMap data to project",
    )
    downwardAPI: Optional[DownwardApi] = Field(
        default=None,
        alias="downward_api",
        description="downwardAPI information about the downwardAPI data to project",
    )
    secret: Optional[Secret] = Field(
        default=None, description="secret information about the secret data to project"
    )
    serviceAccountToken: Optional[ServiceAccountToken] = Field(
        default=None,
        alias="service_account_token",
        description="serviceAccountToken is information about the serviceAccountToken data to project",
    )


class Projected(BaseModel):
    """projected items for all in one resources secrets, configmaps, and downward API"""

    model_config = ConfigDict(extra="forbid")

    defaultMode: Optional[int] = Field(
        default=None,
        alias="default_mode",
        description="defaultMode are the mode bits used to set permissions on created files by default. Must be an octal value between 0000 and 0777 or a decimal value between 0 and 511. YAML accepts both octal and decimal values, JSON requires decimal values for mode bits. Directories within the path are not affected by this setting. This might be in conflict with other options that affect the file mode, like fsGroup, and the result can be other mode bits set.",
    )
    sources: Optional[List[Sources]] = Field(
        default=None,
        description="sources is the list of volume projections. Each entry in this list handles one source.",
    )


class Quobyte(BaseModel):
    """quobyte represents a Quobyte mount on the host that shares a pod's lifetime"""

    model_config = ConfigDict(extra="forbid")

    group: Optional[str] = Field(
        default=None, description="group to map volume access to Default is no group"
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the Quobyte volume to be mounted with read-only permissions. Defaults to false.",
    )
    registry: str = Field(
        description="registry represents a single or multiple Quobyte Registry services specified as a string as host:port pair (multiple entries are separated with commas) which acts as the central registry for volumes"
    )
    tenant: Optional[str] = Field(
        default=None,
        description="tenant owning the given Quobyte volume in the Backend Used with dynamically provisioned Quobyte volumes, value is set by the plugin",
    )
    user: Optional[str] = Field(
        default=None,
        description="user to map volume access to Defaults to serivceaccount user",
    )
    volume: str = Field(
        description="volume is a string that references an already created Quobyte volume by name."
    )


class Rbd(BaseModel):
    """rbd represents a Rados Block Device mount on the host that shares a pod's lifetime. More info: https://examples.k8s.io/volumes/rbd/README.md"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type of the volume that you want to mount. Tip: Ensure that the filesystem type is supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://kubernetes.io/docs/concepts/storage/volumes#rbd',
    )
    image: str = Field(
        description="image is the rados image name. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it"
    )
    keyring: Optional[str] = Field(
        default="/etc/ceph/keyring",
        description="keyring is the path to key ring for RBDUser. Default is /etc/ceph/keyring. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it",
    )
    monitors: List[str] = Field(
        description="monitors is a collection of Ceph monitors. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it"
    )
    pool: Optional[str] = Field(
        default="rbd",
        description="pool is the rados pool name. Default is rbd. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly here will force the ReadOnly setting in VolumeMounts. Defaults to false. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef is name of the authentication secret for RBDUser. If provided overrides keyring. Default is nil. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it",
    )
    user: Optional[str] = Field(
        default="admin",
        description="user is the rados user name. Default is admin. More info: https://examples.k8s.io/volumes/rbd/README.md#how-to-use-it",
    )


class ScaleIo(BaseModel):
    """scaleIO represents a ScaleIO persistent volume attached and mounted on Kubernetes nodes."""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default="xfs",
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Default is "xfs".',
    )
    gateway: str = Field(
        description="gateway is the host address of the ScaleIO API Gateway."
    )
    protectionDomain: Optional[str] = Field(
        default=None,
        alias="protection_domain",
        description="protectionDomain is the name of the ScaleIO Protection Domain for the configured storage.",
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly Defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    secretRef: SecretRef = Field(
        alias="secret_ref",
        description="secretRef references to the secret for ScaleIO user and other sensitive information. If this is not provided, Login operation will fail.",
    )
    sslEnabled: Optional[bool] = Field(
        default=None,
        alias="ssl_enabled",
        description="sslEnabled Flag enable/disable SSL communication with Gateway, default false",
    )
    storageMode: Optional[str] = Field(
        default="ThinProvisioned",
        alias="storage_mode",
        description="storageMode indicates whether the storage for a volume should be ThickProvisioned or ThinProvisioned. Default is ThinProvisioned.",
    )
    storagePool: Optional[str] = Field(
        default=None,
        alias="storage_pool",
        description="storagePool is the ScaleIO Storage Pool associated with the protection domain.",
    )
    system: str = Field(
        description="system is the name of the storage system as configured in ScaleIO."
    )
    volumeName: Optional[str] = Field(
        default=None,
        alias="volume_name",
        description="volumeName is the name of a volume already created in the ScaleIO system that is associated with this volume source.",
    )


class Storageos(BaseModel):
    """storageOS represents a StorageOS volume attached and mounted on Kubernetes nodes."""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is the filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    readOnly: Optional[bool] = Field(
        default=None,
        alias="read_only",
        description="readOnly defaults to false (read/write). ReadOnly here will force the ReadOnly setting in VolumeMounts.",
    )
    secretRef: Optional[SecretRef] = Field(
        default=None,
        alias="secret_ref",
        description="secretRef specifies the secret to use for obtaining the StorageOS API credentials.  If not specified, default values will be attempted.",
    )
    volumeName: Optional[str] = Field(
        default=None,
        alias="volume_name",
        description="volumeName is the human-readable name of the StorageOS volume.  Volume names are only unique within a namespace.",
    )
    volumeNamespace: Optional[str] = Field(
        default=None,
        alias="volume_namespace",
        description='volumeNamespace specifies the scope of the volume within StorageOS.  If no namespace is specified then the Pod\'s namespace will be used.  This allows the Kubernetes name scoping to be mirrored within StorageOS for tighter integration. Set VolumeName to any name to override the default behaviour. Set to "default" if you are not using namespaces within StorageOS. Namespaces that do not pre-exist within StorageOS will be created.',
    )


class VsphereVolume(BaseModel):
    """vsphereVolume represents a vSphere volume attached and mounted on kubelets host machine"""

    model_config = ConfigDict(extra="forbid")

    fsType: Optional[str] = Field(
        default=None,
        alias="fs_type",
        description='fsType is filesystem type to mount. Must be a filesystem type supported by the host operating system. Ex. "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified.',
    )
    storagePolicyID: Optional[str] = Field(
        default=None,
        alias="storage_policy_id",
        description="storagePolicyID is the storage Policy Based Management (SPBM) profile ID associated with the StoragePolicyName.",
    )
    storagePolicyName: Optional[str] = Field(
        default=None,
        alias="storage_policy_name",
        description="storagePolicyName is the storage Policy Based Management (SPBM) profile name.",
    )
    volumePath: str = Field(
        alias="volume_path",
        description="volumePath is the path that identifies vSphere volume vmdk",
    )


class Volumes(BaseModel):
    """Volume represents a named volume in a pod that may be accessed by any container in the pod."""

    model_config = ConfigDict(extra="forbid")

    awsElasticBlockStore: Optional[AwsElasticBlockStore] = Field(
        default=None,
        alias="aws_elastic_block_store",
        description="awsElasticBlockStore represents an AWS Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes#awselasticblockstore",
    )
    azureDisk: Optional[AzureDisk] = Field(
        default=None,
        alias="azure_disk",
        description="azureDisk represents an Azure Data Disk mount on the host and bind mount to the pod.",
    )
    azureFile: Optional[AzureFile] = Field(
        default=None,
        alias="azure_file",
        description="azureFile represents an Azure File Service mount on the host and bind mount to the pod.",
    )
    cephfs: Optional[Cephfs] = Field(
        default=None,
        description="cephFS represents a Ceph FS mount on the host that shares a pod's lifetime",
    )
    cinder: Optional[Cinder] = Field(
        default=None,
        description="cinder represents a cinder volume attached and mounted on kubelets host machine. More info: https://examples.k8s.io/mysql-cinder-pd/README.md",
    )
    configMap: Optional[ConfigMap] = Field(
        default=None,
        alias="config_map",
        description="configMap represents a configMap that should populate this volume",
    )
    csi: Optional[Csi] = Field(
        default=None,
        description="csi (Container Storage Interface) represents ephemeral storage that is handled by certain external CSI drivers (Beta feature).",
    )
    downwardAPI: Optional[DownwardApi] = Field(
        default=None,
        alias="downward_api",
        description="downwardAPI represents downward API about the pod that should populate this volume",
    )
    emptyDir: Optional[EmptyDir] = Field(
        default=None,
        alias="empty_dir",
        description="emptyDir represents a temporary directory that shares a pod's lifetime. More info: https://kubernetes.io/docs/concepts/storage/volumes#emptydir",
    )
    ephemeral: Optional[Ephemeral] = Field(
        default=None,
        description="ephemeral represents a volume that is handled by a cluster storage driver. The volume's lifecycle is tied to the pod that defines it - it will be created before the pod starts, and deleted when the pod is removed.  Use this if: a) the volume is only needed while the pod runs, b) features of normal volumes like restoring from snapshot or capacity    tracking are needed, c) the storage driver is specified through a storage class, and d) the storage driver supports dynamic volume provisioning through    a PersistentVolumeClaim (see EphemeralVolumeSource for more    information on the connection between this volume type    and PersistentVolumeClaim).  Use PersistentVolumeClaim or one of the vendor-specific APIs for volumes that persist for longer than the lifecycle of an individual pod.  Use CSI for light-weight local ephemeral volumes if the CSI driver is meant to be used that way - see the documentation of the driver for more information.  A pod can use both types of ephemeral volumes and persistent volumes at the same time.",
    )
    fc: Optional[Fc] = Field(
        default=None,
        description="fc represents a Fibre Channel resource that is attached to a kubelet's host machine and then exposed to the pod.",
    )
    flexVolume: Optional[FlexVolume] = Field(
        default=None,
        alias="flex_volume",
        description="flexVolume represents a generic volume resource that is provisioned/attached using an exec based plugin.",
    )
    flocker: Optional[Flocker] = Field(
        default=None,
        description="flocker represents a Flocker volume attached to a kubelet's host machine. This depends on the Flocker control service being running",
    )
    gcePersistentDisk: Optional[GcePersistentDisk] = Field(
        default=None,
        alias="gce_persistent_disk",
        description="gcePersistentDisk represents a GCE Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes#gcepersistentdisk",
    )
    gitRepo: Optional[GitRepo] = Field(
        default=None,
        alias="git_repo",
        description="gitRepo represents a git repository at a particular revision. DEPRECATED: GitRepo is deprecated. To provision a container with a git repo, mount an EmptyDir into an InitContainer that clones the repo using git, then mount the EmptyDir into the Pod's container.",
    )
    glusterfs: Optional[Glusterfs] = Field(
        default=None,
        description="glusterfs represents a Glusterfs mount on the host that shares a pod's lifetime. More info: https://examples.k8s.io/volumes/glusterfs/README.md",
    )
    hostPath: Optional[HostPath] = Field(
        default=None,
        alias="host_path",
        description="hostPath represents a pre-existing file or directory on the host machine that is directly exposed to the container. This is generally used for system agents or other privileged things that are allowed to see the host machine. Most containers will NOT need this. More info: https://kubernetes.io/docs/concepts/storage/volumes#hostpath",
    )
    image: Optional[Image] = Field(
        default=None,
        description="image represents an OCI object (a container image or artifact) pulled and mounted on the kubelet's host machine. The volume is resolved at pod startup depending on which PullPolicy value is provided:  - Always: the kubelet always attempts to pull the reference. Container creation will fail If the pull fails. - Never: the kubelet never pulls the reference and only uses a local image or artifact. Container creation will fail if the reference isn't present. - IfNotPresent: the kubelet pulls if the reference isn't already present on disk. Container creation will fail if the reference isn't present and the pull fails.  The volume gets re-resolved if the pod gets deleted and recreated, which means that new remote content will become available on pod recreation. A failure to resolve or pull the image during pod startup will block containers from starting and may add significant latency. Failures will be retried using normal volume backoff and will be reported on the pod reason and message. The types of objects that may be mounted by this volume are defined by the container runtime implementation on a host machine and at minimum must include all valid types supported by the container image field. The OCI object gets mounted in a single directory (spec.containers[*].volumeMounts.mountPath) by merging the manifest layers in the same way as for container images. The volume will be mounted read-only (ro) and non-executable files (noexec). Sub path mounts for containers are not supported (spec.containers[*].volumeMounts.subpath). The field spec.securityContext.fsGroupChangePolicy has no effect on this volume type.",
    )
    iscsi: Optional[Iscsi] = Field(
        default=None,
        description="iscsi represents an ISCSI Disk resource that is attached to a kubelet's host machine and then exposed to the pod. More info: https://examples.k8s.io/volumes/iscsi/README.md",
    )
    name: str = Field(
        description="name of the volume. Must be a DNS_LABEL and unique within the pod. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names"
    )
    nfs: Optional[Nfs] = Field(
        default=None,
        description="nfs represents an NFS mount on the host that shares a pod's lifetime More info: https://kubernetes.io/docs/concepts/storage/volumes#nfs",
    )
    persistentVolumeClaim: Optional[PersistentVolumeClaim] = Field(
        default=None,
        alias="persistent_volume_claim",
        description="persistentVolumeClaimVolumeSource represents a reference to a PersistentVolumeClaim in the same namespace. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#persistentvolumeclaims",
    )
    photonPersistentDisk: Optional[PhotonPersistentDisk] = Field(
        default=None,
        alias="photon_persistent_disk",
        description="photonPersistentDisk represents a PhotonController persistent disk attached and mounted on kubelets host machine",
    )
    portworxVolume: Optional[PortworxVolume] = Field(
        default=None,
        alias="portworx_volume",
        description="portworxVolume represents a portworx volume attached and mounted on kubelets host machine",
    )
    projected: Optional[Projected] = Field(
        default=None,
        description="projected items for all in one resources secrets, configmaps, and downward API",
    )
    quobyte: Optional[Quobyte] = Field(
        default=None,
        description="quobyte represents a Quobyte mount on the host that shares a pod's lifetime",
    )
    rbd: Optional[Rbd] = Field(
        default=None,
        description="rbd represents a Rados Block Device mount on the host that shares a pod's lifetime. More info: https://examples.k8s.io/volumes/rbd/README.md",
    )
    scaleIO: Optional[ScaleIo] = Field(
        default=None,
        alias="scale_io",
        description="scaleIO represents a ScaleIO persistent volume attached and mounted on Kubernetes nodes.",
    )
    secret: Optional[Secret] = Field(
        default=None,
        description="secret represents a secret that should populate this volume. More info: https://kubernetes.io/docs/concepts/storage/volumes#secret",
    )
    storageos: Optional[Storageos] = Field(
        default=None,
        description="storageOS represents a StorageOS volume attached and mounted on Kubernetes nodes.",
    )
    vsphereVolume: Optional[VsphereVolume] = Field(
        default=None,
        alias="vsphere_volume",
        description="vsphereVolume represents a vSphere volume attached and mounted on kubelets host machine",
    )


class Spec(BaseModel):
    """Specification of the desired behavior of the pod. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status"""

    model_config = ConfigDict(extra="forbid")

    activeDeadlineSeconds: Optional[int] = Field(
        default=None,
        alias="active_deadline_seconds",
        description="Optional duration in seconds the pod may be active on the node relative to StartTime before the system will actively try to mark it failed and kill associated containers. Value must be a positive integer.",
    )
    affinity: Optional[Affinity] = Field(
        default=None, description="If specified, the pod's scheduling constraints"
    )
    automountServiceAccountToken: Optional[bool] = Field(
        default=None,
        alias="automount_service_account_token",
        description="AutomountServiceAccountToken indicates whether a service account token should be automatically mounted.",
    )
    containers: List[Containers] = Field(
        description="List of containers belonging to the pod. Containers cannot currently be added or removed. There must be at least one container in a Pod. Cannot be updated."
    )
    dnsConfig: Optional[DnsConfig] = Field(
        default=None,
        alias="dns_config",
        description="Specifies the DNS parameters of a pod. Parameters specified here will be merged to the generated DNS configuration based on DNSPolicy.",
    )
    dnsPolicy: Optional[str] = Field(
        default=None,
        alias="dns_policy",
        description="Set DNS policy for the pod. Defaults to \"ClusterFirst\". Valid values are 'ClusterFirstWithHostNet', 'ClusterFirst', 'Default' or 'None'. DNS parameters given in DNSConfig will be merged with the policy selected with DNSPolicy. To have DNS options set along with hostNetwork, you have to specify DNS policy explicitly to 'ClusterFirstWithHostNet'.",
    )
    enableServiceLinks: Optional[bool] = Field(
        default=None,
        alias="enable_service_links",
        description="EnableServiceLinks indicates whether information about services should be injected into pod's environment variables, matching the syntax of Docker links. Optional: Defaults to true.",
    )
    ephemeralContainers: Optional[List[EphemeralContainers]] = Field(
        default=None,
        alias="ephemeral_containers",
        description="List of ephemeral containers run in this pod. Ephemeral containers may be run in an existing pod to perform user-initiated actions such as debugging. This list cannot be specified when creating a pod, and it cannot be modified by updating the pod spec. In order to add an ephemeral container to an existing pod, use the pod's ephemeralcontainers subresource.",
    )
    hostAliases: Optional[List[HostAliases]] = Field(
        default=None,
        alias="host_aliases",
        description="HostAliases is an optional list of hosts and IPs that will be injected into the pod's hosts file if specified.",
    )
    hostIPC: Optional[bool] = Field(
        default=None,
        alias="host_ipc",
        description="Use the host's ipc namespace. Optional: Default to false.",
    )
    hostNetwork: Optional[bool] = Field(
        default=None,
        alias="host_network",
        description="Host networking requested for this pod. Use the host's network namespace. If this option is set, the ports that will be used must be specified. Default to false.",
    )
    hostPID: Optional[bool] = Field(
        default=None,
        alias="host_pid",
        description="Use the host's pid namespace. Optional: Default to false.",
    )
    hostUsers: Optional[bool] = Field(
        default=None,
        alias="host_users",
        description="Use the host's user namespace. Optional: Default to true. If set to true or not present, the pod will be run in the host user namespace, useful for when the pod needs a feature only available to the host user namespace, such as loading a kernel module with CAP_SYS_MODULE. When set to false, a new userns is created for the pod. Setting false is useful for mitigating container breakout vulnerabilities even allowing users to run their containers as root without actually having root privileges on the host. This field is alpha-level and is only honored by servers that enable the UserNamespacesSupport feature.",
    )
    hostname: Optional[str] = Field(
        default=None,
        description="Specifies the hostname of the Pod If not specified, the pod's hostname will be set to a system-defined value.",
    )
    imagePullSecrets: Optional[List[ImagePullSecrets]] = Field(
        default=None,
        alias="image_pull_secrets",
        description="ImagePullSecrets is an optional list of references to secrets in the same namespace to use for pulling any of the images used by this PodSpec. If specified, these secrets will be passed to individual puller implementations for them to use. More info: https://kubernetes.io/docs/concepts/containers/images#specifying-imagepullsecrets-on-a-pod",
    )
    initContainers: Optional[List[InitContainers]] = Field(
        default=None,
        alias="init_containers",
        description="List of initialization containers belonging to the pod. Init containers are executed in order prior to containers being started. If any init container fails, the pod is considered to have failed and is handled according to its restartPolicy. The name for an init container or normal container must be unique among all containers. Init containers may not have Lifecycle actions, Readiness probes, Liveness probes, or Startup probes. The resourceRequirements of an init container are taken into account during scheduling by finding the highest request/limit for each resource type, and then using the max of of that value or the sum of the normal containers. Limits are applied to init containers in a similar fashion. Init containers cannot currently be added or removed. Cannot be updated. More info: https://kubernetes.io/docs/concepts/workloads/pods/init-containers/",
    )
    nodeName: Optional[str] = Field(
        default=None,
        alias="node_name",
        description="NodeName indicates in which node this pod is scheduled. If empty, this pod is a candidate for scheduling by the scheduler defined in schedulerName. Once this field is set, the kubelet for this node becomes responsible for the lifecycle of this pod. This field should not be used to express a desire for the pod to be scheduled on a specific node. https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodename",
    )
    nodeSelector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="node_selector",
        description="NodeSelector is a selector which must be true for the pod to fit on a node. Selector which must match a node's labels for the pod to be scheduled on that node. More info: https://kubernetes.io/docs/concepts/configuration/assign-pod-node/",
    )
    os: Optional[Os] = Field(
        default=None,
        description="Specifies the OS of the containers in the pod. Some pod and container fields are restricted if this is set.  If the OS field is set to linux, the following fields must be unset: -securityContext.windowsOptions  If the OS field is set to windows, following fields must be unset: - spec.hostPID - spec.hostIPC - spec.hostUsers - spec.securityContext.appArmorProfile - spec.securityContext.seLinuxOptions - spec.securityContext.seccompProfile - spec.securityContext.fsGroup - spec.securityContext.fsGroupChangePolicy - spec.securityContext.sysctls - spec.shareProcessNamespace - spec.securityContext.runAsUser - spec.securityContext.runAsGroup - spec.securityContext.supplementalGroups - spec.securityContext.supplementalGroupsPolicy - spec.containers[*].securityContext.appArmorProfile - spec.containers[*].securityContext.seLinuxOptions - spec.containers[*].securityContext.seccompProfile - spec.containers[*].securityContext.capabilities - spec.containers[*].securityContext.readOnlyRootFilesystem - spec.containers[*].securityContext.privileged - spec.containers[*].securityContext.allowPrivilegeEscalation - spec.containers[*].securityContext.procMount - spec.containers[*].securityContext.runAsUser - spec.containers[*].securityContext.runAsGroup",
    )
    overhead: Optional[Dict[str, Union[int, str]]] = Field(
        default=None,
        description="Overhead represents the resource overhead associated with running a pod for a given RuntimeClass. This field will be autopopulated at admission time by the RuntimeClass admission controller. If the RuntimeClass admission controller is enabled, overhead must not be set in Pod create requests. The RuntimeClass admission controller will reject Pod create requests which have the overhead already set. If RuntimeClass is configured and selected in the PodSpec, Overhead will be set to the value defined in the corresponding RuntimeClass, otherwise it will remain unset and treated as zero. More info: https://git.k8s.io/enhancements/keps/sig-node/688-pod-overhead/README.md",
    )
    preemptionPolicy: Optional[str] = Field(
        default=None,
        alias="preemption_policy",
        description="PreemptionPolicy is the Policy for preempting pods with lower priority. One of Never, PreemptLowerPriority. Defaults to PreemptLowerPriority if unset.",
    )
    priority: Optional[int] = Field(
        default=None,
        description="The priority value. Various system components use this field to find the priority of the pod. When Priority Admission Controller is enabled, it prevents users from setting this field. The admission controller populates this field from PriorityClassName. The higher the value, the higher the priority.",
    )
    priorityClassName: Optional[str] = Field(
        default=None,
        alias="priority_class_name",
        description='If specified, indicates the pod\'s priority. "system-node-critical" and "system-cluster-critical" are two special keywords which indicate the highest priorities with the former being the highest priority. Any other name must be defined by creating a PriorityClass object with that name. If not specified, the pod priority will be default or zero if there is no default.',
    )
    readinessGates: Optional[List[ReadinessGates]] = Field(
        default=None,
        alias="readiness_gates",
        description='If specified, all readiness gates will be evaluated for pod readiness. A pod is ready when all its containers are ready AND all conditions specified in the readiness gates have status equal to "True" More info: https://git.k8s.io/enhancements/keps/sig-network/580-pod-readiness-gates',
    )
    resourceClaims: Optional[List[ResourceClaims]] = Field(
        default=None,
        alias="resource_claims",
        description="ResourceClaims defines which ResourceClaims must be allocated and reserved before the Pod is allowed to start. The resources will be made available to those containers which consume them by name.  This is an alpha field and requires enabling the DynamicResourceAllocation feature gate.  This field is immutable.",
    )
    restartPolicy: Optional[str] = Field(
        default=None,
        alias="restart_policy",
        description="Restart policy for all containers within the pod. One of Always, OnFailure, Never. In some contexts, only a subset of those values may be permitted. Default to Always. More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy",
    )
    runtimeClassName: Optional[str] = Field(
        default=None,
        alias="runtime_class_name",
        description='RuntimeClassName refers to a RuntimeClass object in the node.k8s.io group, which should be used to run this pod.  If no RuntimeClass resource matches the named class, the pod will not be run. If unset or empty, the "legacy" RuntimeClass will be used, which is an implicit class with an empty definition that uses the default runtime handler. More info: https://git.k8s.io/enhancements/keps/sig-node/585-runtime-class',
    )
    schedulerName: Optional[str] = Field(
        default=None,
        alias="scheduler_name",
        description="If specified, the pod will be dispatched by specified scheduler. If not specified, the pod will be dispatched by default scheduler.",
    )
    schedulingGates: Optional[List[SchedulingGates]] = Field(
        default=None,
        alias="scheduling_gates",
        description="SchedulingGates is an opaque list of values that if specified will block scheduling the pod. If schedulingGates is not empty, the pod will stay in the SchedulingGated state and the scheduler will not attempt to schedule the pod.  SchedulingGates can only be set at pod creation time, and be removed only afterwards.",
    )
    securityContext: Optional[SecurityContext] = Field(
        default=None,
        alias="security_context",
        description="SecurityContext holds pod-level security attributes and common container settings. Optional: Defaults to empty.  See type description for default values of each field.",
    )
    serviceAccount: Optional[str] = Field(
        default=None,
        alias="service_account",
        description="DeprecatedServiceAccount is a deprecated alias for ServiceAccountName. Deprecated: Use serviceAccountName instead.",
    )
    serviceAccountName: Optional[str] = Field(
        default=None,
        alias="service_account_name",
        description="ServiceAccountName is the name of the ServiceAccount to use to run this pod. More info: https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/",
    )
    setHostnameAsFQDN: Optional[bool] = Field(
        default=None,
        alias="set_hostname_as_fqdn",
        description="If true the pod's hostname will be configured as the pod's FQDN, rather than the leaf name (the default). In Linux containers, this means setting the FQDN in the hostname field of the kernel (the nodename field of struct utsname). In Windows containers, this means setting the registry value of hostname for the registry key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters to FQDN. If a pod does not have FQDN, this has no effect. Default to false.",
    )
    shareProcessNamespace: Optional[bool] = Field(
        default=None,
        alias="share_process_namespace",
        description="Share a single process namespace between all of the containers in a pod. When this is set containers will be able to view and signal processes from other containers in the same pod, and the first process in each container will not be assigned PID 1. HostPID and ShareProcessNamespace cannot both be set. Optional: Default to false.",
    )
    subdomain: Optional[str] = Field(
        default=None,
        description='If specified, the fully qualified Pod hostname will be "<hostname>.<subdomain>.<pod namespace>.svc.<cluster domain>". If not specified, the pod will not have a domainname at all.',
    )
    terminationGracePeriodSeconds: Optional[int] = Field(
        default=None,
        alias="termination_grace_period_seconds",
        description="Optional duration in seconds the pod needs to terminate gracefully. May be decreased in delete request. Value must be non-negative integer. The value zero indicates stop immediately via the kill signal (no opportunity to shut down). If this value is nil, the default grace period will be used instead. The grace period is the duration in seconds after the processes running in the pod are sent a termination signal and the time when the processes are forcibly halted with a kill signal. Set this value longer than the expected cleanup time for your process. Defaults to 30 seconds.",
    )
    tolerations: Optional[List[Tolerations]] = Field(
        default=None, description="If specified, the pod's tolerations."
    )
    topologySpreadConstraints: Optional[List[TopologySpreadConstraints]] = Field(
        default=None,
        alias="topology_spread_constraints",
        description="TopologySpreadConstraints describes how a group of pods ought to spread across topology domains. Scheduler will schedule pods in a way which abides by the constraints. All topologySpreadConstraints are ANDed.",
    )
    volumes: Optional[List[Volumes]] = Field(
        default=None,
        description="List of volumes that can be mounted by containers belonging to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes",
    )


class Template(BaseModel):
    """template is the Pod template.  The only allowed fields in template.metadata are labels and annotations.  If requests are omitted for a container or initContainer, they default to the limits if they are explicitly specified for the container or initContainer.  During admission, the rules in nodeSelector and nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution that match the keys in the nodeLabels from the ResourceFlavors considered for this Workload are used to filter the ResourceFlavors that can be assigned to this podSet."""

    model_config = ConfigDict(extra="forbid")

    metadata: Optional[Metadata] = Field(
        default=None,
        description="Standard object's metadata. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata",
    )
    spec: Optional[Spec] = Field(
        default=None,
        description="Specification of the desired behavior of the pod. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status",
    )


class ReplicaSpec(BaseModel):
    """ReplicaSpec is a description of the replica"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The name for the replica set")
    replicas: Optional[int] = Field(
        default=1,
        description="Replicas is the desired number of replicas of the given template.",
    )
    spares: Optional[int] = Field(
        default=0,
        description="Spares requests spare resources from Kueue. E.g. If a job is configured with 4 replicas and 2 spares, job requests resources required to run 6 pods such as cpu, gpu",
    )
    template: Optional[Template] = Field(
        default=None,
        description="Template is the object that describes the pod that will be created for this replica.",
    )


class LogMonitoringConfiguration(BaseModel):
    """LogMonitoringRule defines the criteria used to detect a SLOW or HANGING job"""

    model_config = ConfigDict(extra="forbid")

    expectedRecurringFrequencyInSeconds: Optional[int] = Field(
        default=None,
        alias="expected_recurring_frequency_in_seconds",
        description="Time interval between two subsequent matches for LogPattern beyond which, the rule evaluates to HANGING. When not specified, there is no constraint on duration between two subsequent matches for  LogPattern.",
    )
    expectedStartCutOffInSeconds: Optional[int] = Field(
        default=None,
        alias="expected_start_cut_off_in_seconds",
        description="Time to first match for LogPattern beyond which, the rule evaluates to HANGING. When not specified, there is no constraint on time to first match for LogPattern.",
    )
    logPattern: str = Field(
        alias="log_pattern",
        description="Regex to identify log lines to apply the rule to when the rule is active. This regex can optionally include one capturing group to extract a numeric metric value.",
    )
    metricEvaluationDataPoints: Optional[int] = Field(
        default=None,
        alias="metric_evaluation_data_points",
        description="The number of consecutive times that a rule must evaluate to SLOW in order to mark a job as SLOW. When not specified, the default value is 1.",
    )
    metricThreshold: Optional[int] = Field(
        default=None,
        alias="metric_threshold",
        description="Threshold for value extracted by LogPattern if it has a capturing group. When not specified, Metric evaluation will not be performed.",
    )
    name: str = Field(description="Name of the rule")
    operator: Optional[str] = Field(
        default=None,
        description="Operator to compare the value extracted by LogPattern to MetricThreshold. Rule evaluates to SLOW if value extracted by LogPattern compared to MetricThreshold using Operator evaluates to true. When not specified, Metric evaluation will not be performed. Following operator values are supported: gt (greater than) lt (lesser than) eq (equal to) gteq (greater than or equal to) lteq (less than or equal to)",
    )
    stopPattern: Optional[str] = Field(
        default=None,
        alias="stop_pattern",
        description="Regex to identify the log line at which to deactivate the rule. When not specified, the rule will always be active.",
    )


class RestartPolicy(BaseModel):
    """Additional restart limiting configurations"""

    model_config = ConfigDict(extra="forbid")

    evalPeriodSeconds: int = Field(
        alias="eval_period_seconds",
        description="The period of evaluating the restart limit in seconds",
    )
    maxFullJobRestarts: Optional[int] = Field(
        default=None,
        alias="max_full_job_restarts",
        description="The max allowed number of full job restarts before failing the job",
    )
    numRestartBeforeFullJobRestart: Optional[int] = Field(
        default=None,
        alias="num_restart_before_full_job_restart",
        description="The number of standard restarts before a full job restart",
    )


class RunPolicy(BaseModel):
    """RunPolicy"""

    model_config = ConfigDict(extra="forbid")

    activeDeadlineSeconds: Optional[int] = Field(
        default=None,
        alias="active_deadline_seconds",
        description="Specifies the duration in seconds relative to the startTime that the job may be active before the system tries to terminate it; value must be positive integer.",
    )
    cleanPodPolicy: Optional[str] = Field(
        default="All",
        alias="clean_pod_policy",
        description="CleanPodPolicy defines the policy to kill pods after the job completes.",
    )
    faultDeadlineSeconds: Optional[int] = Field(
        default=None,
        alias="fault_deadline_seconds",
        description="The limit on the fault time for the job (Status of Fault) before failing",
    )
    jobMaxRetryCount: Optional[int] = Field(default=None, alias="job_max_retry_count")
    logMonitoringConfiguration: Optional[List[LogMonitoringConfiguration]] = Field(
        default=None,
        alias="log_monitoring_configuration",
        description="LogMonitoringConfiguration defines the log monitoring rules for SLOW and HANGING job detection",
    )
    restartPolicy: Optional[RestartPolicy] = Field(
        default=None,
        alias="restart_policy",
        description="Additional restart limiting configurations",
    )
    startupDeadlineSeconds: Optional[int] = Field(
        default=None,
        alias="startup_deadline_seconds",
        description="The limit on the startup time for the job (Status of Staring) before failing",
    )
    suspend: Optional[bool] = Field(
        default=None, description="Suspend suspends HyperPodPytorchJob when set to true"
    )
    ttlSecondsAfterFinished: Optional[int] = Field(
        default=0,
        alias="ttl_seconds_after_finished",
        description="TTLSecondsAfterFinished is the TTL to clean up jobs. Set to -1 for infinite",
    )


class PodSets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(
        default=1, description="count is the number of pods for the spec."
    )
    minCount: Optional[int] = Field(
        default=None,
        alias="min_count",
        description="minCount is the minimum number of pods for the spec acceptable if the workload supports partial admission.  If not provided, partial admission for the current PodSet is not enabled.  Only one podSet within the workload can use this.  This is an alpha field and requires enabling PartialAdmission feature gate.",
    )
    name: Optional[str] = Field(default="main", description="name is the PodSet name.")
    template: Template = Field(
        description="template is the Pod template.  The only allowed fields in template.metadata are labels and annotations.  If requests are omitted for a container or initContainer, they default to the limits if they are explicitly specified for the container or initContainer.  During admission, the rules in nodeSelector and nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution that match the keys in the nodeLabels from the ResourceFlavors considered for this Workload are used to filter the ResourceFlavors that can be assigned to this podSet."
    )


class Pods(BaseModel):
    """DEPRECATED pods to include job pods status in jobPods associated with replicaSpecs pods is retained here to support operator upgrade"""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None, alias="api_version", description="API version of the referent."
    )
    fieldPath: Optional[str] = Field(
        default=None,
        alias="field_path",
        description='If referring to a piece of an object instead of an entire object, this string should contain a valid JSON/Go field access statement, such as desiredState.manifest.containers[2]. For example, if the object reference is to a container within a pod, this would take on a value like: "spec.containers{name}" (where "name" refers to the name of the container that triggered the event) or if no container name is specified "spec.containers[2]" (container with index 2 in this pod). This syntax is chosen only to have some well-defined way of referencing a part of an object.',
    )
    kind: Optional[str] = Field(
        default=None,
        description="Kind of the referent. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds",
    )
    name: Optional[str] = Field(
        default=None,
        description="Name of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/",
    )
    resourceVersion: Optional[str] = Field(
        default=None,
        alias="resource_version",
        description="Specific resourceVersion to which this reference is made, if any. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#concurrency-control-and-consistency",
    )
    uid: Optional[str] = Field(
        default=None,
        description="UID of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids",
    )


class RestartStatus(BaseModel):
    """Additional restart limiting status"""

    model_config = ConfigDict(extra="forbid")

    currentEvalPeriod: int = Field(
        alias="current_eval_period", description="The current window"
    )
    fullJobRestartCount: int = Field(
        alias="full_job_restart_count",
        description="The number of full job restarts that have ocurred in the window",
    )
    restartCount: int = Field(
        alias="restart_count",
        description="The number of standard restarts that have occurred in the window since the last full job restart",
    )


class HyperPodPytorchJobStatus(BaseModel):
    """HyperPodPytorchJobStatus defines the observed state of HyperPodPytorchJob"""

    model_config = ConfigDict(extra="forbid")

    completionTime: Optional[str] = Field(
        default=None,
        alias="completion_time",
        description="Represents time when the job was completed. It is not guaranteed to be set in happens-before order across separate operations. It is represented in RFC3339 form and is in UTC.",
    )
    conditions: Optional[List[Conditions]] = None
    jobPods: Optional[List[JobPods]] = Field(
        default=None,
        alias="job_pods",
        description="The StatefulSet containing the training pods",
    )
    managerPods: Optional[ManagerPods] = Field(
        default=None, alias="manager_pods", description="Pod Manager pods"
    )
    masterAddr: Optional[str] = Field(
        default=None,
        alias="master_addr",
        description="The address of the master (RANK 0) pod",
    )
    masterPort: Optional[str] = Field(
        default=None,
        alias="master_port",
        description="The port of the master (RANK 0) pod",
    )
    podManagerStatuses: Optional[List[PodManagerStatuses]] = Field(
        default=None,
        alias="pod_manager_statuses",
        description="The status of each pod manager as a PodManagerStatus",
    )
    podSetInfos: Optional[List[PodSetInfos]] = Field(
        default=None,
        alias="pod_set_infos",
        description="PodSetInformation assigned to the HyperPodPytorchJob's PodSet by Kueue",
    )
    podSets: Optional[List[PodSets]] = Field(
        default=None,
        alias="pod_sets",
        description="PodSets used by Kueue to manage workload objects",
    )
    restartCount: Optional[int] = Field(default=0, alias="restart_count")
    restartStatus: Optional[RestartStatus] = Field(
        default=None,
        alias="restart_status",
        description="Additional restart limiting status",
    )
    startTime: Optional[str] = Field(
        default=None,
        alias="start_time",
        description="The time when job is first acknowledged by the controller. When using kueue, the job is also admitted It is represented in RFC3339 form and is in UTC.",
    )


class _HyperPodPytorchJob(BaseModel):
    """Config defines the desired state of HyperPodPytorchJob"""

    model_config = ConfigDict(extra="ignore")

    nprocPerNode: str = Field(
        default="auto",
        alias="nproc_per_node",
        description="Number of workers per node; supported values: [auto, cpu, gpu, int].",
    )
    replicaSpecs: Optional[List[ReplicaSpec]] = Field(
        default=None,
        alias="replica_specs",
        description="The replicas to include as part of the job",
    )
    runPolicy: Optional[RunPolicy] = Field(
        default=None, alias="run_policy", description="RunPolicy"
    )