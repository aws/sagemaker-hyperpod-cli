# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from hyperpod_custom_inference_template.v1_0 import model as v1_0
from hyperpod_custom_inference_template.v1_1 import model as v1_1
from hyperpod_custom_inference_template.v1_0.template import (
    TEMPLATE_CONTENT as v1_0_template,
)
from hyperpod_custom_inference_template.v1_1.template import (
    TEMPLATE_CONTENT as v1_1_template,
)

SCHEMA_REGISTRY = {
    "1.0": v1_0.FlatHPEndpoint,
    "1.1": v1_1.FlatHPEndpoint,
}

TEMPLATE_REGISTRY = {"1.0": v1_0_template, "1.1": v1_1_template}
