"""
CLI decorators for consistent error handling across all commands.
Template-agnostic design that dynamically detects resource and operation types.
"""

import sys
import click
import functools
import logging
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)

def _namespace_exists(namespace: str) -> bool:
    """
    Check if a namespace exists using KubernetesClient.
    Uses lazy initialization to avoid import-time failures.
    """
    try:
        from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
        k8s_client = KubernetesClient()
        return k8s_client.check_if_namespace_exists(namespace)
    except Exception as e:
        logger.debug(f"Failed to check namespace existence: {e}")
        # If we can't check, assume it exists to avoid false negatives
        return True

def _check_training_operator_exists() -> bool:
    """
    Check if Training Operator CRD exists using KubernetesClient.
    Uses lazy initialization to avoid import-time failures.
    """
    try:
        from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
        from kubernetes import client
        from sagemaker.hyperpod.cli.constants.pytorch_constants import HYPERPOD_PYTORCH_CRD_NAME
        
        k8s_client = KubernetesClient()
        
        # Ensure kube client is initialized
        if not k8s_client._kube_client:
            logger.debug("Kubernetes client not initialized")
            return True  # Don't block if client unavailable
            
        # Use ApiextensionsV1Api to check for CRDs
        extensions_api = client.ApiextensionsV1Api(k8s_client._kube_client)
        
        # Check if the Training Operator CRD exists
        extensions_api.read_custom_resource_definition(name=HYPERPOD_PYTORCH_CRD_NAME)
        return True
        
    except ImportError as e:
        logger.debug(f"Failed to import kubernetes client: {e}")
        return True  # Don't block if kubernetes package unavailable
    except client.rest.ApiException as e:
        if e.status == 404:
            return False  # CRD doesn't exist
        else:
            logger.debug(f"Error checking Training Operator CRD: {e}")
            return True  # Don't block on API errors
    except Exception as e:
        logger.debug(f"Failed to check Training Operator existence: {e}")
        return True  # Don't block on validation failures
    
def _is_pytorch_job_operation(func, **kwargs) -> bool:
    """
    Detect if this is a Pytorch job operation
    """
    try:
        # Check function name for PyTorch patterns
        func_name = func.__name__.lower()
        if 'pytorch' in func_name:
            return True

        # Check if wrapped function has PyTorch in name
        if hasattr(func, '__wrapped__'):
            wrapped_name = getattr(func.__wrapped__, '__name__', '').lower()
            if 'pytorch' in wrapped_name:
                return True

        # Check Click command info for PyTorch patterns
        try:
            click_ctx = click.get_current_context(silent=True)
            if click_ctx and hasattr(click_ctx, 'info_name'):
                # This would catch commands like "hyp pytorch create pytorch-job"
                command_path = str(click_ctx.info_name).lower()
                if 'pytorch' in command_path:
                    return True
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"Failed to detect PyTorch operation: {e}")

    return False

def _is_get_logs_operation(func, **kwargs) -> bool:
    """
    Detect if this is a get-logs operation
    """
    try:
        # Check function name for logs patterns
        func_name = func.__name__.lower()
        if 'logs' in func_name:
            return True

        # Check if wrapped function has logs in name
        if hasattr(func, '__wrapped__'):
            wrapped_name = getattr(func.__wrapped__, '__name__', '').lower()
            if 'logs' in wrapped_name:
                return True

        # Check Click command info for logs patterns
        try:
            click_ctx = click.get_current_context(silent=True)
            if click_ctx and hasattr(click_ctx, 'info_name'):
                # This would catch commands like "hyp get-logs hyp-pytorch-job"
                command_path = str(click_ctx.info_name).lower()
                if 'logs' in command_path:
                    return True
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"Failed to detect get-logs operation: {e}")

    return False

def _check_pod_readiness_and_generate_message(pod_name: str, namespace: str) -> str:
    """
    Check pod readiness and generate appropriate error message for get-logs operations.
    Uses lazy initialization to avoid import-time failures.
    """
    try:
        from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
        
        k8s_client = KubernetesClient()
        
        # Ensure kube client is initialized
        if not k8s_client._kube_client:
            logger.debug("Kubernetes client not initialized")
            return f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet."
            
        # Get pod details
        pod_details = k8s_client.get_pod_details(pod_name, namespace)
        
        # Extract pod phase
        pod_phase = getattr(pod_details.status, 'phase', 'Unknown') if pod_details.status else 'Unknown'
        
        # Extract container statuses and reasons
        container_reason = None
        if pod_details.status and hasattr(pod_details.status, 'container_statuses') and pod_details.status.container_statuses:
            for container_status in pod_details.status.container_statuses:
                if hasattr(container_status, 'state') and container_status.state:
                    if hasattr(container_status.state, 'waiting') and container_status.state.waiting:
                        container_reason = getattr(container_status.state.waiting, 'reason', None)
                        break
                    elif hasattr(container_status.state, 'terminated') and container_status.state.terminated:
                        container_reason = getattr(container_status.state.terminated, 'reason', None)
                        break
        
        # Check init container statuses
        init_container_reason = None
        if pod_details.status and hasattr(pod_details.status, 'init_container_statuses') and pod_details.status.init_container_statuses:
            for init_container_status in pod_details.status.init_container_statuses:
                if hasattr(init_container_status, 'state') and init_container_status.state:
                    if hasattr(init_container_status.state, 'waiting') and init_container_status.state.waiting:
                        init_container_reason = getattr(init_container_status.state.waiting, 'reason', None)
                        break
        
        # Generate appropriate message based on pod state
        if pod_phase == 'Failed':
            reason_text = container_reason or 'Container exited with non-zero status'
            return (f"❌ Cannot get logs for pod '{pod_name}' - pod has failed.\n"
                   f"Pod Status: Failed ({reason_text})\n"
                   f"Reason: {_get_human_readable_reason(reason_text)}")
        
        elif pod_phase == 'Pending':
            if init_container_reason:
                if 'Init:' in str(init_container_reason):
                    reason_text = init_container_reason
                    return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                           f"Pod Status: Pending ({reason_text})\n"
                           f"Reason: Init containers are still running")
                else:
                    reason_text = init_container_reason
                    return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                           f"Pod Status: Pending ({reason_text})\n"
                           f"Reason: {_get_human_readable_reason(reason_text)}")
            elif container_reason:
                reason_text = container_reason
                return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                       f"Pod Status: Pending ({reason_text})\n"
                       f"Reason: {_get_human_readable_reason(reason_text)}")
            else:
                return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                       f"Pod Status: Pending\n"
                       f"Reason: Pod is still being scheduled or initialized")
        
        elif pod_phase == 'Running' and container_reason:
            # Running but with issues like CrashLoopBackOff
            return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                   f"Pod Status: Running ({container_reason})\n"
                   f"Reason: {_get_human_readable_reason(container_reason)}")
        
        else:
            # Check if pod is being terminated
            if (pod_details.metadata and hasattr(pod_details.metadata, 'deletion_timestamp') 
                and pod_details.metadata.deletion_timestamp):
                return (f"❌ Cannot get logs for pod '{pod_name}' - pod is being terminated.\n"
                       f"Pod Status: Terminating\n"
                       f"Reason: Pod is shutting down")
            else:
                # Fallback for unknown states
                return (f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet.\n"
                       f"Pod Status: {pod_phase}\n"
                       f"Reason: Pod may not be fully initialized")
        
    except ImportError as e:
        logger.debug(f"Failed to import kubernetes client: {e}")
        return f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet."
    except Exception as e:
        logger.debug(f"Failed to check pod readiness for pod {pod_name}: {e}")
        return f"❌ Cannot get logs for pod '{pod_name}' - pod is not ready yet."

def _get_human_readable_reason(reason: str) -> str:
    """
    Convert Kubernetes container reasons to human-readable explanations.
    """
    reason_map = {
        'ContainerCreating': 'Containers are still being created',
        'ImagePullBackOff': 'Cannot pull container image',
        'ErrImagePull': 'Cannot pull container image',
        'CrashLoopBackOff': 'Container keeps crashing and restarting',
        'Error': 'Container exited with non-zero status',
        'Completed': 'Container has completed execution',
        'OOMKilled': 'Container was killed due to out of memory',
        'CreateContainerConfigError': 'Container configuration is invalid',
        'InvalidImageName': 'Container image name is invalid',
        'CreateContainerError': 'Cannot create container',
        'RunContainerError': 'Cannot run container',
    }
    
    return reason_map.get(reason, f'Container state: {reason}')

def _check_job_exists_for_pod_validation(job_name: str, namespace: str, raw_resource_type: str) -> bool:
    """
    Check if a job/resource exists independently of pod validation.
    Uses template-agnostic CLI commands to verify job existence.
    """
    try:
        import subprocess
        
        # Construct the describe command for the resource type
        # Use appropriate parameter name based on resource type
        if raw_resource_type == "pytorch-job":
            cmd = ["hyp", "describe", f"hyp-{raw_resource_type}", "--job-name", job_name]
        else:
            cmd = ["hyp", "describe", f"hyp-{raw_resource_type}", "--name", job_name]
            
        if namespace != "default":
            cmd.extend(["--namespace", namespace])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        # If describe command succeeds, job exists
        return result.returncode == 0
        
    except Exception as e:
        logger.debug(f"Failed to check job existence for {job_name}: {e}")
        return False  # Conservative: assume job doesn't exist if we can't verify

def _is_pod_not_found_in_job_scenario(error_message: str, func=None, **kwargs) -> bool:
    """
    Detect if this is a scenario where job exists but pod name is wrong.
    This happens when get-logs is called with invalid pod name for existing job.
    """
    try:
        # Check if this is a get-logs operation
        is_logs_op = _is_get_logs_operation(func, **kwargs)
        if not is_logs_op:
            return False
            
        # Check if error message indicates job not found
        error_lower = error_message.lower()
        has_not_found = "not found" in error_lower
        if not has_not_found:
            return False
            
        # Extract job name and namespace from context
        job_name = None
        namespace = _extract_namespace_from_kwargs(**kwargs)
        
        # Try to get job name from kwargs or click context
        try:
            click_ctx = click.get_current_context(silent=True)
            if click_ctx and click_ctx.params:
                # Common parameter names for job/resource names
                for param_name in ['job_name', 'name', 'job']:
                    if param_name in click_ctx.params:
                        job_name = click_ctx.params[param_name]
                        break
        except Exception:
            pass
        
        # Also check kwargs
        if not job_name:
            for param_name in ['job_name', 'name', 'job']:
                if param_name in kwargs:
                    job_name = kwargs[param_name]
                    break
        
        if not job_name:
            return False
            
        # Check if job actually exists
        raw_resource_type, _ = _extract_resource_from_command(None)  # Will use context
        job_exists = _check_job_exists_for_pod_validation(job_name, namespace, raw_resource_type)
        
        result = job_exists  # If job exists but we got "not found", it's likely a pod issue
        return result
        
    except Exception as e:
        logger.debug(f"Failed to detect pod not found scenario: {e}")
        return False

def _generate_pod_not_found_message(pod_name: str, job_name: str) -> str:
    """
    Generate enhanced error message for pod not found in job scenario.
    """
    return f"❌ Pod '{pod_name}' not found for job '{job_name}'."

def _extract_namespace_from_kwargs(**kwargs) -> str:
    """Extract namespace from function kwargs and Click context."""
    # First try kwargs (works for most commands)
    namespace = kwargs.get('namespace')
    if namespace:
        return namespace
    
    # For create commands using @generate_click_command, check Click context
    try:
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and click_ctx.params:
            namespace = click_ctx.params.get('namespace')
            if namespace:
                return namespace
    except Exception as e:
        logger.debug(f"Failed to extract namespace from Click context: {e}")
    
    return 'default'

def _is_create_operation(func) -> bool:
    """
    Template-agnostic detection of create operations.
    Create operations should let parameter validation happen first before namespace validation.
    """
    try:
        # Check function name for create patterns
        func_name = func.__name__.lower()
        if 'create' in func_name:
            return True
        
        # Check if wrapped function has create in name
        if hasattr(func, '__wrapped__'):
            wrapped_name = getattr(func.__wrapped__, '__name__', '').lower()
            if 'create' in wrapped_name:
                return True
        
        # Check Click command info for create patterns
        try:
            click_ctx = click.get_current_context(silent=True)
            if click_ctx and hasattr(click_ctx, 'info_name'):
                # This would catch commands like "hyp create hyp-jumpstart-endpoint"
                command_path = str(click_ctx.info_name).lower()
                if 'create' in command_path:
                    return True
        except Exception:
            pass
            
    except Exception as e:
        logger.debug(f"Failed to detect create operation: {e}")
    
    return False

def _extract_model_id_dynamically(**kwargs) -> str:
    """
    Extract model-id from parameters.
    Returns model-id value or 'unknown' if not found.
    """
    try:
        # Check Click context for model_id variations
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and click_ctx.params:
            for param_name, value in click_ctx.params.items():
                if 'model' in param_name.lower() and 'id' in param_name.lower() and value:
                    return str(value)
        
        # Also check kwargs fallback
        for param_name, value in kwargs.items():
            if 'model' in param_name.lower() and 'id' in param_name.lower() and value:
                return str(value)
                
    except Exception as e:
        logger.debug(f"Failed to extract model-id: {e}")
    
    return 'unknown'

def _is_valid_jumpstart_model_id(model_id: str) -> bool:
    """
    Check if model-id exists in JumpStart registry.
    Uses same SageMaker API that's already being called during creation.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        sagemaker_client = boto3.client('sagemaker')
        
        # Use same API call that's failing in the current code
        sagemaker_client.describe_hub_content(
            HubName='SageMakerPublicHub',
            HubContentType='Model', 
            HubContentName=model_id
        )
        return True  # Model exists
        
    except ClientError as e:
        if 'ResourceNotFound' in str(e):
            return False  # Model doesn't exist
        else:
            logger.debug(f"Error validating model-id {model_id}: {e}")
            return True  # Don't block on API errors
    except Exception as e:
        logger.debug(f"Failed to validate model-id {model_id}: {e}")
        return True  # Don't block on validation failures

def _validate_model_id_if_present(**kwargs) -> bool:
    """
    Template-agnostic model-id validation for JumpStart endpoints.
    Only validates if model_id parameter is present.
    Returns True if validation passes or no model-id found, False if invalid model-id.
    """
    try:
        model_id = _extract_model_id_dynamically(**kwargs)
        
        # No model-id found = no validation needed
        if model_id == 'unknown':
            return True
            
        # Validate using SageMaker API
        return _is_valid_jumpstart_model_id(model_id)
        
    except Exception as e:
        logger.debug(f"Failed to validate model-id: {e}")
        return True  # Don't block on validation failures

def _extract_container_name_dynamically(**kwargs) -> str:
    """
    Extract container name from parameters.
    Returns container name or 'unknown' if not found.
    """
    try:
        # Check Click context for container parameter
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and click_ctx.params:
            container = click_ctx.params.get('container')
            if container:
                return str(container)
        
        # Also check kwargs fallback
        container = kwargs.get('container')
        if container:
            return str(container)
                
    except Exception as e:
        logger.debug(f"Failed to extract container name: {e}")
    
    return 'unknown'

def _get_available_containers(pod_name: str, namespace: str) -> list:
    """
    Get list of available container names in a pod using KubernetesClient.
    Returns list of container names or empty list if unable to determine.
    """
    try:
        from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
        k8s_client = KubernetesClient()
        
        # Get pod details using existing method
        pod_details = k8s_client.get_pod_details(pod_name, namespace)
        
        containers = []
        
        # Extract main containers
        if hasattr(pod_details, 'spec') and hasattr(pod_details.spec, 'containers'):
            for container in pod_details.spec.containers:
                if hasattr(container, 'name'):
                    containers.append(container.name)
        
        # Extract init containers if they exist
        if hasattr(pod_details, 'spec') and hasattr(pod_details.spec, 'init_containers'):
            for container in pod_details.spec.init_containers:
                if hasattr(container, 'name'):
                    containers.append(f"{container.name} (init)")
        
        return containers
        
    except Exception as e:
        logger.debug(f"Failed to get available containers for pod {pod_name}: {e}")
        return []

def _has_container_parameter(**kwargs) -> bool:
    """
    Check if command has container parameter specified.
    The 400 Bad Request error only occurs when container parameter is provided but invalid.
    """
    try:
        # Check Click context for container parameter
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and click_ctx.params:
            return 'container' in click_ctx.params and click_ctx.params.get('container')
        
        # Fallback to kwargs
        return 'container' in kwargs and kwargs.get('container')
        
    except Exception as e:
        logger.debug(f"Failed to detect container parameter: {e}")
        return False

def _extract_primary_target_dynamically(**kwargs):
    """
    Dynamically determine what the command is targeting - completely template-agnostic.
    Returns tuple of (target_type, target_name) where:
    - target_type: 'pod' if targeting pods, 'resource' if targeting resources
    - target_name: the actual name being targeted
    """
    try:
        # 1: Click context extraction (most reliable)
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and click_ctx.params:
            params = click_ctx.params
            
            # Check if command has pod_name but no other *_name parameters
            has_pod_name = 'pod_name' in params and params.get('pod_name')
            has_resource_name = any((k.endswith('_name') or k == 'name') and k not in ['pod_name', 'namespace'] 
                                   and params.get(k) for k in params.keys())
            
            if has_pod_name and not has_resource_name:
                # Command is targeting a pod (like get-logs with only pod-name)
                return ('pod', params.get('pod_name'))
            elif has_resource_name:
                # Command is targeting a resource instance
                for param_name, value in params.items():
                    if ((param_name.endswith('_name') or param_name == 'name') and 
                        param_name not in ['pod_name', 'namespace'] and 
                        value):
                        return ('resource', value)
        
        # 2: Parent context fallback (for nested commands)
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and hasattr(click_ctx, 'parent') and click_ctx.parent:
            # Look at parent context for potential arguments
            parent_params = getattr(click_ctx.parent, 'params', {})
            for param_name, value in parent_params.items():
                if ((param_name.endswith('_name') or param_name == 'name') and 
                    param_name not in ['pod_name', 'namespace'] and 
                    value):
                    return ('resource', value)
        
        # 3: Direct kwargs inspection fallback (for error handling scenarios)
        for param_name, value in kwargs.items():
            if ((param_name.endswith('_name') or param_name == 'name') and 
                param_name not in ['pod_name', 'namespace'] and 
                value):
                # Check if this is a pod-targeted command
                has_pod_name = 'pod_name' in kwargs and kwargs.get('pod_name')
                if has_pod_name and param_name == 'pod_name':
                    return ('pod', value)
                elif param_name != 'pod_name':
                    return ('resource', value)
                    
    except Exception as e:
        logger.debug(f"Failed to extract primary target dynamically: {e}")
    
    return ('resource', 'unknown')  # Final fallback

def _generate_context_aware_error_message(target_type: str, target_name: str, display_name: str, namespace: str, raw_resource_type: str, resources_exist: bool = None) -> str:
    """
    Generate appropriate error message based on what the command is actually targeting.
    Completely template-agnostic and context-driven.
    """
    if target_type == 'pod':
        # Pod-focused error - suggestions about listing resources aren't helpful for pod operations
        if namespace == 'default':
            return f"❓ Pod '{target_name}' not found for {display_name} resources. Please check the pod name."
        else:
            return f"❓ Pod '{target_name}' not found for {display_name} resources in namespace '{namespace}'. Please check the pod name."
    else:
        # Resource-focused error - include helpful suggestions
        list_command = _get_list_command_from_resource_type(raw_resource_type)
        namespace_flag = f" --namespace {namespace}" if namespace != "default" else ""
        
        # Construct namespace part of message - don't mention default namespace in main message
        if namespace == 'default':
            namespace_part = ""
            location_description = f" in namespace '{namespace}'"  # Always specify the actual namespace
        else:
            namespace_part = f" in namespace '{namespace}'"
            location_description = f" in namespace '{namespace}'"
        
        if resources_exist is False:
            # No resources exist in namespace
            return (
                f"❓ {display_name} '{target_name}' not found{namespace_part}. "
                f"No resources of this type exist{location_description}. "
                f"Use '{list_command}' to check for available resources."
            )
        elif resources_exist is True:
            # Resources exist in namespace
            return (
                f"❓ {display_name} '{target_name}' not found{namespace_part}. "
                f"Please check the resource name - other resources exist{location_description}. "
                f"Use '{list_command}{namespace_flag}' to see available resources."
            )
        else:
            # Unable to determine - fallback to basic contextual message
            return (
                f"❓ {display_name} '{target_name}' not found{namespace_part}. "
                f"Please check the resource name and try again. "
                f"Use '{list_command}{namespace_flag}' to see available resources."
            )

def _generate_namespace_error_message(namespace: str, func) -> str:
    """Generate helpful error message for non-existent namespace - context-aware for create vs other operations."""
    # Check if this is a create operation
    if _is_create_operation(func):
        return (
            f"❌ Namespace '{namespace}' does not exist on this cluster. "
            f"Please create the namespace first or use an existing namespace."
        )
    else:
        # For describe/delete/list operations, suggest checking for resources
        raw_resource_type, display_name = _extract_resource_from_command(func)
        list_command = _get_list_command_from_resource_type(raw_resource_type)
        
        return (
            f"❌ Namespace '{namespace}' does not exist on this cluster. "
            f"Use '{list_command}' to check for available resources."
        )

def _extract_resource_from_command(func) -> tuple[str, str]:
    """
    Extract resource type and display name from command context - template-agnostic.
    Detect's Click command names through multiple methods.
    
    Returns:
        Tuple of (raw_resource_type, display_name) where:
        - raw_resource_type: for list commands (e.g., "jumpstart-endpoint")  
        - display_name: for user messages (e.g., "JumpStart Endpoint")
    """
    try:
        command_name = None
        
        # 1: Get from current Click context (most reliable)
        click_ctx = click.get_current_context(silent=True)
        if click_ctx and hasattr(click_ctx, 'info_name'):
            command_name = click_ctx.info_name.lower()
        
        # 2: Direct access to func.name
        elif hasattr(func, 'name') and func.name:
            command_name = func.name.lower()
        
        # 3: Check __wrapped__ attribute chain (for complex decorator combinations)
        elif hasattr(func, '__wrapped__'):
            wrapped = func.__wrapped__
            if hasattr(wrapped, 'name') and wrapped.name:
                command_name = wrapped.name.lower()
        
        # If we found a Click command name, parse it
        if command_name and command_name.startswith('hyp-'):
            resource_part = command_name[4:]  # Remove 'hyp-' prefix
            display_name = _format_display_name(resource_part)
            return resource_part, display_name
        
        func_name = func.__name__.lower()
        if '_' in func_name:
            # Template-agnostic: "js_delete" -> "js", "custom_describe" -> "custom"
            prefix = func_name.split('_')[0]
            display_name = _format_display_name(prefix)
            return f"{prefix}-resource", display_name
            
    except (AttributeError, TypeError):
        pass
    
    return "resource", "Resource"  # Generic fallback

def _format_display_name(resource_part: str) -> str:
    """
    Format resource part into user-friendly display name.
    Completely template-agnostic - no hardcoded template names.
    """
    # Split on hyphens and capitalize each part
    parts = resource_part.split('-')
    formatted_parts = [part.capitalize() for part in parts]
    return ' '.join(formatted_parts)

def _get_list_command_from_resource_type(raw_resource_type: str) -> str:
    """
    Generate appropriate list command for resource type.
    Fully template-agnostic - constructs command directly from raw resource type.
    """
    # raw_resource_type is already in the correct format (e.g., "resource-type")
    return f"hyp list hyp-{raw_resource_type}"

def _check_resources_exist(raw_resource_type: str, namespace: str) -> bool:
    """
    Check if any resources exist in namespace - template-agnostic CLI approach.
    Uses the existing CLI commands to check for resource existence without importing template classes.
    Returns True if resources exist, False if no resources, None if unable to determine.
    """
    try:
        import subprocess
        
        # Construct the list command that already exists (use hyp directly)
        cmd = ["hyp", "list", f"hyp-{raw_resource_type}"]
        if namespace != "default":
            cmd.extend(["--namespace", namespace])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,  
            timeout=15,  # 15 second timeout
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Check if output contains any data rows (simple heuristic: more than 2 lines means header + separator + data)
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # If we have more than 2 lines, likely we have: header + separator + at least one data row
            # This is much simpler and more reliable than parsing the table format
            has_data = len(lines) > 2
            
            return has_data
        
        # If command failed or no output, assume no resources
        logger.debug(f"List command failed or returned no data. Return code: {result.returncode}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.debug(f"List command timed out for {raw_resource_type}")
        return None
    except Exception as e:
        logger.debug(f"Failed to check resource existence for {raw_resource_type}: {e}")
        return None

def handle_cli_exceptions():
    """
    Template-agnostic decorator with proactive namespace validation and enhanced error handling.
    
    This decorator:
    1. Validates namespace existence BEFORE command execution (for all namespaces)
    2. Dynamically detects resource type from Click command name
    3. Dynamically detects operation type from function name
    4. Applies enhanced 404 handling with contextual messages
    5. Handles all other exceptions consistently
    
    Usage:
        @handle_cli_exceptions()
        @click.command("hyp-resource-type")
        def resource_delete(name, namespace):
            # Command logic here - no try/catch needed!
            # Namespace validation and resource type automatically handled
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1: Smart Namespace Validation
            # Only validate namespace proactively for operations where it's the PRIMARY concern
            # Skip for create operations where parameter validation should come first
            namespace = _extract_namespace_from_kwargs(**kwargs)
            
            # Template-agnostic operation detection
            is_create_operation = _is_create_operation(func)
            
            # Only validate namespace proactively for non-create operations
            if not is_create_operation and namespace != 'default' and not _namespace_exists(namespace):
                namespace_error_message = _generate_namespace_error_message(namespace, func)
                click.echo(namespace_error_message)
                sys.exit(1)
                return
            
            # Validate model-id BEFORE creation starts to avoid failed deployments
            if is_create_operation and not _validate_model_id_if_present(**kwargs):
                model_id = _extract_model_id_dynamically(**kwargs)
                click.echo(f"❌ Model ID '{model_id}' not found in JumpStart registry.")
                sys.exit(1)
                return
            
            # Check Training Operator CRD for PyTorch job creation
            if is_create_operation and _is_pytorch_job_operation(func, **kwargs):
                if not _check_training_operator_exists():
                    from sagemaker.hyperpod.cli.constants.pytorch_constants import HYPERPOD_PYTORCH_CRD_NAME
                    click.echo("❌ Training Operator not found in cluster.")
                    click.echo(f"Missing Custom Resource Definition: {HYPERPOD_PYTORCH_CRD_NAME}")
                    click.echo("The Training Operator is required to submit PyTorch jobs. Please install the Training Operator in your cluster.")
                    sys.exit(1)
                    return
            
            # Execute the command
            try:
                return func(*args, **kwargs)
            except Exception as e:
                
                # 2: Enhanced Error Handling with Create Operation Namespace Check
                # For create operations, check if namespace exists when command fails
                if is_create_operation and namespace != 'default' and not _namespace_exists(namespace):
                    namespace_error_message = _generate_namespace_error_message(namespace, func)
                    click.echo(namespace_error_message)
                    sys.exit(1)
                    return
                
                # 3: Enhanced 404 Resource Handling with Dynamic Target Detection
                # Check if this is a 404 error that can benefit from enhanced handling
                if isinstance(e, ApiException) and e.status == 404:
                    # Dynamically determine what the command is targeting
                    target_type, target_name = _extract_primary_target_dynamically(**kwargs)
                    namespace = kwargs.get('namespace', 'default')
                    
                    # Dynamically detect resource type
                    raw_resource_type, display_name = _extract_resource_from_command(func)
                    
                    try:
                        # Generate context-aware error message based on target type
                        if target_type == 'pod':
                            # Pod-focused error - no need to check resource existence
                            enhanced_message = _generate_context_aware_error_message(
                                target_type, target_name, display_name, namespace, raw_resource_type
                            )
                        else:
                            # Resource-focused error - check resource existence for better context
                            resources_exist = _check_resources_exist(raw_resource_type, namespace)
                            enhanced_message = _generate_context_aware_error_message(
                                target_type, target_name, display_name, namespace, raw_resource_type, resources_exist
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                        
                    except Exception:
                        # Fallback to basic message (no ❓ emoji for fallback)
                        fallback_message = (
                            f"{display_name} '{target_name}' not found in namespace '{namespace}'. "
                            f"Please check the resource name and namespace."
                        )
                        click.echo(fallback_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                
                # Check if this might be a wrapped 404 in a regular Exception
                elif "404" in str(e) or "not found" in str(e).lower():
                    # First check if this is a "pod not found in job" scenario
                    if _is_pod_not_found_in_job_scenario(str(e), func=func, **kwargs):
                        try:
                            # Extract pod name and job name from context
                            pod_name = None
                            job_name = None
                            
                            click_ctx = click.get_current_context(silent=True)
                            if click_ctx and click_ctx.params:
                                pod_name = click_ctx.params.get('pod_name')
                                job_name = click_ctx.params.get('job_name') or click_ctx.params.get('name')
                            
                            # Fallback to kwargs
                            if not pod_name:
                                pod_name = kwargs.get('pod_name')
                            if not job_name:
                                job_name = kwargs.get('job_name') or kwargs.get('name')
                            
                            if pod_name and job_name:
                                enhanced_message = _generate_pod_not_found_message(pod_name, job_name)
                                click.echo(enhanced_message)
                                sys.exit(1)
                                return
                        except Exception:
                            # Fall through to normal 404 handling if pod validation fails
                            pass
                    
                    # Use dynamic target detection for wrapped 404s as well
                    target_type, target_name = _extract_primary_target_dynamically(**kwargs)
                    namespace = kwargs.get('namespace', 'default')
                    
                    # Dynamically detect resource type
                    raw_resource_type, display_name = _extract_resource_from_command(func)
                    
                    try:
                        # Generate context-aware error message based on target type
                        if target_type == 'pod':
                            # Pod-focused error - no need to check resource existence
                            enhanced_message = _generate_context_aware_error_message(
                                target_type, target_name, display_name, namespace, raw_resource_type
                            )
                        else:
                            # Resource-focused error - check resource existence for better context
                            resources_exist = _check_resources_exist(raw_resource_type, namespace)
                            enhanced_message = _generate_context_aware_error_message(
                                target_type, target_name, display_name, namespace, raw_resource_type, resources_exist
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                        
                    except Exception:
                        # Fall through to standard handling
                        pass
                
                # 4: Container Error Handling for 400 Bad Request
                # Check if this is a 400 Bad Request with invalid container parameter (check this FIRST)
                elif "400" in str(e) and "Bad Request" in str(e) and _has_container_parameter(**kwargs):
                    try:
                        pod_name = _extract_primary_target_dynamically(**kwargs)[1]  # Get pod name
                        container_name = _extract_container_name_dynamically(**kwargs)
                        namespace = kwargs.get('namespace', 'default')
                        
                        available_containers = _get_available_containers(pod_name, namespace)
                        if available_containers:
                            click.echo(f"❌ Container '{container_name}' not found in pod '{pod_name}'.")
                            click.echo(f"Available containers: {available_containers}")
                            # Generate helpful command suggestion
                            raw_resource_type, _ = _extract_resource_from_command(func)
                            suggested_container = available_containers[0].replace(' (init)', '')  # Remove init marker for command
                            click.echo(f"Use: hyp get-logs hyp-{raw_resource_type} --pod-name {pod_name} --container {suggested_container}")
                        else:
                            click.echo(f"❌ Container '{container_name}' not found in pod '{pod_name}'.")
                        
                        sys.exit(1)
                        return
                        
                    except Exception:
                        # Fall through to standard handling if container validation fails
                        pass
                
                # 5: Enhanced Pod Readiness Error Handling for get-logs 400 Bad Request
                # Check if this is a 400 Bad Request from get-logs on pod that's not ready
                elif "400" in str(e) and "Bad Request" in str(e) and _is_get_logs_operation(func, **kwargs):
                    try:
                        pod_name = _extract_primary_target_dynamically(**kwargs)[1]  # Get pod name
                        namespace = _extract_namespace_from_kwargs(**kwargs)
                        
                        enhanced_message = _check_pod_readiness_and_generate_message(pod_name, namespace)
                        click.echo(enhanced_message)
                        sys.exit(1)
                        return
                        
                    except Exception:
                        # Fall through to standard handling if pod readiness check fails
                        pass
                
                # For all other errors, use standard handling 
                click.echo(str(e))
                sys.exit(1)
        
        return wrapper
    return decorator
