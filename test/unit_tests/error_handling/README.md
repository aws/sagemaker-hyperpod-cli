# SageMaker HyperPod CLI - Error Handling Unit Tests

This directory contains unit tests for the **template-agnostic** 404 error handling system.

## Overview

The error handling system has been redesigned to be **template-agnostic**, eliminating hardcoded enums and enabling true CLI/SDK decoupling. The system now dynamically detects resource and operation types from command context.

## Current Test Files

### `test_cli_decorators.py` - Template-Agnostic CLI Decorators
- **TestHandleCliExceptions**: Tests the core decorator functionality
- **TestTemplateAgnosticDetection**: Tests dynamic resource/operation detection
- **TestTemplateAgnostic404Handling**: Tests 404 handling without hardcoded types

#### Key Features Tested:
- `_extract_resource_from_command()` - Extracts resource type from Click command names
- `_detect_operation_type_from_function()` - Detects operation from function names  
- `_get_list_command_from_resource_type()` - Generates appropriate list commands
- Template-agnostic 404 message generation
- Fallback handling when detection fails

## Template-Agnostic Design Benefits

### ✅ **Future-Proof**
```python
# New templates work automatically without code changes:
# hyp-llama-job → "llama job" 
# hyp-future-template → "future template"
```

### ✅ **Zero Maintenance Overhead**
- No hardcoded enums to maintain
- No resource type mappings 
- No constant updates for new templates

### ✅ **True Decoupling**
- Template packages are completely independent of CLI core
- Follows `hyp <verb> <noun>` pattern exactly
- CLI core never needs modification for new templates

## Running Tests

```bash
# Run template-agnostic error handling tests
pytest test/unit_tests/error_handling/test_cli_decorators.py -v

# Run all error handling tests
pytest test/unit_tests/error_handling/ -v
```

## How It Works

### 1. Dynamic Resource Detection
```python
# From Click command: "hyp-jumpstart-endpoint" → "jumpstart endpoint"
# From Click command: "hyp-pytorch-job" → "pytorch job"
# From Click command: "hyp-any-future-template" → "any future template"
```

### 2. Dynamic Operation Detection  
```python
# From function name: "js_delete" → "delete"
# From function name: "pytorch_describe" → "describe"
# From function name: "custom_list_pods" → "list"
```

### 3. Dynamic List Command Generation
```python
# "jumpstart endpoint" → "hyp list hyp-jumpstart-endpoint"
# "pytorch job" → "hyp list hyp-pytorch-job" 
# "future template" → "hyp list hyp-future-template"
```

## Example Error Messages

### Template-Agnostic 404 Messages
```bash
# JumpStart endpoint
❓ jumpstart endpoint 'missing-name' not found in namespace 'default'. 
Please check the resource name and try again. 
Use 'hyp list hyp-jumpstart-endpoint' to see available resources.

# PyTorch job  
❓ pytorch job 'missing-job' not found in namespace 'production'.
Please check the resource name and try again.
Use 'hyp list hyp-pytorch-job --namespace production' to see available resources.

# Future template (zero code changes needed!)
❓ llama job 'missing-llama-job' not found in namespace 'default'.
Please check the resource name and try again. 
Use 'hyp list hyp-llama-job' to see available resources.
```

## Removed Files (Now Obsolete)

The following files were removed as part of the template-agnostic redesign:

- `test_error_constants.py` - Hardcoded enums no longer needed
- `test_error_context.py` - Complex context gathering replaced with simple approach
- `test_not_found_handler.py` - Enum-based message generation replaced
- `test_utils_404_handling.py` - Enum dependencies removed

- `src/sagemaker/hyperpod/common/exceptions/error_constants.py` - Hardcoded enums removed
- `src/sagemaker/hyperpod/common/exceptions/error_context.py` - Complex context system removed  
- `src/sagemaker/hyperpod/common/exceptions/not_found_handler.py` - Enum-based handler removed

## Implementation Location

The template-agnostic 404 error handling is now implemented in:
- `src/sagemaker/hyperpod/common/cli_decorators.py` - Main implementation
- `src/sagemaker/hyperpod/common/utils.py` - Common log display utility

## Usage in CLI Commands

```python
# Old approach (removed):
@handle_cli_exceptions(
    resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,  # ❌ Hardcoded
    operation_type=OperationType.DELETE                  # ❌ Hardcoded  
)

# New approach (template-agnostic):
@handle_cli_exceptions()  # ✅ Auto-detects everything dynamically
@click.command("hyp-jumpstart-endpoint")
def js_delete(name, namespace):
    # Automatically detects:
    # - Resource: "jumpstart endpoint" (from command name)
    # - Operation: "delete" (from function name)
    # - List command: "hyp list hyp-jumpstart-endpoint"
```

## Future Template Support

When new templates are added (e.g., `hyperpod-llama-job-template/`):

1. **No CLI core changes needed** ✅
2. **No enum updates required** ✅ 
3. **No mapping maintenance** ✅
4. **Automatic 404 handling** ✅

The system will automatically:
- Detect resource type from command name
- Generate appropriate error messages
- Provide correct list commands
- Work seamlessly with telemetry

This achieves the vision of making CLI/SDK code truly template-agnostic while maintaining excellent user experience.
