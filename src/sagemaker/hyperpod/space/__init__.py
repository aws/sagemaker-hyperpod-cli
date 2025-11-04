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

from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate
from hyperpod_space_template.v1_0.model import SpaceConfig

__all__ = [
    "HPSpace",
    "HPSpaceTemplate",
    "SpaceConfig",
]
