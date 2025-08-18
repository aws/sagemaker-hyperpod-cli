# SageMaker HyperPod CLI - Error Handling Unit Tests

This directory contains comprehensive unit tests for the SageMaker HyperPod CLI's enhanced 404 error handling system.

## Overview

The error handling system provides user-friendly, contextual error messages when resources are not found, helping users understand what went wrong and how to fix it.

## Test Structure

### Core Test Files

1. **`test_error_constants.py`** - Tests error constants and enums
   - ResourceType enum values and consistency
   - OperationType enum values and consistency  
   - RESOURCE_LIST_COMMANDS mapping completeness
   - RESOURCE_DISPLAY_NAMES mapping completeness
   - Cross-mapping consistency validation

2. **`test_error_context.py`** - Tests error context gathering
   - ErrorContext dataclass functionality
   - ContextGatherer initialization and configuration
   - Resource availability checking (with timeout protection)
   - Context gathering for different resource types
   - Integration with real SageMaker SDK calls

3. **`test_not_found_handler.py`** - Tests 404 message generation
   - NotFoundMessageGenerator template rendering
   - Message generation for all resource/operation combinations
   - NotFoundHandler main coordination logic
   - Integration scenarios combining context + message generation
   - Fallback handling for edge cases

4. **`test_cli_decorators.py`** - Tests CLI integration decorators
   - Smart CLI exception handler with auto-detection
   - Resource/operation type detection from CLI context
   - Integration with existing CLI exception handling
   - Legacy compatibility support

5. **`test_utils_404_handling.py`** - Tests utility functions
   - handle_404() function with various input combinations
   - handle_exception() function for different exception types
   - ApiException status code handling (401, 403, 404, 409, 500, etc.)
   - Integration scenarios combining all components

## Test Coverage

The test suite provides comprehensive coverage of:

- **104 individual test cases** covering all components
- **All resource types**: HyperPod PyTorch Jobs, Custom Endpoints, JumpStart Endpoints
- **All operation types**: DELETE, GET, DESCRIBE, LIST
- **All error scenarios**: 404 Not Found, 401 Unauthorized, 403 Forbidden, etc.
- **Integration scenarios**: End-to-end error handling workflows
- **Edge cases**: Unknown types, timeouts, fallback handling

## Running the Tests

### Run All Error Handling Tests
```bash
# From project root
python test/unit_tests/error_handling/run_comprehensive_404_unit_tests.py

# Or from the error_handling directory
cd test/unit_tests/error_handling
python run_comprehensive_404_unit_tests.py
```

### Run Individual Test Files
```bash
# Run specific test category
pytest test/unit_tests/error_handling/test_error_constants.py -v
pytest test/unit_tests/error_handling/test_error_context.py -v
pytest test/unit_tests/error_handling/test_not_found_handler.py -v
pytest test/unit_tests/error_handling/test_cli_decorators.py -v
pytest test/unit_tests/error_handling/test_utils_404_handling.py -v
```

### Run All Tests in Directory
```bash
# Run all error handling tests
pytest test/unit_tests/error_handling/ -v
```

## Components Tested

### Error Constants (`src/sagemaker/hyperpod/common/error_constants.py`)
- ResourceType enum (HYP_PYTORCH_JOB, HYP_CUSTOM_ENDPOINT, HYP_JUMPSTART_ENDPOINT)
- OperationType enum (DELETE, GET, DESCRIBE, LIST)
- RESOURCE_LIST_COMMANDS mapping
- RESOURCE_DISPLAY_NAMES mapping

### Error Context (`src/sagemaker/hyperpod/common/error_context.py`)
- ErrorContext dataclass for structured error information
- ContextGatherer for collecting available resources
- Timeout protection for external API calls
- Integration with SageMaker SDK

### Not Found Handler (`src/sagemaker/hyperpod/common/not_found_handler.py`)
- NotFoundMessageGenerator for template-based message creation
- NotFoundHandler for coordinating context gathering and message generation
- Support for all resource/operation combinations

### CLI Decorators (`src/sagemaker/hyperpod/common/cli_decorators.py`)
- Smart exception handler with automatic resource/operation detection
- Integration with Click CLI framework
- Legacy compatibility support

### Utils 404 Handling (`src/sagemaker/hyperpod/common/utils.py`)
- handle_404() for standardized 404 error handling
- handle_exception() for comprehensive exception handling
- Support for all Kubernetes ApiException status codes

## Test Philosophy

1. **Comprehensive Coverage**: Every function, class, and code path is tested
2. **Real Integration**: Tests use actual SageMaker SDK calls where appropriate
3. **Mocking Strategy**: Strategic mocking to isolate components while maintaining realism
4. **Edge Case Handling**: Extensive testing of error conditions and fallbacks
5. **Documentation**: Each test is clearly documented with purpose and expected behavior

## Example Error Messages Generated

### PyTorch Job Not Found
```
❓ Job 'my-training-job' not found in namespace 'production'. 
There are 3 resources in this namespace. 
Use 'hyp list hyp-pytorch-job --namespace production' to see available resources.
```

### JumpStart Endpoint Not Found
```
❓ JumpStart endpoint 'my-endpoint' not found in namespace 'default'. 
No resources of this type exist in the namespace. 
Use 'hyp list hyp-jumpstart-endpoint' to check for available resources.
```

### Custom Endpoint Not Found
```
❓ Custom endpoint 'missing-endpoint' not found in namespace 'inference'. 
There are 5 resources in this namespace. 
Use 'hyp list hyp-custom-endpoint --namespace inference' to see available resources.
```

## Future Maintenance

When adding new resource types or operations:

1. Update the enums in `error_constants.py`
2. Add corresponding mappings in `RESOURCE_LIST_COMMANDS` and `RESOURCE_DISPLAY_NAMES`
3. Add test cases in the appropriate test files
4. Update this README with new examples

## Integration Testing

For integration testing with real endpoints, see:
- `test_cli_404_integration_real_endpoints.py` (in project root)
- `test_real_404_error_messages_comprehensive.py` (in project root)
- `test404cmds.ipynb` (Jupyter notebook with real endpoint examples)
